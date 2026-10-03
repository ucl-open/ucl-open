# ucl-open API

We need to build a data API for ucl-open datasets that allows users to easily load raw data into pandas dataframes. Please use https://github.com/SainsburyWellcomeCentre/aeon_api as a reference/inspiration for approach as we want the ucl-open API to be very similar as these libraries may merge at some point in the future.

## Requirements for the user
The primary goal is to add a python api package to ucl-open that allows a user to load a full dataset after specifying a few things. The user must provide:
1. A root path for the dataset
2. A reader mapping, specifying which data readers to use for each device's (subfolder) data.

In the end we would want the user to be able to load parts from a dataset with something like:
```
experiment = DotMap(
    [
        Device("HarpDevice", harp_reader)
        Device("MousePosition", csv_reader)
        Device("Video", video_reader)
    ]
)

analog_data = api.load(experiment.HarpDevice.AnalogData, C:\temp_data\ses-001_date-2026-10-03T16-14-20)
```

## Requirements for the api
- harp device readers should use https://github.com/harp-tech/python. A reader will need to be provided with a device.yml to populate its reader correctly
- when using the api we assume data is logged according to the logging spec in specs\logging.md. This should allow the api to automate data discovery within subfolders
- by default the api attempts to stitch together all chunks of data over all devices, but we should be able to provide start and stop times to narrow the time window of loaded data
- in the case of multi-channel devices (like harp), that dataset should decomposes the individual registers (channels) of the device into individual data frames