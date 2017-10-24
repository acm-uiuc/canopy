import socketserver
import socket
import config_loader
import threading
import sys
import daemon
import queue

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
        self.cmd_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        """Begin listening asynchronously for canopy clients"""
        self.s = socketserver.ThreadingTCPServer(self.addr, CanopyTCPHandler)
        self.s_thread = threading.Thread(target=self.s.serve_forever)
        self.s_thread.start()
        cprint("canopy server listening at (%s, %d)\n" % self.addr)

    def query_logs(self, service):
        """Retrieve memory from a service running on a client"""
        cprint("Querying logs from: \033[95m%s\033[0m\n" % service)


class CanopyTCPHandler(socketserver.StreamRequestHandler):
    """Handle connections and maintain set of live clients"""

    client_services = set()

    # associate services with client command port
    command_addr = None

    def handle(self):
        cprint("\033[92mnew connection: (%s, %d)\033[0m" % self.client_address)
        self.request.settimeout(config["timeout"])
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            cprint("    ping: %s" % self.data)

            # first packet is command port
            if self.command_addr is None:
                self.command_addr = self.data
                cprint("    set command addr: %s" % self.command_addr)
                continue

            # request terminated or timed out
            if self.data == b"":
                break

            # update list of live services
            new_client_services = set()
            for service in self.data.split(b" "):
                if service is not b"DORMANT_RELAY":
                    new_client_services.add(service)

            # new connections
            for new_serv in new_client_services - self.client_services:
                connections[new_serv] = self.client_address
                self.client_services.add(new_serv)

            # broken connections
            for broken_serv in self.client_services - new_client_services:
                del connections[broken_serv]
                self.client_services.remove(broken_serv)
            
        cprint("\033[93mend connection: (%s, %d)\033[0m\n" % self.client_address)
        
        # remove client from live connections
        for serv in self.client_services:
            del connections[serv] 


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
    elif len(sys.argv) == 3:
        if 'logs' == sys.argv[1]:
            daemon.query_logs(sys.argv[2])
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    print("Usage: %s start|stop|restart|logs [service]" % sys.argv[0])
    sys.exit(2)
