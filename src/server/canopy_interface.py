from flask import Flask
import flask_restful as fr

# callback function when API is called
callback = None

class CanopyLoggerResource(fr.Resource):
    """Resource to get logs from specific microservice"""

    def get(self):
        callback("logger_resource")
        return "canopy logger resource"

class CanopyCommandResource(fr.Resource):
    """Resource to send command to specific microservice""" 

    def get(self, command):
        callback("command_resource", command)
        return "canopy command resource" 

class CanopyInterface():
    """HTTP API interface for Canopy"""

    def __init__(self, address):
        self.address = address
        self.app = Flask(__name__)
        api = fr.Api(self.app)

        # set up resources
        api.add_resource(CanopyLoggerResource, "/canopy/log")
        api.add_resource(CanopyCommandResource, "/canopy/command/<string:command>")

    def run(self):
        host, port = self.address
        self.app.run(host, port)

def cb_func(*args):
    print(args)

if __name__ == "__main__":
    callback = cb_func
    a = CanopyInterface(("0.0.0.0", 8004))
    a.run()
