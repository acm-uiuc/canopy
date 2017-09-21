import SocketServer
import config_loader
import threading

"""The name of the YAML file from which to get configurations""" 
SERVER_CONFIG_FILE_NAME = "server-config.yml"

"""Set of all live connections"""
connections = set()

class CanopyServer():
    """TCP socket-based server for Canopy"""

    def __init__(self):
        """Creates a Canopy server based on configurations in server-config.yml"""
        self.addr = (config["host"], config["port"])
        self.s = SocketServer.ThreadingTCPServer(self.addr, CanopyTCPHandler)
        self.s_thread = threading.Thread(target=self.s.serve_forever)

    def run(self):
        """Begin listening asynchronously for canopy clients"""
        self.s_thread.start()
        cprint("canopy server listening at (%s, %d)" % self.addr)

    def stop(self):
        """Stop listening asynchronously for canopy clients"""
        cprint("Shutting down canopy server")
        self.s.shutdown()

 
class CanopyTCPHandler(SocketServer.StreamRequestHandler):
    """Handle connections and maintain set of live clients"""

    def handle(self):
        print("\033[92mnew connection: (%s, %d)\033[0m" % self.client_address)
        connections.add(self.client_address)
        self.request.settimeout(config["timeout"])
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            # request terminated or timed out
            if self.data == "":
                break
        cprint("\033[93mend connection: (%s, %d)\033[0m" % self.client_address)
        connections.remove(self.client_address)

"""Custom wrapper to print depending on config silent setting"""
def cprint(message):
    if not config["silent"]: print(message)

if __name__ == "__main__":
    config = config_loader.load(SERVER_CONFIG_FILE_NAME)
    canopy_server = CanopyServer()
    canopy_server.run()
    if raw_input() == "stop":
        canopy_server.stop()
