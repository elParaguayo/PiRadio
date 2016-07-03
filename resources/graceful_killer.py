import signal

class GracefulKiller(object):
    """Basic signl handler. Sets a flag which is updated when SIGINT or
       SIGTERM signals are received by the script.
    """

    def __init__(self):
        self.killed = False
        signal.signal(signal.SIGINT, self.kill)
        signal.signal(signal.SIGTERM, self.kill)

    def kill(self, *args):
        self.killed = True
