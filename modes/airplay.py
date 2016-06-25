# Airplay Mode for PiRadio

# Limited functionality for now.
# When enabled, the mode starts the Shairport Sync service to make the device
# visible to Apple devices.
#
# No metadata is available at the moment. This may change in future releases.
from subprocess import call

from resources.basemode import RadioBaseMode


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

        # Send our metadata
        self.show_text("metadata", self.metadata)

    def exit(self):
        # Stop the servive
        call(OFF)

    def show_device(self):
        # Show text if the menu item is used.
        self.show_text("menuinfo", "PiRadio")
