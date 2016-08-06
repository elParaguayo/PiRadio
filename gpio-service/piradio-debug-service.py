import signal
from subprocess import call
from time import sleep

import pigpio

# Name of service to be restarted
SERVICE = "pi-radio"

# GPIO pins to listen for
BUTTONS = [13, 21]

# Number of seconds buttons must be held for until service restarts
TIMEOUT = 5


class PiRadioRecovery(object):
    """Class object to reset PiRadio if GPIO becomes unresponsive.

       This script is designed to be run as a standalone service.
    """

    def __init__(self):

        # Flag to know that the script is running
        self.running = True

        # Timeout limit until service restarts
        self.limit = TIMEOUT * 10

        # Counter for determining length of button presses
        self.count = 0

        # Signal handlers for graceful exit
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

        # Variable for pigpio pi instance
        self.pi = None

        # See if we can connect to the pi
        while self.running and self.pi is None:

            try:
                self.pi = pigpio.pi()
            except:
                sleep(1)

    def run(self):

        # Loop will end when service is killed or service receives SIGINT or
        # SIGTERM
        while self.running:

            # If all buttons are pressed simultaneously...
            if all(not self.pi.read(pin) for pin in BUTTONS):

                # ...increment our counter
                self.count += 1

            # If not...
            else:

                # ...reset it.
                self.count = 0

            # If we've hit our limit...
            if self.count == self.limit:

                # ...restart the service
                self.restart_service()

            # Small sleep so we don't hog CPU
            sleep(0.1)

    def exit(self):
        """Function to cause graceful exit of service."""

        # Set running flag to false so main loop ends.
        self.running = False

    def restart_service(self):
        """Function to restart the designated service. Provides no feedback."""

        # Build relevant command and call it.
        cmd = ["sudo", "systemctl", "restart", SERVICE]
        print "Restarting: {}".format(cmd)
        call(cmd)


if __name__ == "__main__":

    recovery_service = PiRadioRecovery()
    recovery_service.run()
