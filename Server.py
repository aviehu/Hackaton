
from socket import *
import struct
import time
import threading
import random
import scapy.all

#Constants
TIME_TO_WAIT = 10
BUFFER_LEN = 1024
PORT = 13117
UDP_IP = '172.99.255.255'

class Server:

    def __init__(self):
        self.thisIp = scapy.all.get_if_addr('eth2')
        print(self.thisIp)
        self.udpPort = PORT
        print("Server started, listening on IP address {}".format(self.thisIp))
        self.waitingOnClients()

    def setTcpSocket(self):
        self.tcpSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
        self.tcpSocket.bind((UDP_IP, 0))

    def setUdpSocket(self):
        self.udpSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    """
        Description:
            waiting for clients to connect
    """
    def waitingOnClients(self):
        #Set connections
        self.setTcpSocket()
        self.setUdpSocket()

        #Start broadcast
        broadcast = UdpBroadcast(self.udpSocket, self.tcpSocket.getsockname()[1], self.thisIp, self.udpPort)
        broadcast.start()
        self.tcpSocket.listen(2)
        teamName_1 = ""
        teamName_2 = ""

        #Connect and get first team name
        (client1, addr1) = self.tcpSocket.accept()
        while(len(teamName_1) < 1):
            if not teamName_1: teamName_1 = client1.recv(BUFFER_LEN).decode()
        print('{} has joined the match'.format(teamName_1))

        #Connect and get second team name
        (client2, addr2) = self.tcpSocket.accept()
        while(len(teamName_2) < 1):
            if not teamName_2: teamName_2 = client2.recv(BUFFER_LEN).decode()
        print('{} has joined the match'.format(teamName_2))
        client1.setblocking(0)
        client2.setblocking(0)
        broadcast.endBroadcast()
        broadcast.join()
        self.game(client1, client2, teamName_1, teamName_2)
    
    """
        Description:
            Run game between client1 and client2

        Params:
            client1 - first team socket
            client2 - second team socket
            teamName_1 - first team name
            teamName_2  - second team name
    """
    def game(self, client1, client2, teamName_1, teamName_2):
        time.sleep(TIME_TO_WAIT)
        (ans, toPrint) = self.getRandomQuestion()
        welcomeMsg = 'Welcome to Quick Maths.\nPlayer 1: {}\nPlayer 2: {}\nPlease answer the following question as fast as you can:\n{}'.format(teamName_1, teamName_2, toPrint)
        client1.send(welcomeMsg.encode())
        client2.send(welcomeMsg.encode())
        listener1 = TcpListener(client1, ans, teamName_1, teamName_2)
        listener2 = TcpListener(client2, ans, teamName_2, teamName_1)
        listener1.setOther(listener2)
        listener2.setOther(listener1)
        stopper = TcpStopper(listener1, listener2)
        listener1.start()
        listener2.start()
        stopper.start()
        listener1.join()
        listener2.join()
        self.tcpSocket.close()
        print("Game over, sending out offer requests...")
        self.waitingOnClients()

    def getRandomQuestion(self):
        num1 = random.randint(1,5)
        num2 = random.randint(1,4)
        toPrint = '{} + {}'.format(num1, num2)
        return (num1 + num2, toPrint)

class UdpBroadcast(threading.Thread):
    def __init__(self, udpSocket, tcpPort, thisIp, udpPort):
        threading.Thread.__init__(self)
        self.udpSocket = udpSocket
        self.tcpPort = tcpPort
        self.udpPort = udpPort
        self.thisIp = thisIp
        self.allConnected = False
        self.end = False

    def run(self):
        while(not self.end):
            time.sleep(1)
            try:
                self.udpSocket.sendto(self.getUdpMessage(), (UDP_IP, self.udpPort))
            except Exception as err:
                print(err)


    def getUdpMessage(self):
        magicCookie = 0xabcddcba
        messageType = 0x2
        serverPort = self.tcpPort
        print(serverPort)
        return struct.pack('IbH', magicCookie, messageType, serverPort)

    def endBroadcast(self):
        self.end = True

class TcpStopper(threading.Thread):
    def __init__(self, thread1, thread2):
        threading.Thread.__init__(self)
        self.t1 = thread1
        self.t2 = thread2
    
    def run(self):
        time.sleep(TIME_TO_WAIT)
        if(self.t1.is_alive()): self.t1.finishListening()
        if(self.t2.is_alive()): self.t2.finishListening()

class TcpListener(threading.Thread):
    def __init__(self, client, ans, teamName, otherTeamName):
        threading.Thread.__init__(self)
        self.client = client
        self.teamName = teamName
        self.otherTeamName = otherTeamName
        self.otherThread = None
        self.ans = ans
        self.done = False
        self.winner = None

    def run(self):
        while (not self.done):
            try:
                clientAns = self.client.recv(BUFFER_LEN).decode()
                if (clientAns):
                    self.done = True
                    self.otherThread.finishListening()
                    if int(clientAns) == self.ans:
                        self.winner = self.teamName
                        self.otherThread.setWinner(self.teamName)
                    else:
                        self.winner = self.otherTeamName
                        self.otherThread.setWinner(self.otherTeamName)

            except Exception as err:
                time.sleep(0.1)
        try:
            if(self.winner):
                self.client.send('Game over!\nThe correct answer was {}\nCongratulations to the winner: {}'.format(self.ans, self.winner).encode())
            else:
                self.client.send('Game over!\nIts a draw :(\nThe correct answer was {}\n'.format(self.ans).encode())
        except Exception as err:
            print('A player has disconnected, the game is over')

    def finishListening(self):
        self.done = True
    
    def setWinner(self, winner):
        self.winner = winner

    def setOther(self, ot):
        self.otherThread = ot

Server()
