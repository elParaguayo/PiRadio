from .base import BluetoothBase
from .constants import *
from .device import BluetoothDevice
from .media_player import BluetoothMediaPlayer

class BluetoothManager(BluetoothBase):

    def __init__(self):
        super(BluetoothManager, self).__init__()
        self.devices = self.getDevices()

    def getDevices(self):
        devices = self._findInterface(DEVICE_IFACE)
        return [BluetoothDevice(self._getDevice(x)) for x in devices]

    def getConnectedDevices(self, no_name=False):
        if no_name:
            devices = self.getDevices()
        else:
            devices = self.getNamedDevices()
            
        return [x for x in devices if x.connected]

    def getNamedDevices(self):
        devices = self.getDevices()
        nd = []
        for device in devices:
            try:
                name = device.name
                nd.append(device)
            except:
                pass

        return nd

    def getCurrentMediaPlayer(self):
        mp = self._findInterface(PLAYER_IFACE)
        if mp:
            return BluetoothMediaPlayer(str(mp[0]))
        else:
            return None

    def Discover(self, timeout=10):
        if self.adapter:
            self.adapter.DiscoverableTimeout = timeout
            self.adapter.Discoverable = True
            self.adapter.StartDiscovery()

    def StopDiscovery(self):
        self.adapter.StopDiscovery()

    def Forget(self, device):
        try:
            self.adapter.RemoveDevice(device.interface)
            return True
        except:
            return False
