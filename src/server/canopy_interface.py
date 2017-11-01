from flask import Flask
from enum import Enum
import flask_restful as fr


# valid command classes
class Command(Enum):
    LOG = 1
    COMMAND = 2
    STATUS = 3


# callback function when API is called
callback = None


class CanopyLoggerResource(fr.Resource):
    """Resource to get logs from specific microservice"""

    def get(self, service):
        return callback(Command.LOG, service)


class CanopyStatusResource(fr.Resource):
    """Resource to get status of all microservices"""

    def get(self):
        return callback(Command.STATUS)


class CanopyInterface():
    """HTTP API interface for Canopy"""

    def __init__(self, address):
        self.address = address
        self.app = Flask(__name__)
        api = fr.Api(self.app)

        # set up resources
        api.add_resource(CanopyLoggerResource, "/canopy/log/<string:service>")
        api.add_resource(CanopyStatusResource,
                         "/canopy/status")

    def run(self):
        host, port = self.address
        self.app.run(host, port)


def cb_func(*args):
    print(args)


if __name__ == "__main__":
    callback = cb_func
    a = CanopyInterface(("0.0.0.0", 8004))
    a.run()
