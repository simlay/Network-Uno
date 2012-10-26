#!/usr/bin/python

import socket
#import sys
from optparse import OptionParser
import time
import re

class Client():
    def __init__(self, hostname, port, username):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def waitForGame(self):
        while True:
            self.data = self.s.recv(1024)
            print self.data
            time.sleep(1)
    def waitInLobby(self):

        while True:
            self.s.send("[JOIN|%s]" % self.username)
            self.data = self.s.recv(1024)
            m = re.search("(?<=\[ACCEPT\|)[a-zA-Z0-9_]+", self.data)
            # Were we accepted?
            if m:
                self.data = re.sub("ACCEPT[a-zA-Z0-9_]+", "", self.data)
                break
            print self.data
            # Let's just print it.

            time.sleep(1)


    def run(self):
        serverAddress = (self.hostname, self.port)
        self.s.connect(serverAddress)
        self.waitInLobby()
        self.waitForGame()

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
