from time import sleep
from threading import Thread

import pigpio


# Based on Rotary Encoder class from:
# http://abyz.co.uk/rpi/pigpio/code/rotary_encoder_py.zip
# Thanks Joan!

class RotaryEncoder(Thread):
    """Class to decode mechanical rotary encoder pulses and button presses.

       Now subclasses Thread so this runs in background."""

    def __init__(self, pi, rotA, rotB, button,
                 rot_callback=None, but_callback=None, but_debounce=400):
        """Class takes seven parameters:
             pi:           pigpio instance
             rotA:         GPIO pin for leg A of encoder
             rotB:         GPIO pin for leg B of encoder
             button:       GPIO pin for button
             rot_callback: (optional) Callback for rotation event
             but_callback: (optional) Callback for button press
             but_debounce: (optional) Debounce time for button (default 400ms)
        """
        super(RotaryEncoder, self).__init__()

        # Thread needs to be daemonised
        self.daemon = True

        self.pi = pi
        self.gpioA = rotA
        self.gpioB = rotB
        self.button = button
        self.rot_callback = rot_callback
        self.but_callback = but_callback
        self.but_tick = 0
        self.bouncetime = but_debounce * 1000

        self.levA = 0
        self.levB = 0

        self.lastGpio = None

        self.pi.set_mode(rotA, pigpio.INPUT)
        self.pi.set_mode(rotB, pigpio.INPUT)
        self.pi.set_mode(button, pigpio.INPUT)

        self.pi.set_pull_up_down(rotA, pigpio.PUD_UP)
        self.pi.set_pull_up_down(rotB, pigpio.PUD_UP)
        self.pi.set_pull_up_down(button, pigpio.PUD_UP)

    def bind_rotate(self, callback):
        """Set a callback function to be called when the encoder rotates."""
        self.rot_callback = callback

    def bind_select(self, callback):
        """Set a callback function to be called when the button is pressed."""
        self.but_callback = callback

    def unbind(self):
        """Remove callbacks."""
        self.rot_callback = None
        self.but_callback = None

    def _pulse(self, gpio, level, tick):
        """
        Decode the rotary encoder pulse.

                   +---------+         +---------+      0
                   |         |         |         |
         A         |         |         |         |
                   |         |         |         |
         +---------+         +---------+         +----- 1

             +---------+         +---------+            0
             |         |         |         |
         B   |         |         |         |
             |         |         |         |
         ----+         +---------+         +---------+  1
        """

        if gpio == self.gpioA:
            self.levA = level
        else:
            self.levB = level;

        if gpio != self.lastGpio: # debounce
            self.lastGpio = gpio

            if gpio == self.gpioA and level == 1:
                if self.levB == 1 and self.rot_callback:
                    self.rot_callback(1)
            elif gpio == self.gpioB and level == 1:
                if self.levA == 1 and self.rot_callback:
                    self.rot_callback(-1)

    def _but(self, gpio, level, tick):

        # We need to debounce the button press
        if (self.but_callback is not None and
            tick > (self.but_tick + self.bouncetime)):

            self.but_callback(level)
            self.but_tick = tick

    def cancel(self):
        """Cancel the rotary encoder decoder."""
        try:
            self.cbA.cancel()
            self.cbB.cancel()
            self.cbButton.cancel()
        except AttributeError:
            pass

    def run(self):
        """Starts the thread. No callbacks are activated until this point."""

        # Define the callbacks
        self.cbA = self.pi.callback(self.gpioA,
                                    pigpio.EITHER_EDGE,
                                    self._pulse)

        self.cbB = self.pi.callback(self.gpioB,
                                    pigpio.EITHER_EDGE,
                                    self._pulse)

        self.cbButton = self.pi.callback(self.button,
                                         pigpio.EITHER_EDGE,
                                         self._but)

        # Start looping
        while True:
            sleep(1)
