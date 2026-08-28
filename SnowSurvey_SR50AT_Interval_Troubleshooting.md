# SnowSurvey SR50AT Interval Sensor — Troubleshooting Log

**Station:** SnowSurvey (CR6)
**Symptom:** Interval snow depth sensor (`SR50AT_1`, port `C1`) reading flaky/unreliable. Total snow depth sensor (`SR50AT_2`, port `C3`) believed to be working correctly.
**Date opened:** 2026-08-27

## Background

SnowSurvey runs two identical SR50AT sonic snow depth sensors through the same code path (`Templates/Include/SR50AT_M/SR50AT_M_Sample.CRB`), differing only by SDI-12 port and which table fields they feed:

| Sensor | `sensor_index` | SDI-12 port | SDI-12 address | Table fields |
|---|---|---|---|---|
| Interval | 1 | `C1` | `0` | `IntSnow`, `IntDist`, `IntQ` |
| Total | 2 | `C3` | `0` | `TtlSnow`, `TtlDist`, `TtlAirTC`, `TtlQ` |

Each cycle takes 11 SDI-12 `M7!`/`D0!` reads (10-sec slow scan), sorts them, and stores the median (`Result_SR50AT(6,...)`). There is **no power control** anywhere in the code (no `SW12`, `PortSet`, or excitation delay) — sensors are assumed continuously powered, so this was ruled out early as a "warm-up time" issue.

**Off-season gotcha:** `DisableSnowDepth` is set once at boot from the RTC month (`Survey.CRB:83-88`) — `True` for June–October. While `True`, `SR50AT_M_Sample.CRB` short-circuits before ever calling `SDI12Recorder`, so **no SDI-12 traffic occurs on `C1`/`C3` in the off-season** regardless of program state. As of this investigation (2026-08-27), the station is in this disabled state, which meant live terminal testing didn't need to worry about contention with the running program.

## Investigation

1. **Reviewed code for power control** — none exists. Sensor reads are a direct `SDI12Recorder(..., "M7!", ...)` call with no pre-read power cycling.
2. **Confirmed `DisableSnowDepth` is currently `True`** — no active polling of either sensor right now (off-season, boot-time RTC check).
3. **Live SDI-12 terminal test** via LoggerNet Connect Screen → Terminal Emulator → `SDI12` transparent mode:
   - Port `1` (`C1`, Interval): sent `0M7!` → **"No answer from sensor."**
   - First re-test attempt selected port `3` from the menu — this is actually `U1` (the air-temp/RH analog channel), **not** `C3`. Invalid test, discarded.
   - Corrected: port `2` (`C3`, Total): sent `0M7!` / `0D0!` → **sensor responded.**
4. **Conclusion so far:** `C1` is not responding at the raw SDI-12 level; `C3` is. Since `C3` works over the same logger and shared 12V bus, this **rules out a station-wide SDI-12/power failure** — the fault is localized to the `C1` signal path (the CR6's `C1` terminal, the cable, or the Interval sensor head itself). It does **not** yet distinguish between those three.

## SnowSurvey port map (from generated `SnowSurvey.CR6`)

| Port | Used by |
|---|---|
| `U1` | Air temp (`VoltSE`, analog) |
| `U2` | RH (`VoltSE`, analog) |
| `U3` | Rain gauge (`PulseCount`) |
| `U5` | Cabinet temp (`TCDiff`) |
| `U7`, `U8` | Wind direction bridge (`BrHalf`) |
| `U10` | Wind speed (`PulseCount`) |
| `C1` | SR50AT_1 (Interval) — **suspect** |
| `C3` | SR50AT_2 (Total) — confirmed responding |
| `U11` | BaroVUE10 barometric pressure (SDI-12, address `3`) |

SDI-12-capable ports on this CR6 (per the datalogger's own "Select SDI12 Port" menu): `C1, C3, U1, U3, U5, U7, U9, U11`. Of these, **`U9` is the only one both SDI-12-capable and currently unused** — the fallback port if `C1` turns out to be a dead terminal.

## Root-cause isolation plan (not yet executed)

Goal: distinguish CR6 `C1` port vs. cable/connector vs. sensor head.

1. **Port/wire swap** — swap which cable lands on `C1` vs `C3` (physically, or by flipping the `sr50at_sensor_address` order in `surveys.yaml` and redeploying). If the fault follows the `C1` label regardless of what's plugged in → CR6 port itself is bad. If it follows the physical cable/sensor → downstream of the port.
2. **Sensor-head swap** — with wiring restored, swap the two SR50AT sensor heads (or sub in a spare). If the fault follows the sensor → bad sensor. If it stays with the cable run → cable/connector/mounting issue.
3. **Multidrop diagnostic (preferred — no rewiring of `C1` needed):**
   - Change the Interval sensor's SDI-12 address via terminal mode while it's still on its own wire: `0A1!` (address `0` → `1`), confirm with `1M7!`.
   - Temporarily tap the Interval sensor's data line onto the `C3` terminal (parallel with Total, shared 12V/ground).
   - Query address `1` on port `C3` (`1M7!` / `1D0!`).
   - **Responds** → sensor + cable are good; fault is isolated to the **`C1` terminal on the CR6**. Strongest single test — proves it without touching `C1`'s own wiring.
   - **No response** → fault is in the sensor or its cable, not the CR6 port.
   - Revert address with `1A0!` if unwiring back to a standalone `C1`/`C3` setup afterward.

## Possible resolutions

- **If `C1` terminal is confirmed dead:** relocate Interval sensor's data line to `U9` (only free SDI-12-capable port). Requires updating `surveys.yaml`:
  ```yaml
  sr50at_sensor_address:
    - U9   # was C1
    - C3
  ```
  then rebuild (`./precompile_survey_code.py`) and redeploy. This is a relocation, not a fix for the underlying hardware — the CR6's `C1` terminal would remain unusable.
- **If cable/connector is the fault:** replace/re-terminate that run; environment-specific culprits to check given the site (freeze-thaw at connector, ice load/strain on the cable, corrosion, whether the SR50AT's internal heater is functioning to prevent icing on the transducer face).
- **If sensor head is the fault:** replace/RMA the Interval SR50AT.
- **Longer-term option:** consolidate both sensors onto a single SDI-12 port (e.g. `C3`) with distinct addresses (`0`/`1`), freeing a control port. Requires templatizing the currently-hardcoded `"0"` address in `SR50AT_M_Sample.CRB` (add a `sr50at_device_address` list alongside `sr50at_sensor_address`, mirroring how `BaroVUE` already uses non-default address `"3"` on `U11`). Not yet implemented — proposed only.

## Useful reference: manual SDI-12 terminal test procedure

1. LoggerNet Connect Screen → select station → connect → **Datalogger → Terminal Emulator → Open Terminal**.
2. Press Enter until `CR6>` prompt appears.
3. Type `SDI12`, Enter.
4. At "Select SDI12 Port", enter the **menu number** (not the port name) — e.g. `1` = `C1`, `2` = `C3`. **Double-check this mapping each time**; it was the source of one invalid test result in this investigation.
5. `0M7!` (or the sensor's current address) to issue a measurement request; `0D0!` to read back the data.
6. `Esc` to exit SDI-12 terminal mode.

No need to pause the running program for this while `DisableSnowDepth = True` (current state) — there's no active polling to contend with. If testing in-season with the program actively polling, pause it first (Connect Screen → Compile and Run panel) to avoid contention, and remember to resume it afterward since ski patrol relies on this data.
