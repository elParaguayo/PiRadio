# Bluetooth mode for PiRadio

# This mode enables the Bluetooth adaptor and displays metadata for the
# currently playing item.
#
# There is no option to pair devices at the moment. This may be added in later
# releases.
from subprocess import check_output
from threading import Thread
from time import sleep

import dbus

from resources.basemode import RadioBaseMode

# Define the dbus interface for metadata discovery
PLAYER_IFACE = "org.bluez.MediaPlayer1"


class ModeBluetooth(RadioBaseMode):

    name = "Bluetooth"

    def __init__(self):
        super(ModeBluetooth, self).__init__()

        # Create a basic menu.
        self.menu = [("Show Device", self.show_device)]
        self.build_menu()

        # Disable the bluetooth adaptor
        self.start_bluetooth(False)

        # Initialise dbus for metadata retrieval
        self.bus = dbus.SystemBus()

        # Initialise some basic variables
        self.running = False
        self.player = None

    def enter(self):
        # Enable bluetooth adaptor
        self.start_bluetooth(True)

        # Get the dbus object manager (for metadata)
        obj = self.bus.get_object("org.bluez", "/")
        self.manager = dbus.Interface(obj, "org.freedesktop.DBus.ObjectManager")

        # Set the flag so we know our script is running
        self.running = True

        # Define and start a thread to get the song metadata
        meta = Thread(target=self.get_metadata)
        meta.daemon = True
        meta.start()

    def exit(self):
        # Set the running flag to False to stop the metadata thread
        self.running = False

        # Disable the bluetooth adaptor
        self.start_bluetooth(False)

    def show_device(self):
        # Show text if the menu item is used.
        self.show_text("menuinfo", "PiRadio")

    def read_player(self):
        # Get the player properties
        iface = "org.freedesktop.DBus.Properties"
        props = self.player.GetAll(PLAYER_IFACE, dbus_interface=iface)

        # Check is there is a Track property (which contains track metadata)
        if props.get("Track", False):

            # Get the available metadata
            mt = {}
            mt["Title"]  = u"{}".format(props["Track"].get("Title"))
            mt["Artist"] = u"{}".format(props["Track"].get("Artist"))
            mt["Album"] = u"{}".format(props["Track"].get("Album"))

            # Store the metadata
            self.metadata = mt

            # Confirm we've managed to get metadata
            return True

        else:
            # Signal unsuccessful retrieval
            return False

    def poll_metadata(self):
        # If we've got an existing player instance, let's try to use it
        if self.player is not None:
            try:
                return self.read_player()
            except:
                self.player = None

        # If not, we'll need to see if we can find it
        try:
            objects = self.manager.GetManagedObjects()
        except:
            objects = None

        if not objects:
            return False

        else:
            player_path = None
            # Loop through the objects in our manager ...
            for path, interfaces in objects.iteritems():

                # ... and see if we find a bluetooth player
                if PLAYER_IFACE in interfaces:
                    player_path = path

            player = None

            # We've found a player, so now we can get the metadata
            if player_path:
                self.player = self.bus.get_object("org.bluez", player_path)
                return self.read_player()

            else:
                return False

    def get_metadata(self):
        """Method to get track metadata. This should be run in a thread.

           When metadata is found, it is sent to the display.
        """
        while self.running:
            if self.poll_metadata():
                self.show_text("metadata", self.metadata)
            sleep(1)

    def start_bluetooth(self, enabled=False):
        """Method to enable bluetooth. As the audio will stutter if the wifi is
           enabled at the same time, the wifi adaptor is disabled when
           bluetooth is enabled (and vice versa).
        """
        if enabled:
            _ = check_output(["sudo", "hciconfig", "hci0", "up"])
            _ = check_output(["sudo", "ifdown", "wlan0"])

        else:
            _ = check_output(["sudo", "hciconfig", "hci0", "down"])
            _ = check_output(["sudo", "ifup", "wlan0"])
