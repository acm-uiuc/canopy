import sys
import time
from daemon import Daemon


class ServerDaemon(Daemon):
    def run(self):
        while True:
            # Your Code here:
            print("Hello There!")
            time.sleep(1)


if __name__ == "__main__":
    daemon = ServerDaemon('/tmp/canopysd-daemon.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print("Unknown Command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("Usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
