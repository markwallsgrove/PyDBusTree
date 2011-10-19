from dbus.exceptions import DBusException/
from dbus.mainloop.glib import DBusGMainLoop
from xml.dom import minidom
import dbus
import logging
logging.disable(logging.CRITICAL)

def findInterfaces(bus, path):
    introspect = sessionBus.get_object(bus, path).Introspect(dbus_interface = 'org.freedesktop.DBus.Introspectable')
    dom = minidom.parseString(introspect)

    # Gather all interfaces & methods
    for interface in dom.getElementsByTagName("interface"):
        print "\t\tInterface: %s" % interface.getAttribute("name")
        for method in interface.getElementsByTagName("method"):
            print "\t\t\tMethod: %s" % method.getAttribute("name")

def findPaths(bus, path = "/"):
    try:
        introspect = sessionBus.get_object(bus, path).Introspect(dbus_interface = 'org.freedesktop.DBus.Introspectable')
        dom = minidom.parseString(introspect)
        dom = dom.documentElement # Ignore the root node

        newPath = path
        if newPath[-1] is not "/":
            newPath = newPath + "/"

        # Grab all available nodes
        nodes = dom.getElementsByTagName("node")
        for node in nodes:
            foundPath = newPath + node.getAttribute("name")
            findPaths(bus, foundPath)

        # If this path has more content, then print
        print "\tPath: %s" % path
        findInterfaces(bus, path)
    except DBusException: pass

busAliases = {}
uniqueBuses = []
sessionBus = dbus.SessionBus(mainloop = DBusGMainLoop())

# Gather all common names and map them to unique names
for bus in sessionBus.list_names():
    if not bus.startswith(":"):
        busAliases[str(sessionBus.get_name_owner(bus))] = bus
    else: uniqueBuses.append(bus)

# Display common names with unique names
for bus in uniqueBuses:
    readableName = ""
    if bus in busAliases.keys():
        readableName = "%s" % busAliases.get(bus)
    print "Bus: %s (%s)" % (bus, readableName)
    findPaths(bus)
