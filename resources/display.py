import Queue
from subprocess import call
from time import sleep, time
from threading import Thread
import unicodedata

from .pigpio_lcd import PIGPIO_LCD as LCD

# Define modes for the display (which determines template to be displayed)
DISPLAY_CONTROLS = "controls"
DISPLAY_NOWPLAYING = "playing"

# How long to wait before reverting to "now playing" display
DISPLAY_TIMEOUT = 5

# Define our display (e.g. 20x4)
# NB If you use a different size display you will need to redefine the display
# templates
DISPLAY_COLS = 20
DISPLAY_ROWS = 4


class RadioDisplay(Thread):
    """Class to handle the display of information on the state of the
       PiRadio.

       The class needs to provide multiple layouts depending on whether the user
       is browsing the menu or whether we are showing "now playing"
       information.

       The class subclasses Thread and is designed to be run in the background.

       It must therefore be run by calling the "start" method.
    """

    def __init__(self, pi, rs, en, d4, d5, d6, d7, backlight=None, debug=False):

        self.lcd_config = (rs, en, d4, d5, d6, d7, DISPLAY_COLS, DISPLAY_ROWS)
        self.bl = backlight
        self.pi = pi

        # Initialise the Thread
        super(RadioDisplay, self).__init__()

        # Define a queue where requests for updates can be placed
        self.queue = Queue.Queue()

        # Debug mode can be used to test display without a display connected
        self.debug = debug

        # Create an empty list to hold the lines of text
        self.lines = ["" for _ in range(DISPLAY_ROWS)]

        # This thread should be daemonised
        self.daemon = True

        # Initial mode is to show menu
        self.displaymode = DISPLAY_CONTROLS

        # Define which items won't force the menu to change to the menu mode
        self.ignore = ["time", "menuinfo2"]

        # Define the templates for the modes
        self.templates = {"controls":
                             ["{mode:^14.14} {time}",
                              "{menuinfo:^20.20}",
                              "{menuinfo2:^20.20}",
                              "Vol:  -|{vol}|+"],
                         "playing":
                             ["{mode:^14.14} {time}",
                              "{title:^20.20}",
                              "{artist:^20.20}",
                              "{album:^20.20}"]
                         }

        # Create a single string of the current template
        # self.text = "\n".join(self.templates[self.displaymode])

        # Define a dict of parameters that will be used to format the text
        # to be displayed on the LCD
        self.params = {"mode": "PiRadio",
                       "menuinfo": "Starting up",
                       "menuinfo2": "",
                       "vol": "",
                       "time": "00:00",
                       "title": "",
                       "artist": "",
                       "album": ""}

        # Create a list of formatted text for display
        self.newtxt = [line.format(**self.params)
                       for line in self.templates[self.displaymode]]

        # Define a list to hold old menu (to compare which lines have been
        # updated)
        self.dirty = ["XX" for _ in range(4)]

        self.abort = False

    def remove_accents(self, data):
        """Method to tidy up strings for the display.

           The LCD can't handle accented characters so we need to make sure all
           text is ASCII.

           However, rather than removing accents, the code tries to replace the
           letter with the non-accented version wherever possible. Removal of
           characters is a last resort.
        """
        # Metadata is provided in a dict, so make sure each entry is compatible
        # with our display
        if type(data) == dict:
            return {key: self.remove_accents(data[key]) for key in data}

        else:
            if type(data) == str:
                try:
                    data = unicode(data)
                except UnicodeDecodeError:
                    return data

            # Remove accents from letters
            nfkd_form = unicodedata.normalize('NFKD', data)

            # Remove accented letters (where not normalised above)
            only_ascii = nfkd_form.encode('ASCII', 'ignore')

            return only_ascii

    def parse_metadata(self, meta):
        """Method to update the dictionary of parameters with the metadata
           received from the radio.
        """
        self.params["title"] = meta.get("Title", "")
        self.params["artist"] = meta.get("Artist", "")
        self.params["album"] = meta.get("Album", "")

    def clear_metadata(self):
        """Method to remove the current metadata (e.g. when changing modes)."""
        self.params["title"] = ""
        self.params["artist"] = ""
        self.params["album"] = ""

        # We should refresh the display after doing this to make sure change
        # is instant
        self.update()

    def run(self):
        """Method to start the display functions.

           The thread will continue to monitor the queue and update the display
           for any new information received.
        """

        # Create an instance of the display and start it
        self.lcd = LCD(self.pi, *self.lcd_config, backlight=self.bl)
        self.lcd.start()

        # How long to wait until changing to now playing mode
        change = time() + DISPLAY_TIMEOUT

        # Start our loop
        while not self.abort:
            try:

                # See if there's anything in the queue
                key, text = self.queue.get_nowait()

                text = self.remove_accents(text)

                # Metadata needs to be handled separately
                if key == "metadata":
                    self.parse_metadata(text)

                # Anything else can be added straight to the dictionary
                else:
                    self.params[key] = text

                    # Check whether we need to change the display mode
                    if not key in self.ignore:
                        self.displaymode = DISPLAY_CONTROLS
                        change = time() + DISPLAY_TIMEOUT

            # If there's nothing in the queue...
            except Queue.Empty:

                # Small sleep (so don't hog CPU)
                sleep(0.1)

                # If we're already in now playing then we can go back to start
                # of the loop as there's nothing to update
                if self.displaymode == DISPLAY_NOWPLAYING:
                    continue

            # Do we need to change to now playing mode?
            if self.displaymode == DISPLAY_CONTROLS and time() > change:
                self.displaymode = DISPLAY_NOWPLAYING

            # Update the display
            self.update()

    def update(self):
        """Method to update LCD display with text."""

        # Build the list of lines
        self.newtxt = [line.format(**self.params)
                       for line in self.templates[self.displaymode]]

        # and display it
        self.display()

    def display(self):
        """Method to display text. Can output to screen if in debug mode."""

        # Text display if deibugging...
        if self.debug:
            self.text_display()

        # ...otherwise update the LCD
        else:
            self.display_lcd()

    def display_lcd(self):
        """Method to update the LCD. The method check which lines have changed
           and only updates those lines. This reduces flickering on the screen.
        """

        # Loop over the lines
        for i, line in enumerate(self.newtxt):

            # If the line has changed...
            if line != self.dirty[i]:

                # ...update the LCD
                self.write_line(i, line)

        # Update the reference with the new text
        self.dirty = self.newtxt

    def text_display(self):
        """Simple method to create a virtual LCD display on the terminal."""

        # Clear the screen so display is "refreshed"
        call(["clear"])

        # Print each line
        for line in self.lines:
            print "{line:_^{rows}}".format(rows=self.rowlength, line=line)

    def write_line(self, line, text):
        """Method to write lines on the LCD."""
        self.lcd.lcd_string(text, line + 1)

    def clear(self):
        """Clears the LCD display."""
        self.lcd.clear()

    def set_backlight(self, state):
        """Method to turn the LCD backlight on or off."""
        self.lcd.set_backlight(state)

    def turn_off(self):
        """Clear the screen and turn off the backlight."""
        self.clear()
        self.set_backlight(False)
