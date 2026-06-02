# VBTN Barcode Scanner Device Configuration

## Device Overview

This document records the configuration of the USB HID barcode scanner registered for VBTN operations.

| Field | Value |
|---|---|
| **Device ID** | `HID\VID_05E0&PID_1200\7&39b9e678&0&0000` |
| **Vendor ID** | `VID_05E0` (Symbol Technologies / Motorola Solutions) |
| **Product ID** | `PID_1200` |
| **Parent Device** | `USB\VID_05E0&PID_1200\S/N:2F712F7575524AE6916D77A03C3B79C4_Rev:PAACFS00-002-R033` |
| **Serial Number** | `2F712F7575524AE6916D77A03C3B79C4` |
| **Firmware Revision** | `PAACFS00-002-R033` |

## Driver Configuration

| Field | Value |
|---|---|
| **Driver Name** | `keyboard.inf` |
| **Driver Package ID** | `keyboard.inf_amd64_c56788078819b951` |
| **Class GUID** | `{4d36e96b-e325-11ce-bfc1-08002be10318}` (HID Keyboard) |
| **Driver Date** | `06/21/2006` |
| **Driver Version** | `10.0.26100.1882` |
| **Driver Provider** | `Microsoft` |
| **Driver Section** | `HID_Keyboard_Inst.NT` |
| **Driver Rank** | `0xFF1003` |
| **Matching Device ID** | `HID_DEVICE_SYSTEM_KEYBOARD` |
| **Outranked Drivers** | `input.inf:HID_DEVICE:00FF1005` |
| **Device Updated** | `false` |

## Operating Mode

The scanner is configured in **USB HID Keyboard Emulation** mode. In this mode, scanned barcodes are transmitted as keyboard keystrokes and can be read directly by any application with a text input field — no additional barcode SDK is required.

## Usage Notes

- Plug the scanner into any available USB port; the Microsoft HID keyboard driver loads automatically.
- Scanned data is followed by a carriage-return (Enter) by default, which submits the value in most form fields.
- To change the output suffix or enable/disable the Enter key, scan the appropriate configuration barcode from the device's programming guide.
- The device does **not** require a custom driver install on Windows 10/11.

## Classification

**INTERNAL** — VBTN operational hardware inventory record.
