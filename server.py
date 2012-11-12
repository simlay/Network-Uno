#!/usr/bin/python

import socket
import sys
from optparse import OptionParser
import select
import re
import time

from random import choice

cardList = [
                "R0",
                "R1", "R1",
                "R2", "R2",
                "R3", "R3",
                "R4", "R4",
                "R5", "R5",
                "R6", "R6",
                "R7", "R7",
                "R8", "R8",
                "R9", "R9",
                "RD", "RD",
                "RS", "RS",
                "RR", "RR",

                "B0",
                "B1", "B1",
                "B2", "B2",
                "B3", "B3",
                "B4", "B4",
                "B5", "B5",
                "B6", "B6",
                "B7", "B7",
                "B8", "B8",
                "B9", "B9",
                "BD", "BD",
                "BS", "BS",
                "BR", "BR",

                "Y0",
                "Y1", "Y1",
                "Y2", "Y2",
                "Y3", "Y3",
                "Y4", "Y4",
                "Y5", "Y5",
                "Y6", "Y6",
                "Y7", "Y7",
                "Y8", "Y8",
                "Y9", "Y9",
                "YD", "YD",
                "YS", "YS",
                "YR", "YR",

                "G0",
                "G1", "G1",
                "G2", "G2",
                "G3", "G3",
                "G4", "G4",
                "G5", "G5",
                "G6", "G6",
                "G7", "G7",
                "G8", "G8",
                "G9", "G9",
                "GD", "GD",
                "GS", "GS",
                "GR", "GR",

                "NW", "NW", "NW", "NW",
                "NF", "NF", "NF", "NF",
                ]

class Server():
    def __init__(self, port, time, minPlayers, maxPlayers, maxLobby):
        self.port = port
        self.lobbyTime = time
        self.minPlayers = minPlayers
        self.maxPlayers = maxPlayers
        self.maxLobby = maxLobby
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(0)

        serverAddress = ('localhost', self.port)

        self.server.bind(serverAddress)
        self.server.listen(5)
        sys.stderr.write("Starting up server on %s with port %s\n" % serverAddress)

    def broadcast(self, message):
        for connection in self.playerList:
            connection.send(message)

    def sendPlayerList(self):
        message = "[PLAYERS|"
        for playerName in self.playerList.values():
            message = message + playerName + ","
        message = message[:-1] + "]"
        self.broadcast(message)

    def sendStartList(self):
        message = "[START|"
        for playerName in self.playerList.values():
            message = message + playerName + ","
        message = message[:-1] + "]"
        self.broadcast(message)

    def dealCards(self):
        self.playerCards = {}

        self.cardStack = cardList
        for player in self.playerList.values():
            cards = []
            for i in xrange(7):
                newCard = choice(self.cardStack)
                cards.append(newCard)
                self.cardStack.remove(newCard)

            self.playerCards[player] = cards

        topCard = choice(self.cardStack)
        self.cardStack.remove(topCard)
        if topCard[0] == "N":
            topCard = choice(["G", "R", "Y", "B"]) + topCard[1]
        self.discardPile = [topCard]

        for connection in self.playerList:
            message = "[DEAL|"
            for card in self.playerCards[self.playerList[connection]]:
                message = message + card + ","
            message = message[:-1] + "]"
            connection.send(message)

    def validateCard(self, testCard):
        topCard = self.discardPile[-1]
        if topCard[0] == testCard[0] or testCard[1] == "W" or testCard[1] == "F" or topCard[1] == testCard[1]:
            return True
        else:
            return False

    def playGame(self):
        self.playerOrder = self.playerList.values()
        time.sleep(1)

        # Lets get the dictionary of player names to connections.
        self.connectionDictionary = {}
        for connection in self.playerList:
            self.connectionDictionary[self.playerList[connection]] = connection
        playerIndex = 0
        playDirection = 1
        data = ""
        while True:

            playerName = self.playerOrder[playerIndex]
            connection = self.connectionDictionary[playerName]

            message = "[GO|%s]" % self.discardPile[-1]
            connection.send(message)
            while True:
                try:
                    # Let's try to get some data.
                    data = data + connection.recv(1024)
                    break
                except:
                    None

            if data != "":
                print data

            m = re.search("(?<=\[PLAY\|)[A-Z0-9]+", data)
            if m:
                card = m.group(0)
                print playerName, message, card, self.playerCards[playerName], self.discardPile
                if self.validateCard(card):
                    self.discardPile.append(card)
                    playerIndex = (playerIndex + playDirection) % len(self.playerList)

                    message = "[PLAYED|%s,%s]" % (playerName, card)

                    self.broadcast(message)
                    if card != "NN":
                        if card[1] == "F" or card[1] == "W":
                            print "REMOVING CARD %s" % card
                            self.playerCards[playerName].remove("N" + card[1])
                        else:
                            self.playerCards[playerName].remove(card)

                    if len(self.playerCards[playerName]) == 0:
                        self.broadcast("[GG|%s]" % playerName)
                        break

                elif card == "NN":
                    newCard = choice(self.cardStack)
                    self.cardStack.remove(newCard)
                    self.playerCards[playerName].append(newCard)

                    message = "[DEAL|%s]" % newCard
                    connection.send(message)

                    message = "[GO|%s]" % self.discardPile[-1]
                    connection.send(message)
                else:
                    message = "[INVALID|CARD NOT VALID]"
                    connection.send(message)

                data = re.sub("\[PLAY\|[A-Z0-9]+\]", "", data)

                #print self.discardPile, playerIndex
            if len(self.playerCards[playerName]) == 1:
                self.broadcast("[UNO|%s]" % playerName)


            #playerIndex = (playerIndex + 1) % len(self.playerOrder)
            #time.sleep(1)
            time.sleep(1)

    def startGame(self):
        self.sendStartList()
        print "STARTING A GAME WITH %s" % self.playerList.values()

        # Do shuffling, and send cards.
        self.dealCards()

        # Lets play the game!
        self.playGame()

    def lobby(self):
        # Get some sockets!
        server = self.server
        #socket.setdefaulttimeout(0)

        inputs = [ server ]
        self.playerList = {}
        outputs = [ ]

        # For unique names.
        nameCount = 0

        # For the countDown.
        countDownTime = int(time.time())
        data = ""

        while int(time.time()) - countDownTime < self.lobbyTime or len(self.playerList) < self.minPlayers:

            if len(self.playerList) >= self.minPlayers:
                sys.stderr.write("\r%s" % (self.lobbyTime - (int(time.time()) - countDownTime)))

            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is server:
                    connection, clientAddress = s.accept()
                    print clientAddress
                    sys.stderr.write("New connection from %s, %s\n" % clientAddress)
                    connection.setblocking(0)

                    inputs.append(connection)
                    # Write player list to new connection.

                else:
                    data = data + s.recv(1024)
                    if data:
                        m = re.search("(?<=\[JOIN\|)[a-zA-Z0-9_]+", data)
                        if m:
                            # Get the player name.
                            playerName = m.group(0)

                            # Game sure it's a unique name.
                            if playerName in self.playerList.values():
                                playerName = playerName + str(nameCount)
                                nameCount += 1

                            if s not in self.playerList:
                                self.playerList[s] = playerName
                                print "Player %s was added!" % playerName
                                s.send("[ACCEPT|%s]" % playerName)

                                # Send the player list just as exiting the lobby.
                                self.sendPlayerList()

                                # Start off the counter!
                                if len(self.playerList) >= self.minPlayers:
                                    countDownTime = int(time.time())
                                    print "STARTING THE TIMER!"

                        else:
                            print "recieved %s from %s" % ( data, s)

                        if s not in outputs:
                            outputs.append(s)
                    else:
                        if s in outputs:
                            outputs.remove(s)
                            inputs.remove(s)
                            self.playerList.pop(s)
                            s.close()
        sys.stderr.write("\r")

    def run(self):
        self.lobby()
        self.startGame()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-p",
                      "--port",
                      dest="port",
                      help="which port to use",
                      type="int",
                      metavar="NUMBER",
                      default=36741)

    parser.add_option("-t",
                      "--time",
                      dest="timeout",
                      help="timeout for a player",
                      type="int",
                      metavar="NUMBER",
                      default=30)

    parser.add_option("--min",
                      dest="min",
                      help="Minimum number of players",
                      type="int",
                      metavar="NUMBER",
                      default=2)

    parser.add_option("--max",
                      dest="max",
                      help="Maximum number of players",
                      type="int",
                      metavar="NUMBER",
                      default=10)

    parser.add_option("--lobby",
                      dest="lobby",
                      help="Number of players which can be waiting in the lobby",
                      type="int",
                      metavar="NUMBER",
                      default=10)

    (options, args) = parser.parse_args()

    # Create server instance.
    server = Server(options.port,
                    options.timeout,
                    options.min,
                    options.max,
                    options.lobby)

    # Run that server!
    server.run()
