import gobject
import dbus
import dbus.service
import dbus.mainloop.glib

from .base import BluetoothBase
from .constants import *

IGNORE = [PROPERTIES_IFACE, OBJECT_IFACE, INTROSPECT_IFACE]

class BTSignals(object):
    SIGNAL_ADD_INTERFACE = "InterfacesAdded"
    SIGNAL_REMOVE_INTERFACE = "InterfacesRemoved"
    SIGNAL_PROPERTIES = "PropertiesChanged"

    GROUP_PROPERTIES = [SIGNAL_PROPERTIES]
    GROUP_INTERFACES = [SIGNAL_ADD_INTERFACE,
                        SIGNAL_REMOVE_INTERFACE]


class SignalCallback(BluetoothBase):

    def __init__(self, signal=None, interface=None,
                 property_name=False, callback=None, return_iface=False):
         self.tests = []
         super(SignalCallback, self).__init__()
         self.signal = signal
         self.interface = None
         self.property_name = property_name
         self.callback = callback
         self.return_iface = return_iface
         self.tests.append(self.check_signal)

         if self.interface:
             self.tests.append(self.check_interface)

         if self.property_name:
             self.tests.append(self.check_property)

    def check_signal(self, *args):
        return self.signal == args[0]

    def check_interface(self, *args):
        if self.interface:
            return self.interface == args[1]
        else:
            return True

    def check_property(self, *args):
        return self.property_name == str(args[2].keys()[0])

    def check_ignored(self, interface):
        return interface not in IGNORE

    def process_interface(self, signal, interfaces, path):

        if signal == BTSignals.SIGNAL_ADD_INTERFACE:
            for interface, props in interfaces.iteritems():
                if all((self.check_ignored(interface),
                        self.check_interface(0,interface))):

                    if self.return_iface:
                        iface = dbus.Interface(self._getDevice(path=path),
                                               interface)
                    else:
                        iface = None
                    self.callback(interface, path, iface)


        else:
            for interface in interfaces:
                if interface not in IGNORE:
                    self.callback(interface, path, None)

    def property_signal(self, *args):
        signal, interface, changed, path = args
        if all(test(*args) for test in self.tests):
            self.callback(interface, changed, path)

    def interface_signal(self, *args):
        if args[0] == self.signal:
            self.process_interface(*args)


class BluetoothSignalHandler(dbus.service.Object, BluetoothBase):

    def __init__(self):
        super(BluetoothSignalHandler, self).__init__()
        self.callbacks = []
        self.mainloop = None

    def __call__(self):
        self.loop()

    def interface_added(self, path, interfaces):
        for cb in self.callbacks:
            cb.interface_signal(BTSignals.SIGNAL_ADD_INTERFACE,
                                interfaces,
                                path)

    def property_changed(self, interface, changed, invalidated, path):
        for cb in self.callbacks:
            cb.property_signal(BTSignals.SIGNAL_PROPERTIES,
                               interface,
                               changed,
                               path)

    def interface_removed(self, path, interfaces):
        for cb in self.callbacks:
            cb.interface_signal(BTSignals.SIGNAL_REMOVE_INTERFACE,
                                interfaces,
                                path)

    def add_callback(self, signal=None, interface=None, property_name=None,
                     callback=None, return_iface=False):
        self.callbacks.append(SignalCallback(signal=signal,
                                             interface=interface,
                                             property_name=property_name,
                                             callback=callback,
                                             return_iface=return_iface))

    def stop(self):
        self.mainloop.quit()

    def loop(self):

        gobject.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = dbus.SystemBus()
        #dbus.service.Object.__init__(self, dbus.SystemBus(), "/anto/test")

        self.bus.add_signal_receiver(self.interface_added,
                bus_name="org.bluez",
                dbus_interface=OBJECT_IFACE,
                signal_name=BTSignals.SIGNAL_ADD_INTERFACE)

        self.bus.add_signal_receiver(self.interface_removed,
                bus_name="org.bluez",
                dbus_interface=OBJECT_IFACE,
                signal_name=BTSignals.SIGNAL_REMOVE_INTERFACE)

        self.bus.add_signal_receiver(self.property_changed,
                bus_name="org.bluez",
                dbus_interface="org.freedesktop.DBus.Properties",
                signal_name=BTSignals.SIGNAL_PROPERTIES,
                path_keyword = "path")

        """Start the BluePlayer by running the gobject mainloop()"""
        self.mainloop = gobject.MainLoop()
        self.mainloop.run()
