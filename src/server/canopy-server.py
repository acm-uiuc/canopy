import socketserver
import socket
import config_loader
import threading
import sys
import daemon
import canopy_interface as ci
from canopy_interface import Command

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

        # set up API interface
        ci.callback = self.__command_callback
        web_addr = (config["web_host"], config["web_port"])
        self.interface = ci.CanopyInterface(web_addr)

    def run(self):
        """Begin listening asynchronously for canopy clients"""

        # run heartbeat TCP server
        self.s = socketserver.ThreadingTCPServer(self.addr,
                                                 HeartbeatTCPHandler)
        self.s_thread = threading.Thread(target=self.s.serve_forever)
        self.s_thread.start()
        cprint("canopy server listening at (%s, %d)\n" % self.addr)

        # run API interface
        self.interface.run()

    def __command_callback(self, cmd_type, *args):
        """Connects to CommandTCPHandler of a client and relays command"""

        retval = None

        if cmd_type == Command.LOG:
            cprint("canopy server log callback")
            service = args[0]

            # check validity of referenced service
            if service in connections:
                service_addr = connections[service]
                cmd_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cmd_s.connect(service_addr)

                cmd_s.sendall(b"LOGS %s" % service.encode("utf-8"))
                logs = cmd_s.recv(1024).strip().decode()
                cmd_s.close()
                retval = logs

        elif cmd_type == Command.COMMAND:
            # TODO: implement commands
            pass

        elif cmd_type == Command.STATUS:
            cprint("canopy server status callback")
            retval = " ".join(connections.keys())

        return retval


class HeartbeatTCPHandler(socketserver.StreamRequestHandler):
    """Handle connections and maintain set of live clients"""

    client_services = set()

    def handle(self):
        cprint("\033[92mnew connection: (%s, %d)\033[0m" % self.client_address)
        self.request.settimeout(config["timeout"])

        # maintain set of services on client
        client_services = set()

        # receive and initialize socket on command port
        while True:
            try:
                command_bytes = self.request.recv(1024).strip()
                command_addr = command_bytes.decode().split(":")
                command_addr[1] = int(command_addr[1])
                self.request.sendall(b"ACK")
                break
            except ValueError:
                self.request.sendall(b"NACK")
        cprint("    set command addr: %s" % command_addr)

        while True:
            # self.request is the TCP socket connected to the client
            data = self.request.recv(1024).strip()

            # request terminated or timed out
            if data == b"":
                break

            # update list of live services
            new_client_services = set()
            for service in data.split(b" "):
                if service is not b"DORMANT_RELAY":
                    new_client_services.add(service.decode())

            # new connections
            for new_serv in new_client_services - client_services:
                connections[new_serv] = tuple(command_addr)
                client_services.add(new_serv)

            # broken connections
            for broken_serv in client_services - new_client_services:
                del connections[broken_serv]
                client_services.remove(broken_serv)

        cprint("\033[93mend connection: (%s, %d)\033[0m\n"
               % self.client_address)

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
    print("Usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(2)
