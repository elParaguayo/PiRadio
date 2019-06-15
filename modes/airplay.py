# Airplay Mode for PiRadio

# Limited functionality for now.
# When enabled, the mode starts the Shairport Sync service to make the device
# visible to Apple devices.
#
# No metadata is available at the moment. This may change in future releases.
from subprocess import call, check_output, CalledProcessError

from resources.basemode import RadioBaseMode
from .lib.airplay_metadata import AirplayMetadataReader


ON = ["sudo", "systemctl", "start", "shairport-sync.service"]
OFF = ["sudo", "systemctl", "stop", "shairport-sync.service"]


class ModeAirplay(RadioBaseMode):

    name = "Airplay"

    def __init__(self):
        super(ModeAirplay, self).__init__()

        # Create a basic menu
        self.menu = [("Show Device Name", self.show_device)]
        self.build_menu()

        # Service should be disabled by default
        call(OFF)

        # No metadata is currently available so let's just define a fixed
        # item for display
        self.metadata = {"Artist": "PiRadio"}

    def enter(self):
        # Start the service
        call(ON)

        # Can we read metadata?

        # Check the version info
        try:
            check_output(["shairport-sync", "-V"])
        except CalledProcessError, e:
            # Version info is returned with exit code of 1 so need to handles
            # in except block
            self.can_read_metadata = "metadata" in e.output

        # We've got metadata support
        if self.can_read_metadata:

            # Set up a callback function
            func = lambda meta: self.show_text("metadata", meta)

            # Create the metadata handler
            self.metadata_handler = AirplayMetadataReader(callback=func)

            # daemonise it
            self.metadata_handler.daemon = True

            # start it
            self.metadata_handler.start()

        else:
            # No metadata support so display basic info
            self.show_text("metadata", self.metadata)

    def exit(self):
        # Stop the servive
        call(OFF)

        # Stop the metadata handler
        if self.can_read_metadata:
            self.metadata_handler.running = False

    def show_device(self):
        # Show text if the menu item is used.
        self.show_text("menuinfo", "PiRadio")
