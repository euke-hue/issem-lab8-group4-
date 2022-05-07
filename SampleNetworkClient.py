import matplotlib.pyplot as plt
import matplotlib.animation as animation
from Incubator import infinc
import time
import math
import socket
import fcntl
import os
import errno
import random
import string
import rsa 

class SimpleNetworkClient :
    def __init__(self, port1, port2):#add in the second port after
        self.fig, self.ax = plt.subplots()
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now-i)) for i in range(30, 0, -1)]
        self.infTemps = [0]*30
        self.incTemps = [0]*30
        self.infLn, = plt.plot(range(30), self.infTemps, label="Infant Temperature")
        self.incLn, = plt.plot(range(30), self.incTemps, label="Incubator Temperature")
        plt.xticks(range(30), self.times, rotation=45)
        plt.ylim((20,50))
        plt.legend(handles=[self.infLn, self.incLn])
        self.infPort = port1
        self.incPort = port2

        self.infToken = None
        self.incToken = None

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

    def updateTime(self) :
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime) :
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            #last 30 seconds of of data
            self.times = self.times[-30:]
            self.lastTime = now
            plt.xticks(range(30), self.times,rotation = 45)
            plt.title(time.strftime("%A, %Y-%m-%d", time.localtime(now)))

    def getTemperatureFromPort(self, p, tok) :
        #s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        #s.sendto(b"%s;GET_TEMP" % tok, ("127.0.0.1", p))
        #msg, addr = s.recvfrom(1024)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", p))
            byte_req = bytes("%s;GET_TEMP" % tok, 'utf-8')            
            s.sendall(byte_req)
            msg = s.recv(4096)
            print(f"Received {msg!r}")
            m = msg.decode("utf-8").strip("\n")
            print(m)
            return (float(m))

    def authenticate(self, p, pw) :
        # s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # s.sendto(b"AUTH %s" % pw, ("127.0.0.1", p))
        # msg, addr = s.recvfrom(1024)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", p))
            byte_req = bytes("AUTH %s" % pw, 'utf-8')            
            s.sendall(byte_req)
            msg = s.recv(4096)
            print(f"Received {msg!r}")
            m = msg.decode("utf-8")
            return m
    def updateInfTemp(self, frame) :
        self.updateTime()
        if self.infToken is None : #not yet authenticated
            self.infToken = self.authenticate(self.infPort, "!Q#E%T&U8i6y4r2w")

        self.infTemps.append(self.getTemperatureFromPort(self.infPort, self.infToken)-273)
        #self.infTemps.append(self.infTemps[-1] + 1)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame) :
        self.updateTime()
        if self.incToken is None : #not yet authenticated
            self.incToken = self.authenticate(self.incPort, "!Q#E%T&U8i6y4r2w")

        self.incTemps.append(self.getTemperatureFromPort(self.incPort, self.incToken)-273)
        #self.incTemps.append(self.incTemps[-1] + 1)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

snc = SimpleNetworkClient(23456, 23457)

plt.grid()
plt.show()