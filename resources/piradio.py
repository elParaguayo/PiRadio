import datetime
from threading import Thread
from time import sleep

from .menubase import RadioMenu
from .radioselector import RadioSelector
from .display import RadioDisplay
from .volume_control import VolumeControl


# Initial volume on boot (0-100)
INITIAL_VOLUME = 50

# Define pin layouts

# Display pin mapping
lcd_rs = 17
lcd_en = 18
lcd_d4 = 27
lcd_d5 = 22
lcd_d6 = 23
lcd_d7 = 24
lcd_backlight = 25

# Volume control pin mapping
vol_a = 19
vol_b = 20
vol_button = 21

# Selection dial pin mapping
sel_a = 5
sel_b = 6
sel_button = 13


class PiRadio(object):
    """PiRadio class definition.

       This class handles the initialisation of the display as well as the
       volume and selection rotary encoders.

       The class switches between defined modes as requested by the user.

       The class also provides two functions for updating information on the
       display:

         Volume information
         Clock

       Finally, the class also provides a graceful shutdown of the radio on an
       exit event.
    """

    def __init__(self, pi, modes):
        """Initialisation of the radio. Requires two (mandatory) parameters:

             pi:    A pigpio instance
             modes: A list of initialised radio modes

          Note: Initialising the class does not start the application.
        """
        self.pi = pi

        # Define the volume control and set its callback function
        self.volume_control = VolumeControl(self.pi, vol_a, vol_b, vol_button,
                                            cb=self.vol_change)

        # Define the selection control (we don't use a callback here as the
        # control will be bound to the menu object later)
        self.selector = RadioSelector(self.pi, sel_a, sel_b, sel_button)

        # Define the LCD disply
        self.lcd = RadioDisplay(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                                lcd_backlight)

        # Define the main menu object and set up some callbacks
        self.main_menu = RadioMenu("", modeselect=self.change_mode,
                                       cb_display=self.menu_change)

        # Build our menu based on the modes
        for mode in modes:

            # Modes need access to the LCD queue
            mode.display_q = self.lcd.queue

            # Add the mode-specific menu to our own menu
            self.main_menu.add_item(mode.modemenu)

        # Bind the selection control actions to the main menu
        self.selector.bind_rotate(self.main_menu.rotate)
        self.selector.bind_select(self.main_menu.select)

        # No mode set at the moment
        self.mode = None

        # Set the initial volume level
        self.vol_change(INITIAL_VOLUME)

        # Blank time for the display
        self.now = "00:00"

        # Set up a thread to change the time in the LCD and daemonise it
        self._time = Thread(target=self._time_worker)
        self._time.daemon = True

    def start(self):
        """Method to start all the controls required to run the radio."""

        # Set a flag to show we're running
        self.running = True

        # Start radio controls and display
        self.volume_control.start()
        self.selector.start()
        self.lcd.start()

        # Start the time thread
        self._time.start()

    def exit(self):
        """Method to stop the radio and shutdown gracefully."""

        # Set the flag (stops threads that are watching this)
        self.running = False

        # Run the active mode's exit method so processes can be stopped
        try:
            self.mode.exit()
        except (AttributeError, TypeError):
            pass

        # Remove text from the display
        self.lcd.clear()

        # Turn the backlight off
        self.lcd.set_backlight(0)

    def change_mode(self, newmode):
        """Method to change the active mode of the radio."""

        # Run the current mode's exit method to stop processes
        if self.mode:
            self.mode.exit()

        # Set the new mode
        self.mode = newmode

        # Run the enter method of the mode to start relevant processes
        self.mode.enter()

        # Remove the metadata from the display
        self.lcd.clear_metadata()

        # Upate the mode name on the display
        self.lcd.queue.put(("mode", newmode.name))

    def menu_change(self, txt):
        """Simple method to change the menu info on the display."""
        if self.lcd.queue:
            self.lcd.queue.put(("menuinfo", txt))

    def vol_change(self, level):
        """Method to provide graphical representation of volume on the
           display.
        """

        # We've got 10 boxes for volume so rebase the percentage number
        l = int(level/10)

        # Create the volume string (square blocks for volume padded with '-')
        vol = "{v:-<10}".format(v=chr(255)*l)

        # Send the string to the display
        if self.lcd.queue:
            self.lcd.queue.put(("vol", "{vol}".format(vol=vol)))

    def _time_worker(self):
        """Thread to update the time on the display."""

        # Loop to keep thread running while radio is running
        while self.running:

            # Get the time
            now = datetime.datetime.now().time()

            # Pretty formatting
            timestring = "{h:0>2}:{m:0>2}".format(h=now.hour, m=now.minute)

            # We only update if the time has changed
            if timestring != self.now:
                self.lcd.queue.put(("time", timestring))
                self.now = timestring

            # 1 second refresh should be accurate enough
            sleep(1)
