import socket
import time
import sys
import config_loader
import signal
import threading

"""The name of the YAML file from which to get configurations""" 
CLIENT_CONFIG_FILE_NAME = "client-config.yml"

class CanopyClient():
    """TCP socket-based client for Canopy"""

    def __init__(self):
        """Creates a Canopy client based on configurations in client-config.yml"""
        self.addr = (config["host"], config["port"])
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hb_thread = threading.Thread(target=heartbeat, args=(self.s,))

    def run(self):
        """Begin sending messages to canopy server and launch threads"""
        self.s.connect(self.addr)
        self.hb_thread.start()
        cprint("canopy client connected to (%s, %d)" % self.addr)
        
    def stop(self):
        """Stop sending messages to canopy server"""
        cprint("Shutting down canopy client")
        self.s.close()


"""Sends data to server on existing TCP socket"""
def heartbeat(socket):
    try:
        while True:
            socket.sendall("heartbeat")
            time.sleep(config["timeout"])
    except:
        pass

"""Custom wrapper to print depending on config silent setting"""
def cprint(message):
    if not config["silent"]: print(message)

if __name__ == "__main__":
    config = config_loader.load(CLIENT_CONFIG_FILE_NAME)
    canopy_client = CanopyClient()
    canopy_client.run()
    if raw_input() == "stop":
        canopy_client.stop()
