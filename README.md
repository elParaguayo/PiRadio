PiRadio
=======

### Requirements

* Hardware
    * Raspberry Pi 3
    * Radio (needs to be big enough to house everything here)
    * Amplifier + speakers
    * 2x rotary encoders
    * LCD Display
* Software
    * Bluetooth
    * Shairport-Sync
    * Squeezelite
    * MPC + MPD
    * AdafruitLCD
    * Pigpio

### Installing the required Software

#### Bluetooth

I got help for getting bluetooth working on the forum. Rather than recreating the steps here, I'd recommend following the posts in order from [here](https://www.raspberrypi.org/forums/viewtopic.php?f=38&t=68779&start=75#p943645).

We also need dbus support to get metadata info from Bluetooth media.

`sudo pip install dbus-python`

#### Airplay support (Shairport-Sync)

This is easy enough, I just followed the instructions on the Readme on the [Github page](https://github.com/mikebrady/shairport-sync).

#### Logitech Media Server support (Squeezelite)

The main point here is to make sure you do _not_ use the squeezelite in the Raspbian repository. This seems to hog the CPU.

Instead download the version from the Google code page. I used [this one](http://squeezelite-downloads.googlecode.com/git/squeezelite-armv6hf).

Rename the file to `squeezelite`, put it somewhere in your path (e.g. `/usr/local/bin`) and make sure it's executable.

#### Internet radio (MPC + MPD)

`sudo apt-get install mpc mpd`

Assuming you've installed the blueooth support above you'll need to make sure that mpd is a member of the relevant groups.

`sudo usermod -aG pulse,pulse-access mpd`

#### AdafruitLCD

Follow the instructions on the [Github page](https://github.com/adafruit/Adafruit_Python_CharLCD).

#### Pigpio

I think this is now in the Raspbian repository so, I guess, it's installed with:
`sudo apt-get install pigpio`

I downloaded it from the website and followed the [instructions](http://abyz.co.uk/rpi/pigpio/download.html).

I also set up a systemd script to launch pigpiod at boot.

`sudo nano /lib/systemd/system/pigpio.service`

    [Unit]
    Description=Pigpio Daemon

    [Service]
    Type=forking
    ExecStart=/usr/local/bin/pigpiod

    [Install]
    WantedBy=multi-user.target

Create the symlink:
`sudo ln -s /lib/systemd/system/pigpio.service /etc/systemd/system/pigpio.service`

and enable it:
`sudo systemctl enable pigpio.service`

#### Install this script

`git clone https://github.com/elParaguayo/PiRadio.git`

    cd PiRadio
    chmod +x main.py

I also created a systemd script for this programme.
`sudo nano /lib/systemd/system/pi-radio.service`

    [Unit]
    Description=Pi Radio Service
    After=tmp.mount bluetooth.service pigpio.service sound.target
    Requires=pigpio.service sound.target

    [Service]
    Type=simple
    ExecStart=/home/pi/dev/main.py

    [Install]
    WantedBy=multi-user.target

Create the symlink:
`sudo ln -s /lib/systemd/system/pi-radio.service /etc/systemd/system/pi-radio.service`

and enable it:
`sudo systemctl enable pi-radio.service`

Time to reboot!
