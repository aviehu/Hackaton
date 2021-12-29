import socket
import select
import sys
import scapy.all

class Client:
    def __init__(self):
        self.teamName = 'Team Josh'
        self.udpSocket = None
        self.tcpSocket = None
        self.udpIp = scapy.all.get_if_addr('eth1')
        self.udpPort = 13117
        print('Client started, listening for offer requests...')
        self.lookingForServer()

    def setUdpSocket(self):
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udpSocket.bind(('', self.udpPort))

    
    def lookingForServer(self):
        self.setUdpSocket()
        try:
            data, addr = self.udpSocket.recvfrom(1024)
            print('Received offer from {}, attempting to connect...'.format(addr[0]))
        except Exception as err:
            print(err)
        self.udpSocket.close()
        self.checkAndConnect(data)

    def checkAndConnect(self,data):
        magicCookie = bytes.fromhex('abcddcba')
        messageType = 2
        if str(magicCookie) == str(data[0:4]) and str(messageType) == str(data[4]):
            try:
                currPort = int.from_bytes(data[5:7], "big")
                self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcpSocket.connect((self.udpIp, currPort))
                self.startGame()
            except Exception:
                self.lookingForServer()
        else:
            self.lookingForServer()
    
    def startGame(self):

        self.tcpSocket.send(self.teamName.encode())
        print(self.tcpSocket.recv(1024).decode())
        try:
            reads, _, _ = select.select([sys.stdin, self.tcpSocket], [], [], 10)
            if(sys.stdin in reads):
                userAns = sys.stdin.read(1)
                self.tcpSocket.send(userAns.encode())
        except Exception as err:
            self.tcpSocket.close()
            self.lookingForServer()
        print(self.tcpSocket.recv(1024).decode())
        self.tcpSocket.close()
        print('Server disconnected, listening for offer requests...')
        self.lookingForServer()
        
        
Client()