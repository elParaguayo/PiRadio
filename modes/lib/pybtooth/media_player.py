import dbus

from .base import BluetoothBase
from .constants import *

class BluetoothMediaPlayer(BluetoothBase):

    def __init__(self, path):
        super(BluetoothMediaPlayer, self).__init__()
        self.device = dbus.SystemBus().get_object(SERVICE_NAME, path)
        self.interface = dbus.Interface(self.device, PLAYER_IFACE)
        self.props = dbus.Interface(self.device, PROPERTIES_IFACE)
        self.get = lambda prop: self.props.Get(PLAYER_IFACE, prop)
        self.set = lambda prop, value: self.props.Set(PLAYER_IFACE, prop, value)
        self.meta_template = {'Album': '',
                              'NumberOfTracks': '0',
                              'Title': '',
                              'Artist': '',
                              'Duration': '',
                              'Genre': '',
                              'TrackNumber': ''}


    def Play(self):
        self.interface.Play()

    def Stop(self):
        self.interface.Stop()

    def Pause(self):
        self.interface.Pause()

    def Next(self):
        self.interface.Next()

    def Previous(self):
        self.interface.Previous()

    def FastForward(self):
        self.interface.FastForward()

    def Rewind(self):
        self.interface.Rewind()

    @property
    def name(self):
        return self.get("Name")

    @property
    def metadata(self):
        try:
            meta = self.get("Track")
            return {str(k): str(v) for k, v in meta.iteritems()}
        except:
            return self.meta_template.copy()
