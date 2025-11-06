# Bear Valley CR_Basic - Claude Code Instructions

## Project Overview

This repository contains a **Jinja2-based code generation system** that produces CRBasic programs for Campbell Scientific dataloggers deployed at a ski area. The system generates weather monitoring programs for 5 stations that provide real-time data to ski patrollers and the public for avalanche forecasting, safety decisions, and weather awareness.

## Quick Reference

### Generate All Programs
```bash
./precompile_survey_code.py
```

This generates 5 deployment-ready programs:
- `Base.CR1` - CR1000 at base elevation
- `KoalaTop.CR1` - CR1000 at mid elevation
- `BearTop.CR300` - CR300 at summit (with watchdog)
- `SnowSurvey.CR6` - CR6 with dual snow depth sensors
- `Grizzly.CR1` - CR1000 with multiple sensor arrays

### Key Files
- `Templates/surveys.yaml` - Master configuration (all station settings)
- `Templates/Survey.CRB` - Main Jinja2 template
- `Templates/Include/` - Modular sensor/table components
- `precompile_survey_code.py` - Build script

## Architecture

### Template Resolution Hierarchy

The build system searches for includes in this order:
1. `Include/Stations/<STATION_NAME>/<FILE>` (station-specific override)
2. `Include/Models/<MODEL_SERIES>/<FILE>` (model-specific override)
3. `Include/<FILE>` (default/shared)

This allows granular customization while maintaining code reuse.

### Configuration Structure

`surveys.yaml` has three layers:

```yaml
shared:           # Applied to ALL stations
  main_scan_interval_count: 3
  sensor_air_temperature: &temp {...}  # YAML anchors for reuse

CR1000:           # Model-specific overrides
  panel_frequency_filter: _60Hz

stations:         # Array of 5 station configs
  - station_name: "Base"
    model_series: "CR1000"
    sensor_windspeed:
      <<: *temp   # Inherit from anchor
      model: "05103"
```

Merge priority: `Station > Model > Shared`

## Five Deployed Stations

| Station | Model | Key Features |
|---------|-------|--------------|
| **Base** | CR1000 | Standard weather (temp/humidity/wind) |
| **KoalaTop** | CR1000 | Enhanced wind sensor (05108-45) |
| **BearTop** | CR300 | **Watchdog + Ping system**, summit conditions |
| **SnowSurvey** | CR6 | **2x SR50AT snow sensors**, barometric pressure, rain gauge |
| **Grizzly** | CR1000 | **Dual sensor arrays** (T11_/GB_ prefixes) |

## Directory Structure

```
Templates/
├── Survey.CRB                    # Master template (Jinja2)
├── surveys.yaml                  # Configuration source
└── Include/
    ├── Functions/                # Calculations (dew point, wind chill, wet bulb)
    ├── Tables/                   # Data table definitions by interval
    ├── Stations/                 # Station-specific overrides
    │   ├── Base/
    │   ├── BearTop/
    │   ├── KoalaTop/
    │   ├── SnowSurvey/
    │   └── Grizzly/
    ├── SR50AT_M/                 # Snow depth sensor code
    ├── Barometric/               # Pressure sensor code
    ├── Air_Temperature_*.CRB     # Temperature sensor modules
    ├── Windspeed_*.CRB           # Wind sensor modules
    ├── Cabinet_Temperature_Scan.CRB
    ├── Watchdog_*.CRB            # BearTop watchdog system
    └── PulseCount_Windspeed_Scan.CRB
```

## Common Tasks

### Adding a New Sensor

1. **Create sensor module in `Include/`**:
   - `<SensorName>_Vars.CRB` - Variable declarations
   - `<SensorName>_Scan.CRB` - Measurement code

2. **Update `surveys.yaml`**:
   ```yaml
   shared:
     sensor_<name>:
       channel: 5
       multiplier: 1.0

   stations:
     - station_name: "Base"
       enable_<sensor>: true
   ```

3. **Add includes to `Survey.CRB`**:
   ```jinja
   {% include find_template('<SensorName>_Vars.CRB') %}

   {% if enable_<sensor> %}
     {% include find_template('<SensorName>_Scan.CRB') %}
   {% endif %}
   ```

4. **Rebuild**: Run `./precompile_survey_code.py`

### Modifying a Specific Station

**Option A: Edit station-specific override**
- Create/edit `Include/Stations/<STATION>/Air_Temperature_Scan.CRB`
- This overrides the default for that station only

**Option B: Edit station config in `surveys.yaml`**
```yaml
stations:
  - station_name: "Base"
    sensor_air_temperature:
      air_tf_chan: 3  # Change channel from default
```

### Adding a New Data Table

1. **Create table definition**: `Include/Tables/<Name>.CRB`
   ```crbasic
   DataTable(MyTable, True, -1)
     DataInterval(0, 5, Min, 10)
     Sample(1, AirTC, FP2)
     Sample(1, RH, FP2)
   EndTable
   ```

2. **Add to scan routine** in appropriate include file:
   ```crbasic
   CallTable MyTable
   ```

3. **Rebuild and test**

### Debugging Generated Programs

1. **Generate programs**: `./precompile_survey_code.py`
2. **Inspect output**: Open `<Station>.<Extension>` in text editor
3. **Search for include location**: Look for your expected sensor code
4. **Check template resolution**: Verify correct override was used
5. **Test in LoggerNet**: Compile program to check for CRBasic syntax errors

## CRBasic Key Concepts

### Scan Intervals
```crbasic
Scan(3, Sec, 1, 0)        # Main scan: every 3 seconds
  ' Measurement code here
NextScan

SlowSequence
  Scan(60, Sec, 1, 0)     # Slow scan: every 60 seconds
    ' Low-priority code
  NextScan
EndSequence
```

### Sensor Reading Patterns

**Voltage Input**:
```crbasic
VoltSE(AirTC, 1, mV2500, 1, 0, 0, _60Hz, 0.1, -40)
' VoltSE(variable, count, range, channel, multiplex, integration, filter, mult, offset)
```

**Pulse Count** (wind speed, rain):
```crbasic
PulseCount(WS_mph, 1, 1, 1, 1, 0.2192, 0)
' PulseCount(variable, count, channel, mode, edge, multiplier, offset)
```

**Bridge Measurement** (wind direction):
```crbasic
BrHalf(WindDir, 1, mV2500, 2, 1, 1, 2500, 0, _60Hz, 355, 0)
```

**Serial Digital Interface** (snow depth, barometric):
```crbasic
SDI12Recorder(sr50at_response(), C1, 0, "M!", 1.0, 0.0)
```

### Data Tables
```crbasic
DataTable(Table1, True, -1)
  DataInterval(0, 10, Min, 10)      # 10-minute intervals
  Average(1, AirTC, FP2, False)     # Average temperature
  Sample(1, RH, FP2)                # Instantaneous humidity
  Maximum(1, WS_mph, FP2, 0, False) # Max wind speed
EndTable
```

## Watchdog System (BearTop Only)

BearTop has a self-healing watchdog that:
- Pings Google DNS (8.8.8.8) every 10 minutes
- Resets datalogger if no successful ping in 6 hours
- Uses physical output pin 1 for hardware reset

**Configuration** in `surveys.yaml`:
```yaml
watchdog:
  enabled: true
  skip_iterations: 19      # Skip 19 main scans before check
  use_initial: true        # 30-second grace period on startup
  use_ping: true           # Enable ping functionality
  pin: 1                   # Output pin for reset relay
```

**Template files**:
- `Watchdog_Vars.CRB` - Variable declarations
- `Watchdog_Scan.CRB` - Main watchdog logic in 3-second scan
- `Watchdog_PingScan.CRB` - Ping routine in 10-minute slow scan

## Snow Depth System (SnowSurvey Only)

Uses **two SR50AT sonic snow depth sensors** with sophisticated measurement logic:

**Features**:
- Takes 11 readings per measurement cycle
- Sorts readings to eliminate outliers
- Uses median of middle readings
- Barometric pressure correction
- SDI-12 protocol communication

**Configuration** in `surveys.yaml`:
```yaml
enable_precip_and_snow_sensors: true
sr50at_sensor_address: [C1, C3]    # Two sensors on different addresses
```

**Template files**:
- `SR50AT_M/SR50AT_M_Vars.CRB` - Arrays for 11 readings per sensor
- `SR50AT_M/SR50AT_M_Sample.CRB` - Measurement and sorting logic

## Multi-Sensor Arrays (Grizzly)

Grizzly has **multiple sensor arrays with prefixes**:

**Temperature Arrays**:
- `T11_` prefix: First temperature/humidity sensor
- `GB_` prefix: Second temperature/humidity sensor

**Wind Arrays**:
- `GT_` prefix: Pulse count anemometer
- `T11_` prefix: Voltage-based wind sensor

**Configuration pattern**:
```yaml
sensor_air_temperature:
  prefixes:
    T11_:
      temp_c: {pin: 1, multi: 0.0625, offset: -75}
      rh: {pin: 2, multi: 0.0625, offset: -25}
    GB_:
      temp_c: {pin: 3, multi: 0.0625, offset: -75}
      rh: {pin: 4, multi: 0.0625, offset: -25}
```

Templates iterate over prefixes to generate code for each array.

## Data Quality Patterns

The code includes several validation patterns:

**Humidity Clamping**:
```crbasic
If RH>100 AND RH<108 Then RH=100
```

**Dew Point Validation**:
```crbasic
If TdC>AirTC Or TdC=NAN Then TdC=AirTC
```

**Wind Chill Conditional**:
```crbasic
If AirTF<50 AND WS_mph>3 Then
  ' Apply wind chill formula
Else
  WindChill=AirTF
EndIf
```

## Deployment Workflow

### 1. Make Changes
- Edit `surveys.yaml` for configuration changes
- Edit template files for code changes
- Use station-specific overrides when needed

### 2. Build
```bash
./precompile_survey_code.py
```

### 3. Review Generated Files
Check the output `.CR1`, `.CR300`, or `.CR6` files for correctness.

### 4. Deploy to Datalogger
In **Campbell Scientific LoggerNet**:
1. Connect to datalogger
2. Select "Conditional Compile, Include Files and Save"
3. Load the `.CR<X>` file
4. Compile to datalogger
5. Deploy to field device

### 5. Monitor
- Check data tables for expected measurements
- Monitor battery voltage (should be ~12-14V)
- Verify network connectivity (BearTop ping status)

## Important File Mappings

### Model to Extension
| Datalogger | Extension |
|------------|-----------|
| CR1000 | `.CR1` |
| CR300 | `.CR300` |
| CR6 | `.CR6` |

### Common Sensor Models
| Sensor | Model Number | Measures |
|--------|--------------|----------|
| Temperature/Humidity | EE181 | °C, %RH |
| Wind Speed | 05103 | Anemometer (pulse) |
| Wind Speed | 05108-45 | Anemometer (pulse) |
| Wind Direction | | Potentiometer (bridge) |
| Rain Gauge | TE525 | Tipping bucket (pulse) |
| Snow Depth | SR50AT | Sonic ranging (SDI-12) |
| Barometric Pressure | CS106 | Pressure (SDI-12) |

### Voltage Ranges (Model-Specific)
| Model | Range Symbol | Voltage |
|-------|--------------|---------|
| CR1000 | mV2500 | ±2500mV |
| CR1000 | mV5000 | ±5000mV |
| CR300 | mV1000 | ±1000mV |
| CR6 | mV1000 | ±1000mV |

### Channel Notation
| Model | Format | Example |
|-------|--------|---------|
| CR1000/CR300 | Numeric | 1, 2, 3... |
| CR6 | U-series | U1, U2, U3... |

## Common Gotchas

### 1. Panel Frequency Filter Varies by Model
- CR1000 uses `_60Hz` suffix
- CR300/CR6 use `60` (numeric)
- Set correctly in model-specific config

### 2. File Extensions Matter
The build script determines output extension from `model_series` in config:
```python
model_series_to_extension = {
    "CR1000": "CR1",
    "CR6": "CR6",
    "CR300": "CR300",
}
```

### 3. Table Names Must Be Unique
Legacy table names from original programs are preserved via `legacy_tables` config to maintain compatibility.

### 4. Watchdog Pin Must Be Free
BearTop uses pin 1 for watchdog output. Don't assign sensors to this pin.

### 5. Snow Sensors Require Slow Scan
SR50AT sensors need 10-second interval slow scan to collect 11 readings properly.

### 6. YAML Anchors Save Repetition
Use anchors (`&name`) and aliases (`<<: *name`) to avoid duplicating sensor configs across stations.

## Testing Checklist

When making changes:

- [ ] Run build script successfully
- [ ] Check generated file size (should be similar to previous)
- [ ] Search generated file for new sensor variables
- [ ] Verify scan intervals are correct
- [ ] Check data table intervals match requirements
- [ ] Compile in LoggerNet (syntax check)
- [ ] Deploy to test datalogger if available
- [ ] Monitor first data collection cycle
- [ ] Verify data appears in expected tables
- [ ] Check battery voltage remains stable

## Git Workflow

This project uses git for version control. Current branch: `main`

**Before making changes**:
```bash
git status                    # Check current state
git diff                      # Review uncommitted changes
```

**After testing**:
```bash
git add Templates/surveys.yaml
git add Templates/Include/NewSensor_Scan.CRB
git commit -m "Add new sensor support for station X"
```

**Recent relevant commits**:
- `cb3a28c` - Update snowsurvey base depth
- `347e592` - Add watchdog to beartop
- `f96bfd8` - Switch to epoch time
- `8f47143` - Make ping public

## External Resources

- **CRBasic Reference**: Available in LoggerNet help documentation
- **Campbell Scientific**: https://www.campbellsci.com
- **Jinja2 Documentation**: https://jinja.palletsprojects.com/
- **Datalogger Manuals**: Check for model-specific wiring and capabilities

## Context for Claude

When working on this codebase:

1. **Always run the build script** after template changes to see the full impact
2. **Check station-specific overrides** before editing shared templates
3. **Use the find_template() hierarchy** to understand which file is actually included
4. **Respect the configuration merge order**: Station > Model > Shared
5. **Test watchdog changes carefully** on BearTop (it can reset the datalogger)
6. **Snow sensor changes affect SnowSurvey only** (check `enable_precip_and_snow_sensors`)
7. **Multi-prefix sensors** (Grizzly) require iteration logic in templates
8. **Data tables are the output** - always verify table definitions match data needs
9. **This is safety-critical** - ski patrol uses this data for avalanche forecasting
10. **Battery monitoring is crucial** - remote stations must remain powered through winter

## Support & Feedback

For issues with Claude Code itself, see: https://github.com/anthropics/claude-code/issues
