import socket
import select
import struct
import sys
import scapy.all

BUFFER_SIZE = 1024
PORT = 13117
UDP_IP = '172.99.255.255'

class Client:
    def __init__(self):
        self.teamName = 'Team Josh'
        self.udpSocket = None
        self.tcpSocket = None
        self.udpIp = scapy.all.get_if_addr('eth1')
        self.udpPort = PORT
        print('Client started, listening for offer requests...')
        self.lookingForServer()

    def setUdpSocket(self):
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udpSocket.bind((UDP_IP, self.udpPort))

    
    def lookingForServer(self):
        self.setUdpSocket()
        try:
            data, addr = self.udpSocket.recvfrom(BUFFER_SIZE)
            print('Received offer from {}, attempting to connect...'.format(addr[0]))
        except Exception as err:
            print(err)
        self.udpSocket.close()
        self.checkAndConnect(data)

    def checkAndConnect(self,data):
        unPacked = struct.unpack('IbH', data)
        magicCookie = 0xABCDDCBA
        messageType = 0x2
        if unPacked[0] == magicCookie and unPacked[1] == messageType:
            try:
                currPort = unPacked[2]
                self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcpSocket.connect((self.udpIp, currPort))
                self.startGame()
            except Exception:
                self.lookingForServer()
        else:
            self.lookingForServer()
    
    def startGame(self):

        self.tcpSocket.send(self.teamName.encode())
        print(self.tcpSocket.recv(BUFFER_SIZE).decode())
        try:
            reads, _, _ = select.select([sys.stdin, self.tcpSocket], [], [], 10)
            if(sys.stdin in reads):
                userAns = sys.stdin.read(1)
                self.tcpSocket.send(userAns.encode())
        except Exception as err:
            self.tcpSocket.close()
            self.lookingForServer()
        print(self.tcpSocket.recv(BUFFER_SIZE).decode())
        self.tcpSocket.close()
        print('Server disconnected, listening for offer requests...')
        self.lookingForServer()
 
        
Client()