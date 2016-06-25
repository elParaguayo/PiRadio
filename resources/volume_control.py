from subprocess import check_call

from .rotary_encoder import RotaryEncoder
import pigpio

class VolumeControl(object):
    """Class for handling volume control using a rotary encoder.

       Turning the encoder increases or decreases volume by 5%. Pressing the
       button will mute the output device.

       Class is initialised with the following parameters:
         pi:     Instance of pigpio
         pinA:   GPIO pin for leg A on encoder
         pinB:   GPIO pin for leg B on encoder
         button: GPIO pin for button on encoder
         led:    GPIO pin for mute indicator
    """

    # Starting level
    INITIAL_VOL = 50

    # Amount to change volume by (percent)
    INCREMENT = 5

    # Base command for adjusting volume
    #CMD = "amixer set Master {vol}% > /dev/null"
    CMD = "pactl set-sink-volume 0 {vol}%"

    def __init__(self, pi, pinA, pinB, button, led=None, cb=None):

        self.pi = pi
        self.level = self.INITIAL_VOL
        self.old_level = self.INITIAL_VOL
        self.muted = False
        self.led = led
        self.callback = cb

        if self.led:
            self.pi.set_mode(led, pigpio.OUTPUT)
            self.pi.write(led, 0)

        self.control = RotaryEncoder(pi, pinA, pinB, button,
                                     rot_callback=self.adjust,
                                     but_callback=self.mute)

        self.setVolume(self.level)

    def setVolume(self, vol):
        cmd = self.CMD.format(vol=vol).split()
        check_call(cmd)

    def adjust(self, way):

        if self.muted:
            self.mute(False)
        else:

            self.level += (self.INCREMENT * way)
            if self.level < 0:
                self.level = 0
            if self.level > 100:
                self.level = 100

            self.setVolume(self.level)
            if self.callback:
                self.callback(self.level)

    def mute(self, level):
        if self.muted:
            self.level = self.old_level
            self.muted = False
        else:
            self.old_level = self.level
            self.level = 0
            self.muted = True

        self.setVolume(self.level)

        if self.callback:
            self.callback(self.level)

        if self.led:
            self.pi.write(self.led, int(self.muted))

    def start(self):
        self.control.start()
