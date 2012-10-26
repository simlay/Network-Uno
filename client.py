#!/usr/bin/python

import socket
#import sys
from optparse import OptionParser
import time

class Client():
    def __init__(self, hostname, port, username):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def run(self):
        serverAddress = (self.hostname, self.port)
        self.s.connect(serverAddress)
        while True:
            self.s.send("[join|%s]" % self.username)
            data = self.s.recv(1024)
            print data
            time.sleep(1)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-p",
                      "--port",
                      dest="port",
                      help="which port to use",
                      type="int",
                      metavar="NUMBER",
                      default=36741)
    parser.add_option("--host",
                      dest="hostname",
                      help="hostname to connect to",
                      type="string",
                      metavar="STRING",
                      default="localhost")
    parser.add_option("-u",
                      "--username",
                      dest="username",
                      help="the username for the client",
                      type="string",
                      metavar="STRING",
                      default="simlay")
    (options, args) = parser.parse_args()


    client = Client(options.hostname, options.port, options.username)
    client.run()
