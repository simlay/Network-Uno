#!/usr/bin/python

import socket
import sys
from optparse import OptionParser
import select
import re
import time


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

    def sendPlayerList(self):
        for connection in self.playerList:
            message = "[players|"
            for playerName in self.playerList.values():
                message = message + "," + playerName
            message = message + "]"
            connection.send(message)

    def startGame(self):
        print "STARTING A GAME WITH %s" % self.playerList.values()

    def lobby(self):
        # Get some sockets!
        server = self.server

        inputs = [ server ]
        self.playerList = {}
        outputs = [ ]

        # For unique names.
        nameCount = 0

        # For the countDown.
        countDownTime = int(time.time())

        while int(time.time()) - countDownTime < self.lobbyTime\
              or len(self.playerList) < self.minPlayers:

            sys.stderr.write("\r %s %s" % (countDownTime, int(time.time())))
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
                    data = s.recv(1024)
                    if data:
                        m = re.search("(?<=\[join\|)[a-zA-Z0-9_]+", data)
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
                                s.send("[accept|%s]" % playerName)

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

        # Send the player list just as exiting the lobby.
        self.sendPlayerList()


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
