# Intro
During covid I started building a small Co2 sensor to monitor the Co2 and TVOC levels in my room and display them on a small epaper display.

![Co2_sensor](https://user-images.githubusercontent.com/50334068/175136259-10f1e927-1f91-4aee-9638-58555aa540cb.jpg)
*Red line is CO2 in ppm, black stroked line is TVOC in ppb*

Out of the box, this code should work with


- Adafruit's CCS 811 Co2 sensor for Raspberry pi
- Raspberry pi zero W (Created with gen 1)
- Geeekpi's 2.13" three-color E-ink display

# Setup instructions
As instructed by the adafruit how-to:
Before launch,

	sudo nano /boot/config.txt

Scroll down until you find a block like

	#Uncomment all the rows below to enable the optional hardware interfaces:
	dtparam=i2c_arm=on
	dtparam=i2s=on
	dtparam=spi=on

and add the following:

    dtparam=i2c_arm_baudrate=10000

> **_NOTE:_** This might not be required anymore after an update to the sensor firmware, but it does no harm

On Raspberry pi zero W (and potentially others), you also need to install the following package to be able to plot the graph:

	sudo apt-get install libatlas-base-dev
