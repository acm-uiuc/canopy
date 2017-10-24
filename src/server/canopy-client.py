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
        self.parent_addr = (config["parent_host"], config["parent_port"])
        self.cmd_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cmd_thread = threading.Thread(target=CommandThread, args=(self.cmd_s,))
        self.hb_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hb_thread = threading.Thread(target=HeartbeatThread, args=(self.hb_s, self.cmd_s,))


    def run(self):
        """Begin sending messages to canopy server and launch threads"""
        global target_buffer

        self.hb_s.connect(self.parent_addr)
        self.cmd_s.connect(self.parent_addr)
        cprint("\033[92mcanopy client connected to (%s, %d)\n    local: hb:(%s, %d) cmd:(%s, %d)\033[0m\n" % (self.parent_addr[0], self.parent_addr[1], self.hb_s.getsockname()[0], self.hb_s.getsockname()[1], self.cmd_s.getsockname()[0], self.cmd_s.getsockname()[1]))
        self.hb_thread.start()

        # launch tcp server if relay node
        if not config["is_leaf"]:
            self.addr = (config["host"], config["port"])
            self.ss = socketserver.ThreadingTCPServer(self.addr, CanopyTCPHandler)
            self.s_thread = threading.Thread(target=self.ss.serve_forever)
            self.s_thread.start()
            cprint("canopy server listening at (%s, %d)" % self.addr)

        # launch target process if leaf node
        if config["target"] is not None:
            cprint("\033[95mBeginning target process: %s\033[0m\n" % config["target"])
            target_command = config["target"].split(" ")
            proc = sp.Popen(target_command, cwd=sys.path[0], 
                            stdout=sp.PIPE, stderr=sp.STDOUT)
            while proc.poll() is None:
                output = proc.stdout.readline().decode()
                if target_buffer.qsize() >= config["bufsize"]:
                    target_buffer.get()
                target_buffer.put(output)
            # once process ends, store last BUFSIZE lines 
            for line in proc.stdout:
                if target_buffer.qsize() >= config["bufsize"]:
                    target_buffer.get()
                target_buffer.put(line.decode())
            while not target_buffer.empty():
                cprint(target_buffer.get())


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


def HeartbeatThread(socket, cmd_socket):
    """Sends data to server on existing TCP socket"""

    try:
        # transmit command socket address
        socket.sendall(("%s:%d" % cmd_socket.getsockname()).encode('utf-8'))

        while True:
            if not config["is_leaf"] and len(connections) > 0:
                socket.sendall(" ".join(connections.values()))
            elif not config["is_leaf"]:
                socket.sendall(config["DORMANT_RELAY"])
            else:
                cprint("Transmitting %s\n" % config["app_name"])
                socket.sendall(config["app_name"])
            time.sleep(config["hb_interval"])
    except:
        cprint(str(sys.exc_info()[1]))
        socket.shutdown()
        cprint("\033[93mcanopy client detached from server.\033[0m\n")


def CommandThread(socket):
    """Listens and relays commands on existing TCP socket"""

    # transmit 

    try:
        while True:
            socket.recv(1024).decode()
             
    except:
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
