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
        print "CLIENT WAITING FOR GAME TO START!"
        while True:
            self.data = self.s.recv(1024)
            m = re.search("(?<=\[START\|)([a-zA-Z0-9]+\,?)+", self.data)
            if m:
                self.playerList = m.group(0).split(",")
                self.data = re.sub("\[START\|([a-zA-Z0-9]+\,?)+\]", "", self.data)
                print "STARTING A GAME WITH %s" % self.playerList
                break

            print self.data
            time.sleep(1)

    def waitInLobby(self):

        while True:
            self.s.send("[JOIN|%s]" % self.username)
            self.data = self.s.recv(1024)
            m = re.search("(?<=\[ACCEPT\|)[a-zA-Z0-9_]+", self.data)
            # Were we accepted?
            if m:
                self.username = m.group(0)
                self.data = re.sub("ACCEPT[a-zA-Z0-9_]+\]", "", self.data)
                break
            print self.data
            # Let's just print it.

            time.sleep(1)

        # Get the player list. (I'll probably throw this away when I'm done with it.)
        m = re.search("(?<=\[PLAYERS\|)([a-zA-Z0-9]+\,?)+", self.data)
        if m:
            self.playerList = m.group(0).split(",")
            self.data = re.sub("\[PLAYERS\|([a-zA-Z0-9]+\,?)+\]", "", self.data)
            print self.playerList
        print "CLIENT EXITING THE LOBBY!"



    # Send a valid card to play.
    def makeTurn(self):
        cardToPlay = self.myCards[0]
        self.myCards.remove(cardToPlay)
        message = "[PLAY|%s]" % cardToPlay
        self.s.send(message)

    # For playing a game.
    def playGame(self):
        self.myCards = []

        while True:
            self.data = self.s.recv(1024)

            # HAVE I BEEN DEALT?
            m = re.search("(?<=\[DEAL\|)([A-Z0-9]+\,?)+", self.data)
            if m:
                self.myCards = self.myCards + m.group(0).split(",")
                print "MY CARDS ARE %s" % self.myCards
                self.data = re.sub("\[DEAL\|([A-Z0-9]+\,?)+\]", "", self.data)

            # WHAT'S THE TOP?
            m = re.search("(?<=\[TOP\|)[A-Z0-9]+", self.data)
            if m:
                self.topCard = m.group(0)
                print "THE TOP CARD IS %s" % self.topCard
                self.data = re.sub("\[TOP\|[a-zA-Z0-9]+\]", "", self.data)

            # IS IT A TURN?
            m = re.search("(?<=\[TAKETURN\|)[a-zA-Z0-9_]+", self.data)
            if m:
                myTurn = m.group(0) == self.username
                self.data = re.sub("\[TAKETURN\|[a-zA-Z0-9_]+\]", "", self.data)

                if myTurn:
                    print "IT'S MY TURN!"
                    self.makeTurn()
                    # LET'S MAKE A MOVE!

            print self.data

            time.sleep(1)

    def run(self):
        serverAddress = (self.hostname, self.port)
        self.s.connect(serverAddress)
        self.waitInLobby()
        self.waitForGame()
        self.playGame()

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
