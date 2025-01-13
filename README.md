# platform-py32f0

PlatformIO platform for PY32F0xx devices.

The project is mostly based on https://github.com/IOsetting/py32f0-template repository.

## Frameworks

The supported PIO framework is https://github.com/positron96/framework-py32f0sdk which
  has HAL and LL drivers from manufacturer.

Adding Arduino framework is not a goal of this project, only manufacturer SDK is.

## MCUs

There are "board" definitions for PY32F003x8 (`generic_py32f003x8`) and PY32F003x6 (`generic_py32f003x6`). 
For the rest of MCUs, add your definitions to your project (or make a PR to add another MCU).

There are 2 examples (in the `examples` directory) for PY32F003 using LL and HAL drivers.

## Debug tools

At the moment, the only supported and tested upload/debug tool is blackmagic probe
(which supports PY32 [since mid 2024](https://github.com/blackmagic-debug/blackmagic/pull/1817)).
Download a latest BMDA (PC-side program), use it to connect to a BMP (hardware probe).
In `platformio.ini`, add the following configuration: 

```
upload_protocol=blackmagic
upload_port=:2000
debug_tool=blackmagic
debug_port=:2000
```

ST-Link support is technically there, but not tested.

For J-Link support, modifications to J-Link installation are needed. 
Follow this: https://github.com/IOsetting/py32f0-template?tab=readme-ov-file#option-1-install-segger-j-link.

