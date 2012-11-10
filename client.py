#!/usr/bin/python

import socket
#import sys
from optparse import OptionParser
import time
import re
from random import choice

class Client():
    def __init__(self, hostname, port, username):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #socket.setdefaulttimeout(0)


    def waitForGame(self):
        print "CLIENT WAITING FOR GAME TO START!"
        while True:
            self.data = self.data + self.s.recv(1024)
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
            print self.data

            m = re.search("(?<=\[ACCEPT\|)[a-zA-Z0-9_]+", self.data)
            # Were we accepted?
            if m:
                self.username = m.group(0)
                self.data = re.sub("\[ACCEPT\|[a-zA-Z0-9_]+\]", "", self.data)
                break
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
    def makeTurn(self, topCard):
        def chooseCard(topCard):
            cardToPlay = "NN"
            cardToRemove = cardToPlay
            for card in self.myCards:
                if card[0] == "N":
                    cardToPlay = choice(["G", "B", "R", "Y"]) + card[1]
                    cardToRemove = card
                    break
                elif card[0] == topCard[0] or card[1] == topCard[1]:
                    cardToPlay = card
                    cardToRemove = card
                    break
            return cardToPlay, cardToRemove


        # Choose a random card!
        #if len(self.myCards) > 0:
        #    cardToPlay = choice(self.myCards)
        cardToPlay, cardToRemove = chooseCard(topCard)
        self.s.send("[PLAY|%s]" % cardToPlay)
        if cardToPlay == "NN":
            self.data = self.data + self.s.recv(1024)
            m = re.search("(?<=\[DEAL\|)([A-Z0-9]+\,?)+", self.data)
            if m:
                self.myCards = self.myCards + m.group(0).split(",")
                print "MY CARDS ARE %s" % self.myCards
                self.data = re.sub("\[DEAL\|([A-Z0-9]+\,?)+\]", "", self.data)

            cardToPlay, cardToRemove = chooseCard(topCard)
            self.s.send("[PLAY|%s]" % cardToPlay)


        while True:
            self.data = self.data + self.s.recv(1024)
            print self.data
            m = re.search("(?<=\[PLAYED\|)[a-zA-Z0-9]+,[A-Z0-9]+", self.data)
            if m:
                self.data = re.sub("\[PLAYED\|[a-zA-Z0-9]+,[A-Z0-9]+\]", "", self.data)
                if cardToRemove != "NN":
                    self.myCards.remove(cardToRemove)
                return
            m = re.search("(?<=\[INVALID\|)[^\]]+", self.data)
            if m:
                self.data = re.sub("\[INVALID\|[^\]]+\]", "", self.data)
                cardToPlay, cardToRemove = chooseCard(topCard)
                self.s.send("[PLAY|%s]" % cardToPlay)
            time.sleep(1)

    # For playing a game.
    def playGame(self):
        self.myCards = []

        while True:
            self.data = self.data + self.s.recv(1024)
            if self.data != "":
                print self.data

            # HAVE I BEEN DEALT?
            m = re.search("(?<=\[DEAL\|)([A-Z0-9]+\,?)+", self.data)
            if m:
                self.myCards = self.myCards + m.group(0).split(",")
                print "MY CARDS ARE %s" % self.myCards
                self.data = re.sub("\[DEAL\|([A-Z0-9]+\,?)+\]", "", self.data)

            # IS IT A TURN?
            m = re.search("(?<=\[GO\|)[A-Z0-9]+", self.data)
            if m:
                topCard = m.group(0)
                self.data = re.sub("\[GO\|[A-Z0-9]+\]", "", self.data)
                print "MY TURN!!!!", topCard, self.data

                self.makeTurn(topCard)

            m = re.search("(?<=\[GG\|)[a-zA-Z0-9_]+", self.data)
            if m:
                self.data = re.sub("\[GG\|[a-zA-Z0-9_]+\]", "", self.data)
                break

            #time.sleep(1)

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
