#!/usr/bin/env python
import time

# GPIO control
import pigpio

# Import main radio class
from resources.piradio import PiRadio

# Import signal handler
from resources.graceful_killer import GracefulKiller

# Import our modes
from modes.bluetooth import ModeBluetooth
from modes.settings import ModeSettings
from modes.squeezeplayer import ModeSqueezeplayer
from modes.internetradio import ModeRadio
from modes.airplay import ModeAirplay
from modes.spotifyconnect import ModeSpotifyConnect

# Get pigpio up and running
pi = pigpio.pi()

# Create an instance of the PiRadio and confirm which modes we want to run
# NB the order of the modes here is how they will appear on the display
radio = PiRadio(pi, [ModeSqueezeplayer(),
                     ModeSpotifyConnect(playername="Kitchen Radio"),
                     ModeRadio(),
                     ModeBluetooth(),
                     ModeAirplay(),
                     ModeSettings()])

# Set up the signal handler
handler = GracefulKiller()

# Go!
radio.start()

# Keep the script alive
while not handler.killed:
    time.sleep(1)

radio.exit()
