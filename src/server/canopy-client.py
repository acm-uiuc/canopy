import SocketServer
import socket
import time
import sys
import config_loader
import threading
import daemon
import subprocess as sp
from collections import deque

"""The name of the YAML file from which to get configurations"""
CLIENT_CONFIG_FILE_NAME = "client-config.yml"

"""Set of all live connections"""
connections = {}

"""Buffer of most recent output from target process"""
target_buffer = deque() 


class CanopyClient(daemon.Daemon):
    """TCP socket-based client for Canopy"""

    def __init__(self, pidfile):
        """Creates a Canopy client based on client-config.yml file"""
        daemon.Daemon.__init__(self, pidfile, stderr='/tmp/canopyclient.log')
        self.parent_addr = (config["parent_host"], config["parent_port"])
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hb_thread = threading.Thread(target=heartbeat, args=(self.s,))


    def run(self):
        """Begin sending messages to canopy server and launch threads"""
        self.s.connect(self.parent_addr)
        self.hb_thread.start()
        cprint("\033[92mcanopy client connected to (%s, %d)" % self.parent_addr)

        # launch tcp server if relay node
        if not config["is_leaf"]:
            self.addr = (config["host"], config["port"])
            self.ss = SocketServer.ThreadingTCPServer(self.addr, CanopyTCPHandler)
            self.s_thread = threading.Thread(target=self.ss.serve_forever)
            self.s_thread.start()
            cprint("canopy server listening at (%s, %d)" % self.addr)

        # launch target process if leaf node
        if config["target"] is not None:
            target_command = config["target"].split(" ")
            proc = sp.Popen(target_command, shell=True, 
                            stdout=sp.PIPE, stderr=sp.PIPE)
            while proc.poll() is None:
                output = proc.stdout.readline()
                if len(target_buffer) >= config["bufsize"]:
                    target_buffer.popleft()
                target_buffer.append(output)


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


def heartbeat(socket):
    """Sends data to server on existing TCP socket"""

    try:
        while True:
            if not config["is_leaf"] and len(connections) > 0:
                socket.sendall(config["app_name"] + " " 
                               + " ".join(connections.values()))
            else:
                socket.sendall(config["app_name"])
            time.sleep(config["hb_interval"])
    except:
        cprint("\033[93mcanopy client detached from server.\033[93m")


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
