from dbus.mainloop.glib import DBusGMainLoop
from xml.parsers.expat import ExpatError
from xml.dom import minidom
import dbus
import gobject
import logging

loggerFormat = "%(levelname)s:\t%(created)f\t%(name)s(%(lineno)d)\t\t%(message)s"
logging.basicConfig(level = logging.CRITICAL, format = loggerFormat)
logging.getLogger("dbus.proxies").setLevel(logging.CRITICAL)

class AsyncDBusTree(object):
    INTROSPECTABLE="org.freedesktop.DBus.Introspectable"

    def __init__(self):
        self.busAliases={}
        self.uniqueBuses=[]
        self.sessionBus=dbus.SessionBus(mainloop = DBusGMainLoop())
        self.logger=logging.getLogger(__name__)
        self.openAsyncCalls = 0

        self.logger.info("Find buses")
        # Gather all common names and map them to unique names
        for bus in self.sessionBus.list_names():
            if not bus.startswith(":"):
                self.busAliases[str(self.sessionBus.get_name_owner(bus))]=bus
            else: self.uniqueBuses.append(bus)

        # Make the method call after a short delay
        gobject.timeout_add(1000, self.findPaths)
        self.loop = gobject.MainLoop()
        self.loop.run()

    def __makeCall(self, uniqueBus, path, reply_handler, error_handler):
        self.openAsyncCalls = self.openAsyncCalls + 1
        self.sessionBus.get_object(uniqueBus, path).Introspect(
            reply_handler = lambda *args : self.__recieveCall(reply_handler, *args),
            error_handler = lambda *args : self.__recieveCall(error_handler, *args),
            dbus_interface = AsyncDBusTree.INTROSPECTABLE)

    def __recieveCall(self, methodToCall, *args):
        self.openAsyncCalls = self.openAsyncCalls - 1
        self.logger.debug("%d open calls to process" % self.openAsyncCalls)
        if self.openAsyncCalls == 0: self.loop.quit()
        methodToCall(*args)

    def findPaths(self, path = "/"):
        for uniqueBus in self.uniqueBuses:
            self.findPathsWithBus(path, uniqueBus)

    def findPathsWithBus(self, path, uniqueBus):
            self.logger.info("Finding objects on bus %s with the path %s" % (uniqueBus, path))
            self.__makeCall(uniqueBus, path,
                reply_handler = lambda xml: self.processPathXML(xml, uniqueBus, path),
                error_handler = self.displayError)

    def processPathXML(self, xml, uniqueBus, path):
        self.logger.debug("Processing path XML for bus %s and path %s" % (uniqueBus, path))

        try:
            dom = minidom.parseString(xml)
            dom = dom.documentElement # Ignore the root node
        except ExpatError, e: 
            self.logger.warn("Bus %s, with path %s raised an XML exception. %s" %(uniqueBus, path, e))
            return

        newPath = path
        if newPath[-1] is not "/":
            newPath = newPath + "/"

        # Grab all available nodes
        nodes = dom.getElementsByTagName("node")
        for node in nodes:
            foundPath=newPath+node.getAttribute("name")
            self.findPathsWithBus(foundPath, uniqueBus)

        # If this path has more content, then print
        self.logger.debug("Calling to process the interface xml for %s : %s"%(uniqueBus, path))
        self.__makeCall(uniqueBus, path,
            reply_handler = lambda xml : self.processInterfaceXML(uniqueBus, xml, path),
            error_handler = self.displayError)

    def processInterfaceXML(self, uniqueBus, xml, path):
        self.logger.debug("Calling to process the interface xml for %s" % (path))
        self.logger.debug("Calling to process the interface xml for %s" % (path))
        dom = minidom.parseString(xml)

        # Gather all interfaces & methods
        print "Bus : %s, Path : %s" % (uniqueBus, path)
        for interface in dom.getElementsByTagName("interface"):
            print "\t\tInterface: %s" % interface.getAttribute("name")
            for method in interface.getElementsByTagName("method"):
                print "\t\t\tMethod: %s" % method.getAttribute("name")
        print

    def displayError(self, *args, **kwargs):
        print "############### ERROR ###################"
        print args
        print kwargs
        print "#########################################"

AsyncDBusTree()