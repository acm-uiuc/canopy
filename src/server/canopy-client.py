import socket
import time
import sys
import config_loader
import threading
import daemon

"""The name of the YAML file from which to get configurations"""
CLIENT_CONFIG_FILE_NAME = "client-config.yml"


class CanopyClient(daemon.Daemon):
    """TCP socket-based client for Canopy"""

    def __init__(self, pidfile):
        """Creates a Canopy client based on client-config.yml file"""
        daemon.Daemon.__init__(self, pidfile, stderr='/tmp/canopyclient.log')
        self.addr = (config["host"], config["port"])
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hb_thread = threading.Thread(target=heartbeat, args=(self.s,))

    def run(self):
        """Begin sending messages to canopy server and launch threads"""
        self.s.connect(self.addr)
        self.hb_thread.start()
        cprint("canopy client connected to (%s, %d)" % self.addr)


def heartbeat(socket):
    """Sends data to server on existing TCP socket"""

    try:
        while True:
            socket.sendall("heartbeat")
            time.sleep(config["timeout"])
    except:
        pass


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
