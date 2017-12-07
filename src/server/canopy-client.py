import socketserver
import socket
import time
import sys
import config_loader
import threading
import daemon
import subprocess as sp
import queue

"""The name of the YAML file from which to get configurations"""
CLIENT_CONFIG_FILE_NAME = "client-config.yml"

"""Set of all live connections"""
connections = {}

"""Buffer of most recent output from target process"""
target_buffer = queue.Queue()


class CanopyClient(daemon.Daemon):
    """TCP socket-based client for Canopy"""

    def __init__(self, pidfile):
        """Creates a Canopy client based on client-config.yml file"""
        daemon.Daemon.__init__(self, pidfile, stderr='/tmp/canopyclient.log')

        # Load addresses from config
        self.hb_addr = (config["hb_host"], config["hb_port"])
        self.cmd_addr = (config["cmd_host"], config["cmd_port"])
        self.parent_addr = (config["parent_host"], config["parent_port"])

    def run(self):
        """Begin sending messages to canopy server and launch threads"""

        # Begin listening for heartbeats
        self.hb_s = socketserver.ThreadingTCPServer(self.hb_addr,
                                                    HeartbeatTCPHandler)
        self.hb_thread = threading.Thread(target=self.hb_s.serve_forever)
        self.hb_thread.start()
        cprint("\033[92mcanopy heartbeat socket listening at (%s, %d)\033[0m\n"
               % self.hb_addr)

        # Begin listening for commands
        self.cmd_s = socketserver.ThreadingTCPServer(self.cmd_addr,
                                                     CommandTCPHandler)
        self.cmd_thread = threading.Thread(target=self.cmd_s.serve_forever)
        self.cmd_thread.start()
        cprint("\033[92mcanopy command socket listening at (%s, %d)\033[0m\n"
               % self.cmd_addr)

        # Begin transmitting heartbeats
        self.hb_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hb_s.connect(self.parent_addr)
        self.hb_thread = threading.Thread(target=HeartbeatThread,
                                          args=(self.hb_s,))
        self.hb_thread.start()
        cprint("\033[92mcanopy client connected to (%s, %d)\033[0m\n"
               % self.parent_addr)

        # launch target process if leaf node
        if config["target"] is not None:
            cprint("\033[95mBeginning target process: %s\033[0m\n"
                   % config["target"])
            target_command = config["target"].split(" ")
            proc = sp.Popen(target_command, cwd=sys.path[0],
                            stdout=sp.PIPE, stderr=sp.STDOUT)
            while proc.poll() is None:
                output = proc.stdout.readline()
                if target_buffer.qsize() >= config["bufsize"]:
                    target_buffer.get()
                target_buffer.put(output)
            cprint("\033[95mTarget process terminated.\033[0m\n")

            # once process ends, store last BUFSIZE lines
            for line in proc.stdout:
                if target_buffer.qsize() >= config["bufsize"]:
                    target_buffer.get()
                target_buffer.put(line)


class HeartbeatTCPHandler(socketserver.StreamRequestHandler):
    """Handle connections and maintain set of live clients"""

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


class CommandTCPHandler(socketserver.StreamRequestHandler):
    """Listen for commands from canopy server"""

    def handle(self):
        cprint("\033[92mcommand socket connected.\033[0m\n")

        # self.request is the TCP socket connected to the client
        data = self.request.recv(1024).strip().decode()
        command_args = data.split()
        if command_args[0] == "LOGS":
            service = command_args[1]
            if service == config["app_name"]:
                cprint("Return logs for %s\n" % service)
                target_logs = b" ".join(target_buffer.queue)
                self.request.sendall(target_logs)
            elif service in connections:
                cprint("Relay log request for %s\n" % service)
                service_addr = connections[service]
                cmd_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cmd_s.connect(service_addr)
                cmd_s.sendall(b"LOGS %s" % service)
                logs = cmd_s.recv(1024).strip()
                self.request.sendall(logs)
            else:
                cprint("Reject log request for %s\n" % service)
                self.request.sendall(b"")
        else:
            # TODO: implement commands
            pass
        cprint("    ping: %s\n" % data)


def HeartbeatThread(socket):
    """Sends data to server on existing TCP socket"""

    try:
        # transmit command socket address and wait for ack
        while True:
            addr = (config["cmd_host"], config["cmd_port"])
            socket.sendall(("%s:%d" % addr).encode('utf-8'))
            answer = socket.recv(1024).strip()
            if answer == b"ACK":
                break

        while True:
            if not config["is_leaf"] and len(connections) > 0:
                socket.sendall(" ".join(connections.values()))
            elif not config["is_leaf"]:
                socket.sendall(config["DORMANT_RELAY"])
            else:
                socket.sendall(config["app_name"].encode('utf-8'))
            time.sleep(config["hb_interval"])
    except:
        cprint(str(sys.exc_info()[1]))
        socket.shutdown()
        cprint("\033[93mcanopy client detached from server.\033[0m\n")


def cprint(message):
    """Custom wrapper to print depending on config silent setting"""

    if not config["silent"]:
        sys.stderr.write(message)


if __name__ == "__main__":
    config = config_loader.load(CLIENT_CONFIG_FILE_NAME)
    daemon = CanopyClient('/tmp/canopyclient-daemon.pid')
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
