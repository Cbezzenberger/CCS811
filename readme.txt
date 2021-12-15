First steps:

Before initialisation,

    sudo nano /boot/config.txt

Scroll down until you find a block like:

    # Uncomment some of all of these to enable the optional hardware interfaces
    dtparam=i2c_arm=on
    dtparam=i2s=on
    dtparam=spi=on

Add the following:
    
    dtparam=i2c_arm_baudrate=10000