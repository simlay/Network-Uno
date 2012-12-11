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
                "RU", "RU",

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
                "BU", "BU",

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
                "YU", "YU",

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
                "GU", "GU",

                "NW", "NW", "NW", "NW",
                "NF", "NF", "NF", "NF",
                ]

class Server():
    def __init__(self, port, timeout, minPlayers, maxPlayers, maxLobby):
        self.port = port
        self.timeout = timeout
        self.minPlayers = minPlayers
        self.maxPlayers = maxPlayers
        self.maxLobby = maxLobby
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(0)

        serverAddress = (socket.gethostname(), self.port)

        self.server.bind(serverAddress)
        self.server.listen(5)
        sys.stderr.write("Starting up server on %s with port %s\n" % serverAddress)

    def broadcast(self, message):
        print "BROADCAST: %s" % message
        for connection in self.playerList:
            try:
                connection.send(message)
            except:
                if connection in self.playerList:
                    print "Connection %s, %s probably closed" % (connection, self.playerList[connection])
                else:
                    print "Connection %s probably closed" % connection

    def sendPlayerList(self):
        message = "[PLAYERS|"
        for playerName in self.lobby_clients.values():
            message = message + playerName + ","
        message = message[:-1] + "]"
        self.broadcast(message)

    def sendStartList(self):
        message = "[STARTGAME|"
        for playerName in self.playerList.values():
            message = message + playerName + ","
        message = message[:-1] + "]"
        #print "SENDING STARTLIST", message
        self.broadcast(message)

    def dealCards(self):
        self.playerCards = {}

        self.cardStack = [x for x in cardList]
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
            try:
                connection.send(message)
            except:
                print "Connection %s probably closed" % connection

    def validateCard(self, testCard):
        topCard = self.discardPile[-1]
        if topCard[0] == testCard[0] or testCard[1] == "W" or testCard[1] == "F" or topCard[1] == testCard[1]:
            return True
        else:
            return False

    def playGame(self):
        print "PLAYING GAME"
        self.playerOrder = self.playerList.values()
        #time.sleep(1)

        # Lets get the dictionary of player names to connections.
        self.connectionDictionary = {}
        for connection in self.playerList:
            self.connectionDictionary[self.playerList[connection]] = connection
        playerIndex = 0
        playDirection = 1
        data = ""
        inputs = self.connectionDictionary.values() + [self.server]
        data_buffer = {}

        already_played_NN = False

        played = False
        sent_go = False

        while len(self.playerList) > 1:
            playerIndex = playerIndex % len(self.playerOrder)
            #if data != "":
            #    print data

            playerName = self.playerOrder[playerIndex]
            connection = self.connectionDictionary[playerName]

            #print "TURN:", playerIndex, playerName

            #print "Player %s turn, top card %s" % (playerName, self.discardPile[-1])
            try:
                if not sent_go:
                    message = "[GO|%s]" % self.discardPile[-1]
                    print "%s -> %s" % (playerName, message)
                    connection.send(message)
                    sent_go = True
            except:
                if connection in self.playerList:
                    print "SENDING GO FAILD: Connection %s probably closed" % (self.playerList[connection])
                    playerIndex = (playerIndex + playDirection) % len(self.playerList)
                else:
                    playerIndex = (playerIndex + playDirection) % len(self.playerList)
                    print "Connection %s probably closed, players %s remain" % (connection, self.playerOrder)

            readable, writable, exceptional = select.select(inputs, [], [], 1)
            for s in readable:
                # A new connection?
                if s == self.server:
                    client, address = self.server.accept()
                    inputs.append(client)
                    print "NEW CONNECTION FROM",  address, client
                else:
                    try:
                        new_data = s.recv(1024)
                    except:
                        new_data = None
                    # Readable data.
                    if new_data:
                        data = data + new_data
                        if s in data_buffer:
                            data_buffer[s] = data_buffer[s] + new_data
                        else:
                            data_buffer[s] = new_data

                        if s not in self.playerList and s not in self.lobby_clients:
                            m = re.search("(?<=\[JOIN\|)[a-zA-Z0-9_]+", new_data)
                            #print new_data
                            if m:
                                newPlayerName = m.group(0)
                                if newPlayerName in self.playerList.values():
                                    newPlayerName = newPlayerName + str(self.nameCount)
                                    self.nameCount += 1
                                print "Player %s was added to lobby!" % newPlayerName
                                message = "[WAIT|%s]" % newPlayerName
                                s.send(message)
                                self.lobby_clients[s] = newPlayerName

                            m = re.search("(?<=\[CHAT\|)[[^\]]+", data)
                            if m:
                                chatMessage = m.group(0)
                                message = "[CHAT|%s]" % chatMessage
                                self.broadcast(message)

                    # Connection has closed.
                    else:
                        inputs.remove(s)

                        if s in self.lobby_clients:
                            del self.lobby_clients[s]

                        if s in self.playerList:
                            print "CONNECTION %s DROPPED" % (self.playerList[s])
                            playerName = self.playerList[s]

                            del self.playerList[s]

                            if playerName in self.connectionDictionary:
                                del self.connectionDictionary[playerName]

                            if playerName in self.playerOrder:
                                self.playerOrder.remove(playerName)

                            if s in inputs:
                                inputs.remove(s)

                            message = "[PLAYERS|"
                            for i in self.playerOrder:
                                message = message + i + ","
                            message = message[:-1] + "]"
                            print "BROADCAST: %s" % message
                            self.broadcast(message)

                        else:
                            print "CONNECTION %s DROPPED" % s

                        if s in self.lobby_clients:
                            del self.lobby_clients[s]


            m = re.search("(?<=\[CHAT\|)[[^\]]+", data)
            if m:
                chatMessage = m.group(0)
                message = "[CHAT|%s]" % chatMessage
                self.broadcast(message)
            try:
                m = re.search("(?<=\[PLAY\|)[A-Z0-9]+", data_buffer[connection])
            except:
                m = None

            if m:
                sent_go = False
                card = m.group(0)
                #print playerName, message, card, self.playerCards[playerName], self.discardPile
                if self.validateCard(card):
                    #print "%s played %s" % (playerName, card)
                    self.discardPile.append(card)

                    message = "[PLAYED|%s,%s]" % (playerName, card)
                    print message

                    self.broadcast(message)
                    if card != "NN":
                        removeCard = card
                        if card[1] == "F" or card[1] == "W":
                            removeCard = "N" + card[1]

                        if removeCard in self.playerCards[playerName]:
                            self.playerCards[playerName].remove(removeCard)
                        else:
                            None
                            #connection.send("[INVALID|YOU DON'T HAVE %s!]" % card)
                            #connection.send("[GO|%s]" % self.discardPile[-1])

                    if len(self.playerCards[playerName]) == 0:
                        self.broadcast("[GG|%s]" % playerName)
                        break

                    # Implement the game rules!
                    # SKIP
                    if card[1] == "S":
                        #print "SKIP INDEX BEFORE: %s AFTER: %s" % (playerIndex, (playerIndex + 2*playDirection) % len(self.playerOrder))
                        playerIndex = (playerIndex + 2*playDirection) % len(self.playerOrder)

                    # REVERSE
                    elif card[1] == "U":
                        #print "REVERSE BEFORE %s AFTER %s" %(playerIndex, (playerIndex - playDirection) % len(self.playerOrder))
                        playDirection = -playDirection
                        playerIndex = (playerIndex + playDirection) % len(self.playerOrder)
                        #print "PLAYER INDEX:", playerIndex

                    # DRAW 2
                    elif card[1] == "D":
                        #print "DRAW 2 BEFORE %s AFTER %s" % (playerIndex, (playerIndex + playDirection) % len(self.playerOrder))
                        playerIndex = (playerIndex + playDirection) % len(self.playerOrder)
                        cards = []
                        for i in xrange(2):
                            newCard = choice(self.cardStack)
                            cards.append(newCard)
                            self.cardStack.remove(newCard)

                        message = "[DEAL|%s,%s]" % (cards[0], cards[1])
                        send_to_player = self.playerOrder[playerIndex]

                        print "%s -> %s" % (send_to_player, message)

                        try:
                            playerIndex = (playerIndex + playDirection) % len(self.playerList)
                            self.connectionDictionary[send_to_player].send(message)
                        except:
                            playerIndex = (playerIndex + playDirection) % len(self.playerList)
                            print "Connection probably closed"

                    # Wild Draw 4
                    elif card[1] == "F":
                        #print "WILD DRAW 4 BEFORE %s AFTER %s" % (playerIndex, (playerIndex + playDirection) % len(self.playerOrder))
                        playerIndex = (playerIndex + playDirection) % len(self.playerOrder)
                        newCards = []
                        for i in xrange(4):
                            newCard = choice(self.cardStack)
                            newCards.append(newCard)
                            self.cardStack.remove(newCard)

                        send_to_player = self.playerOrder[playerIndex]
                        message = "[DEAL|%s,%s,%s,%s]" % (newCards[0], newCards[1], newCards[2], newCards[3])

                        print "%s -> %s" % (send_to_player, message)
                        try:
                            self.connectionDictionary[send_to_player].send(message)
                        except:
                            print "Connection probably closed."

                    else:
                        playerIndex = (playerIndex + playDirection) % len(self.playerList)
                    #played = False
                    already_played_NN = False

                elif card == "NN" and not already_played_NN:
                    if len(self.cardStack) == 0:
                        self.broadcast("[GG|%s]" % socket.gethostname())
                        return

                    newCard = choice(self.cardStack)
                    self.cardStack.remove(newCard)
                    self.playerCards[playerName].append(newCard)

                    message = "[DEAL|%s]" % newCard
                    print "%s -> %s" % (playerName, message)
                    try:
                        connection.send(message)
                    except:
                        if connection in self.playerList:
                            print "385: Connection %s, %s probably closed" % (connection, self.playerList[connection])
                            del self.playerList[connection]
                        else:
                            print "Connection %s probably closed" % connection

                    already_played_NN = True
                    #played = False

                # Still doesn't have a card to play.
                elif card == "NN" and already_played_NN:
                    playerIndex = (playerIndex + playDirection) % len(self.playerOrder)
                    already_played_NN = False
                    #played = True
                else:
                    message = "[INVALID|CARD NOT VALID]"
                    try:
                        connection.send(message)
                    except:
                        if connection in self.playerList:
                            print "Connection %s, %s probably closed" % (connection, self.playerList[connection])
                        else:
                            print "Connection %s probably closed" % connection

                try:

                    data_buffer[connection] = re.sub("\[PLAY\|[A-Z0-9]+\]", "", data_buffer[connection])
                except:
                    None

                #print self.discardPile, playerIndex
            if len(self.playerCards[playerName]) == 1:
                self.broadcast("[UNO|%s]" % playerName)

        if len(self.playerList) == 1:
            print self.playerList
            self.broadcast("[GG|%s]" % self.playerList.values()[0])

        self.playerList = self.lobby_clients

            #playerIndex = (playerIndex + 1) % len(self.playerOrder)
            #time.sleep(1)

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
        outputs = [ ]

        # For unique names.
        self.nameCount = 0

        # For the countDown.
        #countDownTime = int(time.time())
        countDownTime = 0
        data = ""

        self.data_buffer = {}

        print "LOBBY CLIENTS:", self.lobby_clients

        while (time != 0 and int(time.time()) - countDownTime < 5) or len(self.lobby_clients) < self.minPlayers:

            if len(self.lobby_clients) >= self.minPlayers:
                sys.stderr.write("\rStarting in %s" % (5 - (int(time.time()) - countDownTime)))

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
                    if s in self.data_buffer:
                        self.data_buffer[s] = self.data_buffer[s] + s.recv(1024)
                    else:
                        self.data_buffer[s] = s.recv(1024)

                    data = self.data_buffer[s]
                    if data:
                        m = re.search("(?<=\[JOIN\|)[a-zA-Z0-9_]+", data)
                        if m:
                            # Get the player name.
                            playerName = m.group(0)

                            # Game sure it's a unique name.
                            if playerName in self.lobby_clients.values():
                                playerName = playerName + str(self.nameCount)
                                self.nameCount += 1

                            if s not in self.lobby_clients:
                                self.lobby_clients[s] = playerName
                                print "Player %s was added!" % playerName
                                message = "[ACCEPT|%s]" % playerName
                                #print "sending message {%s}" % message

                                s.send(message)

                                # Send the player list just as exiting the lobby.
                                self.playerList = self.lobby_clients
                                self.sendPlayerList()

                                # Start off the counter!
                                if len(self.lobby_clients) >= self.minPlayers:
                                    if countDownTime == 0:
                                        countDownTime = int(time.time())
                                    print "STARTING THE TIMER!"

                        else:
                            print "recieved %s from %s" % ( data, s)

                        if s not in outputs:
                            outputs.append(s)

                    # Remove this element.
                    else:
                        if s in outputs:
                            outputs.remove(s)
                            inputs.remove(s)
                            self.lobby_clients.pop(s)
                            s.close()
                        print "REMOVING PLAYER"
                        del self.lobby_clients[s]
                        s.close()
        sys.stderr.write("\r")
        self.playerList = self.lobby_clients

    def run(self):
        self.lobby_clients = {}
        while True:
            self.lobby()
            self.startGame()


if __name__ == "__main__":
    parser = OptionParser(conflict_handler="resolve")
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
