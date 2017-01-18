import dbus

from .base import BluetoothBase
from .constants import *

class BluetoothDevice(BluetoothBase):
    def __init__(self, device):
        super(BluetoothDevice, self).__init__()
        self.device = device
        self.props = dbus.Interface(device, PROPERTIES_IFACE)
        self.get = lambda prop: self.props.Get(DEVICE_IFACE, prop)
        self.set = lambda prop, value: self.props.Set(DEVICE_IFACE, prop, value)
        self.interface = dbus.Interface(device, DEVICE_IFACE)

    @property
    def trusted(self):
        return bool(self.get("Trusted"))

    @trusted.setter
    def trusted(self):
        self.Trust(bool(value))

    @property
    def connected(self):
        return bool(self.get("Connected"))

    @connected.setter
    def connected(self, value):
        self.Connect(bool(value))

    @property
    def paired(self):
        return bool(self.get("Paired"))

    @property
    def name(self):
        return str(self.get("Name"))

    def Connect(self, connect=True):
        if connect:
            try:
                self.interface.Connect()
                return True
            except:
                return False

        else:
            try:
                self.interface.Disconnect()
                return True
            except:
                return False

    def Disconnect(self):
        return self.Connect(False)

    def Trust(self, trusted=True):
        self.set("Trusted", trusted)

    def Pair(self):
        if not self.paired:
            self.interface.Pair()
            self.Trust()
