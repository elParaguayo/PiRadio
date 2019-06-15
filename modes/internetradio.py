# Internet Radio mode for PiRadio

# Uses MPD to stream sources. Playlist of stations is defined in code below.
from subprocess import check_output, CalledProcessError
from time import sleep
from threading import Thread

from resources.basemode import RadioBaseMode

# Define the radio stations
STATIONS = [("Radio 1", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p"),
            ("Radio 2", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p"),
            ("Radio 3", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio3_mf_p"),
            ("Radio 4", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4fm_mf_p"),
            ("Radio 4 (LW)", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4lw_mf_p"),
            ("Radio 5 Live", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5live_mf_p"),
            ("Radio 5 Extra", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5extra_mf_p"),
            ("Radio 6", "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p"),
            ("Capital FM", "http://media-sov.musicradio.com:80/CapitalMP3"),
            ("Heart", "http://media-sov.musicradio.com:80/HeartLondonMP3"),
            ("XFM", "http://media-sov.musicradio.com:80/RadioXLondonMP3"),
            ("Absolute Radio", "http://mp3-ar-128.timlradio.co.uk/")]


class ModeRadio(RadioBaseMode):

    name = "Internet Radio"

    def __init__(self):
        super(ModeRadio, self).__init__()

        # Build the playlist of our radio stations and add to our menu
        self.get_stations()

        # Finish building the menu
        self.build_menu()

        # Internet radio is unlikely to provide metadata so we'll just let
        # the listener know what station they're listening to
        self.metadata = {"Artist": "Listening to:"}

        # Initialise some useful variables
        self.current_station = None
        self.running = False

    def get_stations(self):
        """Creates menu entries for each radio station."""
        menu = []

        # Empty the existing playlist to be safe
        _ = check_output (["mpc", "clear"])

        # Loop over the list of stations. We need the index too as mpc uses this
        # to play items.
        for i, (station, link) in enumerate(STATIONS):

            # Add the stream address to the mpd playlist
            _ = check_output(["mpc", "add", link])

            # Create a menu item with a callback to start the stream
            menu.append((station, lambda i=i+1: self.play_station(i)))

        # Add the menu items to the mode's main menu
        self.menu = menu

    def enter(self):
        # When turning on the radio, we automatically want to start playing.
        # Preference is to start the last tuned station. If this is the first
        # time, then we play the first station in the playlist.
        if self.current_station is None:
            self.current_station = 1

        self.play_station(self.current_station)

        # Set the script as running
        self.running = True

        # Define and start the thread
        # meta = Thread(target=self.show_station)
        # meta.daemon = True
        # meta.start()

    def exit(self):
        # Stop the radio stream
        _ = check_output(["mpc", "stop"])
        self.running = False

    def play_station(self, link):
        # Start the radio stream
        try:
            _ = check_output(["mpc", "play", str(link)])
        except CalledProcessError, e:
            self.show_text("menuinfo", "Error!")

        # Set the metadata to show the name of the current station
        self.metadata["Album"] = STATIONS[link-1][0]

        # Send metadata to the display
        self.show_text("metadata", self.metadata)

        # Remember the current station
        self.current_station = link

    # def show_station(self):
    #     station = -1
    #
    #     while self.running:
    #         if station != self.current_station:
    #             self.show_text("metadata", self.metadata)
    #             station = self.current_station
    #         sleep(1)
