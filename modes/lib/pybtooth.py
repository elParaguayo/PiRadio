import dbus
from time import sleep

SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + '.Agent1'
ADAPTER_IFACE = SERVICE_NAME + ".Adapter1"
DEVICE_IFACE = SERVICE_NAME + ".Device1"
PLAYER_IFACE = SERVICE_NAME + '.MediaPlayer1'
TRANSPORT_IFACE = SERVICE_NAME + '.MediaTransport1'
OBJECT_IFACE =  "org.freedesktop.DBus.ObjectManager"
PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"


class BluetoothDevice(object):
    def __init__(self, device):
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

    @paired.setter
    def paired(self, value):
        self.Pair(bool(value))

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


class BluetoothMediaPlayer(object):

    def __init__(self, path):
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


class BluetoothManager(object):

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.adapter = self._findAdapter()
        self.devices = self.getDevices()

    def getDevices(self):
        devices = self._findInterface(DEVICE_IFACE)
        return [BluetoothDevice(self._getDevice(x)) for x in devices]

    def getConnectedDevices(self):
        devices = self.getNamedDevices()
        bd = [BluetoothDevice(self._getDevice(x)) for x in devices]
        return [x for x in bd if x.connected]

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

    def _getManagedObjects(self):
        manager = dbus.Interface(self.bus.get_object(SERVICE_NAME, "/"),
                                 OBJECT_IFACE)
        return manager.GetManagedObjects()

    def _findInterface(self, interface):
        paths = []
        objects = self._getManagedObjects()
        for path, ifaces in objects.iteritems():
            device = ifaces.get(interface)
            if device is None:
                continue
            paths.append(path)

        return paths

    def _getDevice(self, path):
        """Get a device from a dbus path"""
        return self.bus.get_object(SERVICE_NAME, path)

    def _findAdapter(self):

        adapters = self._findInterface(ADAPTER_IFACE)
        if adapters:
            device = self._getDevice(adapters[0])
            return dbus.Interface(device, ADAPTER_IFACE)
        else:
            return None

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
