import dbus

from .constants import *

class BluetoothBase(object):

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.adapter = self._findAdapter()


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

    def getInterface(self, interface, path):
        return dbus.Interface(self._getDevice(path), interface)

    def getProperties(self, path):
        return self.getInterface(PROPERTIES_IFACE, path)
