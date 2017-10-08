import SocketServer
import config_loader
import threading
import sys
import daemon

"""The name of the YAML file from which to get configurations"""
SERVER_CONFIG_FILE_NAME = "server-config.yml"

"""Set of all live connections"""
connections = {}


class CanopyServer(daemon.Daemon):
    """TCP socket-based server for Canopy"""

    def __init__(self, pidfile):
        """Creates a Canopy server based on server-config.yml file"""
        daemon.Daemon.__init__(self, pidfile, stderr='/tmp/canopyserver.log')
        self.addr = (config["host"], config["port"])

    def run(self):
        """Begin listening asynchronously for canopy clients"""
        self.s = SocketServer.ThreadingTCPServer(self.addr, CanopyTCPHandler)
        self.s_thread = threading.Thread(target=self.s.serve_forever)
        self.s_thread.start()
        cprint("canopy server listening at (%s, %d)" % self.addr)


class CanopyTCPHandler(SocketServer.StreamRequestHandler):
    """Handle connections and maintain set of live clients"""

    def handle(self):
        cprint("\033[92mnew connection: (%s, %d)\033[0m" % self.client_address)
        self.request.settimeout(config["timeout"])
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            # request terminated or timed out
            if self.data == "":
                break
            connections[self.client_address] = self.data.split(' ')
        cprint("\033[93mend connection: (%s, %d)\033[0m" % self.client_address)
        
        # remove client from live connections
        del connections[self.client_address]


def cprint(message):
    """Custom wrapper to print depending on config silent setting"""

    if not config["silent"]:
        sys.stderr.write(message+"\n")


if __name__ == "__main__":
    config = config_loader.load(SERVER_CONFIG_FILE_NAME)
    daemon = CanopyServer('/tmp/canopyserver-daemon.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    print("Usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(2)
