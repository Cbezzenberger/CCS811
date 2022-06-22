During covid I started building a small Co2 sensor to monitor the Co2 levels in my room and display them on a small epaper display.



Out of the box, this code should work with 
-Adafruit's CCS 811 Co2 sensor for Raspberry pi (For arduino, some adaptation might be necessary)
-Raspberry pi zero W (1st gen)
-Geeekpi's 2.13" three-color E-ink display

As instructed by the adafruit how-to:
Before launch,

    sudo nano /boot/config.txt

Scroll down until you find a block like:

    # Uncomment some of all of these to enable the optional hardware interfaces
    dtparam=i2c_arm=on
    dtparam=i2s=on
    dtparam=spi=on

Add the following:
    
    dtparam=i2c_arm_baudrate=10000

On Raspberry pi zero W and potentially others,

	sudo apt-get install libatlas-base-dev

is also required for the raspberry to be able to plot the graph.
