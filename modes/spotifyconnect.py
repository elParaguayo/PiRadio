# Spotify Connect for PiRadio

# Limited functionality for now.
# When enabled, the mode starts the Shairport Sync service to make the device
# visible to Apple devices.
#
# No metadata is available at the moment. This may change in future releases.
import errno
import os
import shutil
from subprocess import Popen, PIPE
from threading import Thread
from select import select

from resources.basemode import RadioBaseMode


#CACHE = "~/.spotifycache"
CACHE = "/tmp/spotifycache"
DEVICE_NAME = "Kitchen Radio"


class ModeSpotifyConnect(RadioBaseMode):

    name = "Spotify"

    def __init__(self, playername=DEVICE_NAME):
        super(ModeSpotifyConnect, self).__init__()

        # Create a basic menu
        self.menu = [("Show Device Name", self.show_device)]
        self.build_menu()

        self.spotify = None
        self.playername = playername

        self.cache = self.getcache()
        self.running = False

        # Service should be disabled by default
        self.stop()

        # No metadata is currently available so let's just define a fixed
        # item for display
        #self.metadata = {"Artist": self.playername}

    def getcache(self):
        cachedir = os.path.expanduser(CACHE)

        #if os.path.isdir(cachedir):
        #    shutil.rmtree(cachedir)

        #try:
        #    os.makedirs(cachedir)
        #except OSError as e:
        #    if e.errno != errno.EEXIST:
        #        raise

        return cachedir

    def enter(self):
        # Start the service
        self.start()

        # Send our metadata
        #self.show_text("metadata", self.metadata)

    def exit(self):
        # Stop the servive
        self.stop()

    def get_metadata(self):

        while self.running:

            rlist, _, _ = select([self.spotify.stderr], [], [])
            for stdo in rlist:
                line = os.read(stdo.fileno(), 1024)
                
                if "META::" in line:
                    m = line.split("||")
                    mt = {}
                    mt["Title"] = m[1]
                    mt["Artist"] = m[2]
                    mt["Album"] = m[3]
                    self.show_text("metadata", mt)


    def start(self):
        cmd = ["/usr/bin/spotty", "--name", self.playername, "--cache", self.cache]
        cmd += ["--initial-volume", "100"]
        cmd += ["--device", "sysdefault:CARD=ALSA"]
        self.spotify = Popen(cmd, stderr=PIPE)

        self.running = True

        t = Thread(target=self.get_metadata)
        t.start()

    def stop(self):
        self.running = False
        if self.spotify:
            self.spotify.kill()

    def show_device(self):
        # Show text if the menu item is used.
        self.show_text("menuinfo", "PiRadio")
