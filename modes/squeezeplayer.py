# Squeezeplayer mode for PiRadio
#
# Mode that uses Squeezelite to play music from Logitech Media Server.
# Mode will discover server on local network.
from subprocess import Popen, call
from threading import Thread
from time import sleep

from resources.basemode import RadioBaseMode
from .lib.lms_discovery import LMSDiscovery
from .lib.simple_pylms import LMSServer, LMSPlayer

# Define a MAC address for the squeezelite player (so server remembers sync
# groups etc)
PLAYER_MAC = "41:41:41:41:41:41"


class ModeSqueezeplayer(RadioBaseMode):

    name = "Squeezeplayer"

    def __init__(self):
        super(ModeSqueezeplayer, self).__init__()

        # Define and build menu
        self.menu = [("Show Device Name", self.show_device_name),
                     ("WiFi Strength", self.show_wifi)]
        self.build_menu()

        # Define some useful variables
        self.proc = None
        self.stopped = True
        self.current_track = ""
        self.host = None
        self.port = None
        self.connected = False
        self.server = None
        self.ref = PLAYER_MAC

    def enter(self):
        # Try to connect to server
        self.show_text("menuinfo", "Connecting...")
        self.connected = self.connect()

        # If successful...
        if self.connected:

            # Alert the user
            self.show_text("menuinfo", "Connected")

            # Start squeezelite with some defined options (hardcoded for now)
            self.proc = Popen(["squeezelite",
                               "-n", "PiRadio",
                               "-a", "16384:4096",
                               "-o", "sysdefault:CARD=ALSA",
                               "-m", self.ref])

            # Create a player instance so we can send JSON commands
            # to the server (e.g. to control player or retrieve metadata)
            self.player = LMSPlayer(self.ref, self.server)

            # Set flag
            self.stopped = False

            # Define and start thread to monitor metadata
            track_info = Thread(target=self.get_track)
            track_info.daemon = True
            track_info.start()

    def exit(self):
        # Terminate squeezelite ...
        self.proc.terminate()

        # ... and murder it to be sure it's really dead!
        self.proc.kill()

        # Update flag (to end metadata thread)
        self.stopped = True

    def connect(self):

        # See if we can find the server on the network
        if self.host is None:
            hosts = LMSDiscovery().all()
            if hosts:
                self.host = hosts[0]["host"]
                self.port = hosts[0]["port"]

        # We found one so define the server
        if self.host:
            self.server = LMSServer(host=self.host, port=self.port)
            return True

        # Fail.
        else:
            self.server = None
            return False

    def get_track(self):

        # Loop to check metadata
        while not self.stopped:

            # Get the title, artists and album of current track
            try:
                ttl = self.player.get_track_title()
                art = self.player.get_track_artist()
                alb = self.player.get_track_album()

            except (KeyError, TypeError):
                ttl = art = alb = ""

            # Create a single string of all data
            current = ttl + art + alb

            # If it's a new track...
            if current != self.current_track:

                # ... send metadata to display
                self.show_text("metadata", {"Title": ttl,
                                            "Artist": art,
                                            "Album": alb})

                # Remember the current track
                self.current_track = current

    def show_device_name(self):
        # Show the name of the squeezelite player
        self.show_text("menuinfo", "PiRadio")

    def show_wifi(self):
        """Retrieves wifi strength from server."""
        if self.player:
            try:
                wifi = self.player.get_wifi_signal_strength()
                self.show_text("menuinfo", "WiFi strength: {}".format(wifi))
            except (KeyError, TypeError):
                pass
