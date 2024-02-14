### Notes
1. Always compile and deploy using `Conditional Compile, Include Files and Save`. This will generate a unique file with includes included, which we can then compile and deploy, to keep track of revisions.

### Questions
1. Do we want to standardize the Table1/Table2/Table3 etc between the sensors, using includes, for you to use with your bash scripts?

### To Checks
1. Validate pulsecount sensors are reading properly (wind and rain)
2. In StationStatus, look for skipped scans before and after telegraf is running, as well as skipped records. The 1 second inner loop may be too aggressive.
3. Specifically for skipped scans/records, the temperature on/off delay might be a problem
4. Also, for the snow depth, there's a concurrent mode we can try:

```
The C command is for concurrent mode. Concurrent mode allows multiple sensors on the same channel to be performing their measurement sequence at the same time. The CR800, CR1000, CR3000, and CR6 handle the C mode a special way. These dataloggers will send the C command to the sensor and retrieve the result on a following scan. The measurement might lag a scan behind the other measurements, but the datalogger won't be delayed. For more information about this behavior, refer to the help for SDI12Recorder in the CRBasic help.

```
5. Monitor battery drain on remote surveys, both before and after influxdb!

### Hardware Improvements
1. Introduce 120V charging to all stations, and power wifi via 24/48V batteries, Meanwell DRS-240 series. Add an MPPT controller and set it higher than the 120V.
2. 


### TODO
1. Add ping and self-reboot to CR300 at beartop (slash all dataloggers? via mini timer relay from amazon).
2. If we do it via "Watchdog" (see function 24) (can be a 5 minute timer, 15s reset). We can combine with Ping, and ping every minute, and reset if we cannot ping. We can also add an exlusion period each day to force reset.