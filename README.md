# CCS811 e-paper imager

Shows recent CCS811 eCO2 and TVOC estimates on a 2.13-inch black/white/red
GeeekPi e-paper display. eCO2 is estimated from gas readings, not measured CO2.

## Hardware and wiring

- Raspberry Pi Zero/Zero W with a 40-pin header, Raspberry Pi OS, SSH, and internet access during installation
- GeeekPi 2.13-inch 122 x 250 black/white/red e-paper HAT
- CCS811 I2C breakout (the wiring below assumes the Adafruit breakout)

The display HAT plugs directly onto the Pi header. If connecting an equivalent
display with wires, use this map. Numbers are **physical Pi header pins**;
GPIO numbers are **BCM** numbers. The sensor shares 3.3 V and ground with the
display.

```text
Pi Zero 40-pin header                    E-paper          CCS811
physical pin 1   3V3 ------------------ VCC
physical pin 6   GND ------------------ GND
physical pin 11  GPIO17 --------------- RST
physical pin 18  GPIO24 --------------- BUSY
physical pin 19  GPIO10 / SPI0 MOSI --- DIN / SDA
physical pin 22  GPIO25 --------------- DC
physical pin 23  GPIO11 / SPI0 SCLK --- CLK / SCL
physical pin 24  GPIO8  / SPI0 CE0 ---- CS

physical pin 17  3V3 ------------------------------------- VIN
physical pin 9   GND ------------------------------------- GND
physical pin 3   GPIO2 / I2C SDA ------------------------- SDA
physical pin 5   GPIO3 / I2C SCL ------------------------- SCL
physical pin 14  GND ------------------------------------- WAKE *
```

`*` Tie WAKE to ground on the original Adafruit header breakout. The Adafruit
STEMMA QT version does not need a separate WAKE wire. The e-paper's `DIN/SDA`
and `CLK/SCL` labels mean **SPI**, while the CCS811's `SDA` and `SCL` mean
**I2C**; do not connect them together. If the HAT covers the header, use a
stacking header or suitable breakout to connect the sensor. Check the power
and WAKE requirements of any other CCS811 breakout before wiring it.

Pin references: [52Pi display](https://wiki.52pi.com/index.php/EP-0133),
[Adafruit CCS811](https://learn.adafruit.com/adafruit-ccs811-air-quality-sensor/pinouts).

## Install

Clone this repository on the Pi and run from the repository directory:

```sh
git clone https://github.com/Cbezzenberger/CCS811.git
cd CCS811
sudo bash install-pi.sh
sudo reboot
```

The installer enables I2C and SPI, installs dependencies and the GeeekPi
driver, and enables the app and settings services. It runs them as the account
that invoked `sudo`. After reboot, check:

```sh
systemctl status coimager.service coimager-manage.service
journalctl -u coimager.service -n 50 --no-pager
```

## Change settings

From another computer on the same network, use your Pi username and address:

```sh
ssh -N -L 127.0.0.1:8765:127.0.0.1:8765 your-user@your-pi.local
```

Replace `your-user@your-pi.local` with your Pi login and address. Open
<http://127.0.0.1:8765> in your browser. The page is reachable only
through SSH, so protect your Pi login with a strong password or SSH key. You
can change sensor sampling and day/night display refresh times there.

## License

Copyright (C) 2022-2026 Carl Bezzenberger. This version is licensed under
[GNU GPL version 3 only](./LICENCE.md). The display buffer conversion in
[`printToEpaper.py`](./printToEpaper.py) adapts code from
[GeeekPi's GPL-3.0 demo](https://github.com/geeekpi/epaper/blob/main/eink2.13_demo.py).
The installer retrieves that driver and its license from the pinned upstream
revision.
