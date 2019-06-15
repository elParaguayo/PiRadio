import unicodedata

import pigpio

from .menubase import (RadioSubmenu,
                       RadioMenuItem,
                       RadioMenuMode,
                       RadioTempMenu,
                       RadioTempItem)

class RadioBaseMode(object):
    """Base class definition for radio modes. Any custom modes need to
       subclass this.
    """

    def __init__(self, pi=None, led_pin=None, display_q=None):
        """Constructor takes 3 optional parameters:

             pi:        pigpio pi instance (e.g. if you need GPIO access)
             led_pin:   GPIO pin number of LED (to indicate mode active)
             display_q: Queue instance for displaying text on display
        """
        self.pi = pi
        self.led_pin = led_pin
        self.display_q = display_q

        # Prepare LED
        if self.pi and self.led_pin:
            self.pi.set_mode(self.led_pin, pigpio.OUTPUT)

    def build_menu(self):
        """Each mode needs to call this method to build the menu for operating
           the mode.
        """
        self.modemenu = self._get_menu_items()


    def add_temp_menu(self, menu):
        """Creates a temporary menu from the list provided and immediately
           enters the submenu.
        """
        # Create a temporary menu
        tempmenu = RadioTempMenu("")

        # Add the menu items
        tempmenu = self._walk_menu(menu, tempmenu, temp=True)
        tempmenu.add_back_item()

        # Define root and parent menus
        parent = self.root_menu.menu

        while isinstance(parent, RadioTempMenu):
            parent = parent.parent

        tempmenu.parent = parent
        tempmenu.root = self.root_menu

        # Activate the tempory menu now
        if self.root_menu:
            self.root_menu.menu = tempmenu
            self.root_menu.idx = 0
            self.root_menu.draw()

    def enter(self):
        """Each mode should be responsbible for starting any child processes,
           threads etc required for the operation of the mode.

           Such items should be started here.
        """
        pass

    def exit(self):
        """Each mode should be responsbible for killing any child processes,
           threads etc required for the operation of the mode on exit.

           Such items should be stopped here.
        """
        pass

    def _walk_menu(self, menu, parent, temp=False):
        """Recursive method for building menu."""

        # Check if we're building a temporary menu or not and retrieve
        # appropriate classes
        Submenu = RadioTempMenu if temp else RadioSubmenu
        Item = RadioTempItem if temp else RadioMenuItem

        # Loop over menu items
        for text, target in menu:

            # Check if there is a submenu
            if type(target) == list:

                # If so, let's create it
                submenu = self._walk_menu(target, Submenu(text))
                parent.add_item(submenu)

            # If not, add the item
            else:
                parent.add_item(Item(text, target))

        # If we're in a submenu, we need to add a "Back" option.
        if isinstance(parent, RadioSubmenu):
            parent.add_back_item()

        return parent

    def _get_menu_items(self):
        """Build the menu from the user defined list of options."""
        base = RadioMenuMode(self)

        if self.menu:
            return self._walk_menu(self.menu, base)
        else:
            return base

    def get_metadata(self):
        """If the mode is a music player, the mode should provide a reference to
           the relevant metadata handler so that info can be displayed on the
           LCD screen.
        """
        pass

    def toggle_led(self, state):
        """Modes may have access to a dedicated LED to indicate activity
           (e.g. successful Bluetooth connection).

           This method provides the ability to toggle the LED.
        """
        if self.led_pin:
            self.pi.write(self.led_pin, int(state))

    def show_text(self, key, text):
        """Modes should be able to send text to the LCD display via a Queue
           object.
        """
        if self.display_q:
            # text = self.remove_accents(text)
            self.display_q.put((key, text))

    # def remove_accents(self, data):
    #     """Method to tidy up strings for the display.
    #
    #        The LCD can't handle accented characters so we need to make sure all
    #        text is ASCII.
    #
    #        However, rather than removing accents, the code tries to replace the
    #        letter with the non-accented version wherever possible. Removal of
    #        characters is a last resort.
    #     """
    #     # Metadata is provided in a dict, so make sure each entry is compatible
    #     # with our display
    #     if type(data) == dict:
    #         return {key: self.remove_accents(data[key]) for key in data}
    #
    #     else:
    #         if type(data) == str:
    #             data = unicode(data)
    #
    #         # Remove accents from letters
    #         nfkd_form = unicodedata.normalize('NFKD', data)
    #
    #         # Remove accented letters (where not normalised above)
    #         only_ascii = nfkd_form.encode('ASCII', 'ignore')
    #
    #         return only_ascii
