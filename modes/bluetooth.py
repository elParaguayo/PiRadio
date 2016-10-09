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
from .lib.pybtooth import BluetoothManager

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
        self.bus = dbus.SystemBus()

        self.btooth = BluetoothManager()

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
        connected = self.btooth.getConnectedDevices()

        if connected:
            try:
                self.show_text("menuinfo", connected[0].name)
            except:
                self.show_text("menuinfo", "Name unknown")
        else:
            self.show_text("menuinfo", "No connections")

    def scan(self):
        self.btooth.Discover()
        for i in range(10):
            self.show_text("menuinfo", "Scanning: {}".format(10 - i))
            sleep(1)
        self.btooth.StopDiscovery()
        self.btdevices = self.btooth.getNamedDevices()
        if not self.btdevices:
            self.show_text("menuinfo", "No devices found.")
        else:
            temp = []
            for i, device in enumerate(self.btdevices):
                func = lambda index=i: self.device_submenu(index)
                name = device.name
                if device.connected:
                    name += " (*)"
                temp.append((name, func))
            self.add_temp_menu(temp)

    def device_submenu(self, index):
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

    def read_player(self):
        # Get the player properties
        track = self.player.metadata
        self.show_text("mode", self.player.name)

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
            return True

        else:
            # Signal unsuccessful retrieval
            return False

    def getCurrentMediaPlayer(self):

        player = self.btooth.getCurrentMediaPlayer()

        if player:
            self.player = player
        else:
            self.player = None

    def poll_metadata(self):
        # If we've got an existing player instance, let's try to use it
        if self.player is not None:
            try:
                return self.read_player()
            except:
                self.player = None

        self.getCurrentMediaPlayer()

        if self.player:
            try:
                return self.read_player()
            except:
                return False
        else:
            self.show_text("mode", "Not Connected")
            self.show_text("metadata", {"Title": "",
                                        "Artist": "No player found",
                                        "Album": ""})
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

    def player_control(self, command):

        CMDS = ["Play", "Pause", "Stop", "Previous", "Next"]

        if command not in CMDS:
            return None

        control = getattr(self.player, command)
        try:
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
