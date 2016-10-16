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
from .lib.pybtooth import (BluetoothManager,
                           BluetoothSignalHandler,
                           BluetoothMediaPlayer,
                           BTSignals)
from .lib.pybtooth import constants as BT

# Define the dbus interface for metadata discovery
PLAYER_IFACE = "org.bluez.MediaPlayer1"


class ModeBluetooth(RadioBaseMode):

    name = "Bluetooth"

    def __init__(self):
        super(ModeBluetooth, self).__init__()

        # Create a basic menu.
        self.menu = [("Play", self.Play),
                     ("Pause", self.Pause),
                     ("Stop", self.Stop),
                     ("Previous Track", self.Previous),
                     ("Next Track", self.Next),
                     ("Scan for Devices", self.scan),
                     ("Show Device", self.show_device)]
        self.build_menu()

        # Disable the bluetooth adaptor
        self.start_bluetooth(False)

        # Initialise dbus for metadata retrieval
        #self.bus = dbus.SystemBus()

        self.btooth = BluetoothManager()

        # Initialise some basic variables
        self.running = False
        self.player = None

    def enter(self):
        # Enable bluetooth adaptor
        self.start_bluetooth(True)

        # Create an object to watch for Bluetooth signals
        self.signal_handler = BluetoothSignalHandler()

        # Add callbacks for the signals we want

        # Listen for new track metadata
        self.signal_handler.add_callback(signal=BTSignals.SIGNAL_PROPERTIES,
                                         interface=BT.PLAYER_IFACE,
                                         property_name="Track",
                                         callback=self.metadata_changed)

        # Listen for new media players
        self.signal_handler.add_callback(signal=BTSignals.SIGNAL_ADD_INTERFACE,
                                         interface=BT.PLAYER_IFACE,
                                         callback=self.player_changed,
                                         return_iface=True)

        # Set the flag so we know our script is running
        self.running = True

        # See if anything is connected and update the display
        self.getCurrentMediaPlayer()
        self.update_display()

        # Define and start a thread to listen for signals
        meta = Thread(target=self.signal_handler)
        meta.daemon = True
        meta.start()

    def exit(self):
        # Set the running flag to False to stop the metadata thread
        self.running = False

        self.signal_handler.stop()

        # Disable the bluetooth adaptor
        self.start_bluetooth(False)

    def show_device(self):
        """Displays name of connected device."""
        # Show text if the menu item is used.
        try:
            connected = self.btooth.getConnectedDevices()
        except:
            self.show_text("menuinfo", "ERROR")
            return

        if connected:
            try:
                self.show_text("menuinfo", connected[0].name)
            except:
                self.show_text("menuinfo", "Name unknown")
        else:
            self.show_text("menuinfo", "No connections")

    def scan(self):
        """Scans for visible bluetooth devices and displays submenu."""

        # Start the discovery process on the adapter
        self.btooth.Discover()

        # Alert the user that we're scanning
        for i in range(10):
            self.show_text("menuinfo", "Scanning: {}".format(10 - i))
            sleep(1)

        # Stop the discovery
        self.btooth.StopDiscovery()

        # Retrieve a list of the named devices
        self.btdevices = self.btooth.getNamedDevices()

        # Tell the user that we didn't find any devices
        if not self.btdevices:
            self.show_text("menuinfo", "No devices found.")

        # or build a submenu to display found devices
        else:
            temp = []
            for i, device in enumerate(self.btdevices):

                # Create the menu function
                func = lambda index=i: self.device_submenu(index)
                name = device.name

                # We should indicate if the deivce is connected
                if device.connected:
                    name += " (*)"

                # Add the item to the menu
                temp.append((name, func))

            # display the menu
            self.add_temp_menu(temp)

    def device_submenu(self, index):
        """Method to create a submenu for bluetooth devices discovered during
           the scan. Provides the ability to pair, connect, disconnect and
           forget devices.
        """
        device = self.btdevices[index]

        menu = []
        if device.connected:
            menu.append(("Disconnect", device.Disconnect))
        else:
            if device.trusted:
                menu.append(("Connect", device.Connect))
            else:
                menu.append(("Pair", device.Pair))

        if device.paired:
            func = lambda dev=device: self.btooth.Forget(dev)
            menu.append(("Forget", func))

        self.add_temp_menu(menu)

    def update_display(self):
        """Method to update the display based on the attached Bluetooth media
           player and metadata.
        """
        # Get the player properties
        if self.player:
            try:
                track = self.player.metadata
            except:
                track = None

         # Check is there is a Track property (which contains track metadata)
            if track:

                # Get the available metadata
                mt = {}
                mt["Title"]  = track["Title"]
                mt["Artist"] = track["Artist"]
                mt["Album"] = track["Album"]

                # Store the metadata
                self.metadata = mt

                # Confirm we've managed to get metadata
                self.show_text("metadata", self.metadata)

            else:
                # Signal unsuccessful retrieval
                self.show_text("metadata", {"Title": "",
                                            "Artist": "No metadata found",
                                            "Album": ""})

            try:
                self.show_text("mode", self.player.name)
            except:
                self.player = None

        else:
            self.show_text("mode", "Not Connected")
            self.show_text("metadata", {"Title": "",
                                        "Artist": "No player found",
                                        "Album": ""})

    def player_changed(self, interface, path, player):
        """Callback function called when a new media player is created by the
           Bluetooth device.
        """
        try:
            self.player = BluetoothMediaPlayer(path)
        except:
            self.player = None

        self.update_display()

    def metadata_changed(self, interface, changed, path):
        """Callback function called when new Track metadata is provided by the
           Bluetooth device.
        """
        if self.player:
            self.update_display()
        else:
            self.player_changed(None, path, None)

    def getCurrentMediaPlayer(self):
        """Method to retrieve the current media player from the attached device.
        """
        player = self.btooth.getCurrentMediaPlayer()

        if player:
            self.player = player
        else:
            self.player = None

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

    def player_control(self, command):
        """Method to translate control to BluetoothMediaPlayer method."""

        CMDS = ["Play", "Pause", "Stop", "Previous", "Next"]

        if command not in CMDS:
            return None

        try:
            control = getattr(self.player, command)
            control()
        except:
            return None

    def Play(self):
        self.player_control("Play")

    def Pause(self):
        self.player_control("Pause")

    def Stop(self):
        self.player_control("Stop")

    def Previous(self):
        self.player_control("Previous")

    def Next(self):
        self.player_control("Next")
