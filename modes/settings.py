# Settings mode for PiRadio
#
# Mode for handling commands etc.
from subprocess import call, check_output
from time import sleep

from resources.basemode import RadioBaseMode

class ModeSettings(RadioBaseMode):

    name = "Settings"

    def __init__(self):
        super(ModeSettings, self).__init__()

        # Define menu entries and build the menu.
        self.menu = [("IP Address", self.show_ip),
                     ("Restart", self.restart),
                     ("Shutdown", self.shutdown)]
        self.build_menu()

    def show_ip(self):
        ip = check_output(["hostname", "-I"])
        self.show_text("menuinfo", ip)

    def restart(self):
        self.show_text("menuinfo", "Restarting...")
        sleep(0.2)
        self.exit_radio()
        sleep(0.5)
        call(["sudo", "reboot"])

    def shutdown(self):
        self.show_text("menuinfo", "Shutting down...")
        sleep(0.2)
        self.exit_radio()
        sleep(0.5)
        call(["sudo", "poweroff"])
