#!/usr/bin/python

import socket
import select
import sys
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
        None
        #print "CLIENT WAITING FOR GAME TO START!"
        #while True:
        #    print self.data
        #    m = re.search("(?<=\[STARTGAME\|)([a-zA-Z0-9_]+\,?)*", self.data)
        #    if m:
        #        self.playerList = m.group(0).split(",")
        #        self.data = re.sub("\[STARTGAME\|([a-zA-Z0-9_]+\,?)*\]", "", self.data)
        #        print "STARTING A GAME WITH %s" % self.playerList
        #        break
        #    self.data = self.data + self.s.recv(1024)

        #    #print self.data
        #print "STARTING THE GAME"

    def waitInLobby(self):

        while True:
            message = "[JOIN|%s]" % self.username
            #print "writing message {%s}" % message
            self.s.send(message)
            self.data = self.s.recv(1024)
            print self.data

            m = re.search("(?<=\[ACCEPT\|)[a-zA-Z0-9_]+", self.data)
            # Were we accepted?
            if m:
                self.username = m.group(0)
                self.data = re.sub("\[ACCEPT\|[a-zA-Z0-9_]+\]", "", self.data)
                break

            m = re.search("(?<=\[WAIT\|)[a-zA-Z0-9_]+", self.data)
            if m:
                self.username = m.group(0)
                self.data = re.sub("\[WAIT\|[a-zA-Z0-9_]+\]", "", self.data)
                break

        # Get the player list. (I'll probably throw this away when I'm done with it.)
        m = re.search("(?<=\[PLAYERS\|)([a-zA-Z0-9]+\,?)+", self.data)
        if m:
            self.playerList = m.group(0).split(",")
            self.data = re.sub("\[PLAYERS\|([a-zA-Z0-9_]+\,?)+\]", "", self.data)
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


        cardToPlay, cardToRemove = chooseCard(topCard)
        print "Playing card %s given %s" % (cardToPlay, topCard)
        self.s.send("[PLAY|%s]" % cardToPlay)
        if cardToRemove != "NN":
            self.myCards.remove(cardToRemove)

        return
        if cardToPlay == "NN":
            self.data = self.data + self.s.recv(1024)
            m = re.search("(?<=\[DEAL\|)([A-Z0-9]+\,?)+", self.data)
            if m:
                self.myCards = self.myCards + m.group(0).split(",")
                print "MY CARDS ARE %s" % self.myCards
                self.data = re.sub("\[DEAL\|([A-Z0-9]+\,?)+\]", "", self.data)

            cardToPlay, cardToRemove = chooseCard(topCard)
            self.s.send("[PLAY|%s]" % cardToPlay)
        return

        while True:
            self.data = self.data + self.s.recv(1024)
            print self.data
            m = re.search("(?<=\[PLAYED\|)[a-zA-Z0-9_]+,[A-Z0-9]+", self.data)
            if m:
                self.data = re.sub("\[PLAYED\|[a-zA-Z0-9_]+,[A-Z0-9]+\]", "", self.data)
                if cardToRemove != "NN":
                    self.myCards.remove(cardToRemove)
                return
            m = re.search("(?<=\[INVALID\|)[^\]]+", self.data)
            if m:
                self.data = re.sub("\[INVALID\|[^\]]+\]", "", self.data)
                cardToPlay, cardToRemove = chooseCard(topCard)
                self.s.send("[PLAY|%s]" % cardToPlay)
            #time.sleep(1)

    # For playing a game.
    def playGame(self):
        self.myCards = []

        while True:

            readable , writable, exceptional = select.select([self.s], [], [], 1)
            if len(readable) > 0:
                new_data = readable[0].recv(1024)
                if new_data:
                    self.data = self.data + new_data
                else:
                    sys.exit(0)

            # GOOD GAME?
            m = re.search("(?<=\[GG\|)[a-zA-Z0-9_]+", self.data)
            if m:
                self.data = re.sub("\[GG\|[a-zA-Z0-9_]+\]", "", self.data)
                print "PLAYER %s WON!" % m.group(0)
                break

            # NEW GAME?
            m = re.search("(?<=\[STARTGAME\|)([a-zA-Z0-9_]+\,?)*", self.data)
            if m:
                self.playerList = m.group(0).split(",")
                self.data = re.sub("\[STARTGAME\|([a-zA-Z0-9_]+\,?)*\]", "", self.data)
                print "STARTING A GAME WITH %s" % self.playerList
                #break

            m = re.search("(?<=\[PLAYERS\|)([a-zA-Z0-9]+\,?)+", self.data)
            if m:
                self.playerList = m.group(0).split(",")
                self.data = re.sub("\[PLAYERS\|([a-zA-Z0-9_]+\,?)+\]", "", self.data)

            if self.data != "":
                print self.data

            # HAVE I BEEN DEALT?
            m = re.search("(?<=\[DEAL\|)([A-Z0-9]+\,?)+", self.data)
            if m:
                newCards = m.group(0).split(",")
                self.myCards = self.myCards + newCards
                print "MY CARDS ARE %s, newCards are %s" % (self.myCards, newCards)
                self.data = re.sub("\[DEAL\|([A-Z0-9]+\,?)+\]", "", self.data)

            # Did someone play a card?
            m = re.search("(?<=\[PLAYED\|)[a-zA-Z0-9_]+,[A-Z0-9]+", self.data)
            while m:
                playerName, cardToRemove = m.group(0).split(",")
                if playerName == self.username and cardToRemove != "NN":
                    if cardToRemove[1] == "F" or cardToRemove[1] == "W":
                        cardToRemove = "N" + cardToRemove[1]

                print "%s played card %s" % (playerName, cardToRemove)
                self.data = re.sub("\[PLAYED\|[a-zA-Z0-9_]+,[A-Z0-9]+\]", "", self.data)
                m = re.search("(?<=\[PLAYED\|)[a-zA-Z0-9_]+,[A-Z0-9]+", self.data)

            # IS IT A TURN?
            m = re.search("(?<=\[GO\|)[A-Z0-9]+", self.data)
            if m:
                topCard = m.group(0)
                self.data = re.sub("\[GO\|[A-Z0-9]+\]", "", self.data)
                #print "MY TURN!!!!", topCard, self.data
                self.makeTurn(topCard)

            # UNO?
            m = re.search("(?<=\[UNO\|)[a-zA-Z0-9_]+", self.data)
            if m:
                winner = m.group(0)
                print "WINNER %s" % winner
                self.data = re.sub("\[UNO\|[a-zA-Z0-9_]+\]", "", self.data)


            # Have I made an invalid command?
            m = re.search("(?<=\[INVALID\|)[^\]]+", self.data)
            if m:
                self.data = re.sub("\[INVALID\|[^\]]+\]", "", self.data)

            #self.data = self.data + self.s.recv(1024)
            #time.sleep(3)

    def run(self):
        serverAddress = (self.hostname, self.port)
        self.s.connect(serverAddress)
        self.waitInLobby()
        while True:
            self.waitForGame()
            self.playGame()
            #self.data = ""


class Manual_Client():
    def __init__(self, hostname, port, username):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        serverAddress = (self.hostname, self.port)
        self.s.connect(serverAddress)
        self.data = ""
        self.myCards = []

        while True:
            readable , writable, exceptional = select.select([self.s], [], [], 1)
            if len(readable) > 0:
                new_data = readable[0].recv(1024)
                if new_data:
                    self.data = self.data + new_data
                else:
                    sys.exit(0)

            # GOOD GAME?
            m = re.search("(?<=\[GG\|)[a-zA-Z0-9_]+", self.data)
            if m:
                self.data = re.sub("\[GG\|[a-zA-Z0-9_]+\]", "", self.data)
                print "PLAYER %s WON!" % m.group(0)

            # NEW GAME?
            m = re.search("(?<=\[STARTGAME\|)([a-zA-Z0-9_]+\,?)*", self.data)
            if m:
                self.playerList = m.group(0).split(",")
                self.data = re.sub("\[STARTGAME\|([a-zA-Z0-9_]+\,?)*\]", "", self.data)
                print "STARTING A GAME WITH %s" % self.playerList
                #break

            m = re.search("(?<=\[PLAYERS\|)([a-zA-Z0-9]+\,?)+", self.data)
            if m:
                self.playerList = m.group(0).split(",")
                self.data = re.sub("\[PLAYERS\|([a-zA-Z0-9_]+\,?)+\]", "", self.data)

            # HAVE I BEEN DEALT?
            m = re.search("(?<=\[DEAL\|)([A-Z0-9]+\,?)+", self.data)
            if m:
                newCards = m.group(0).split(",")
                self.myCards = self.myCards + newCards
                print "MY CARDS ARE %s, newCards are %s" % (self.myCards, newCards)
                self.data = re.sub("\[DEAL\|([A-Z0-9]+\,?)+\]", "", self.data)

            # Did someone play a card?
            m = re.search("(?<=\[PLAYED\|)[a-zA-Z0-9_]+,[A-Z0-9]+", self.data)
            while m:
                playerName, cardToRemove = m.group(0).split(",")
                if playerName == self.username and cardToRemove != "NN":
                    if cardToRemove[1] == "F" or cardToRemove[1] == "W":
                        cardToRemove = "N" + cardToRemove[1]

                print "%s played card %s" % (playerName, cardToRemove)
                self.data = re.sub("\[PLAYED\|[a-zA-Z0-9_]+,[A-Z0-9]+\]", "", self.data)
                m = re.search("(?<=\[PLAYED\|)[a-zA-Z0-9_]+,[A-Z0-9]+", self.data)

            # IS IT A TURN?
            m = re.search("(?<=\[GO\|)[A-Z0-9]+", self.data)
            if m:
                topCard = m.group(0)
                self.data = re.sub("\[GO\|[A-Z0-9]+\]", "", self.data)
                #print "MY TURN!!!!", topCard, self.data
                self.makeTurn(topCard)

            # UNO?
            m = re.search("(?<=\[UNO\|)[a-zA-Z0-9_]+", self.data)
            if m:
                winner = m.group(0)
                self.data = re.sub("\[UNO\|[a-zA-Z0-9_]+\]", "", self.data)


if __name__ == "__main__":
    #parser = OptionParser()
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-p",
                      "--port",
                      dest="port",
                      help="which port to use",
                      type="int",
                      metavar="NUMBER",
                      default=36741)

    parser.add_option("-h", "--host",
                      dest="hostname",
                      help="hostname to connect to",
                      type="string",
                      metavar="STRING",
                      default=socket.gethostname())

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
