import threading
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


class SmartNetworkThermometer(threading.Thread):
    open_cmds = ["AUTH", "LOGOUT"]
    prot_cmds = ["SET_DEGF", "SET_DEGC", "SET_DEGK", "GET_TEMP", "UPDATE_TEMP"]

    def __init__(self, source, updatePeriod, port):
        threading.Thread.__init__(self, daemon=True)
        # set daemon to be true, so it doesn't block program from exiting
        self.source = source
        self.updatePeriod = updatePeriod
        self.curTemperature = 0
        self.updateTemperature()
        self.tokens = []
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind(("127.0.0.1", port))
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # fcntl.fcntl(self.serverSocket, fcntl.F_SETFL, os.O_NONBLOCK)

        self.deg = "K"

    def setSource(self, source):
        self.source = source

    def setUpdatePeriod(self, updatePeriod):
        self.updatePeriod = updatePeriod

    def setDegreeUnit(self, s):
        self.deg = s
        if self.deg not in ["F", "K", "C"]:
            self.deg = "K"

    def updateTemperature(self):
        self.curTemperature = self.source.getTemperature()

    def getTemperature(self):
        if self.deg == "C":
            return self.curTemperature - 273
        if self.deg == "F":
            return (self.curTemperature - 273) * 9 / 5 + 32
    #print(self.curTemperature)  
        return self.curTemperature

    def processCommands(self, msg):  # removed addr because TCP
         cmds = msg.split(';')
        for c in cmds:
            cs = c.split(' ')
            if len(cs) == 2:  # should be either AUTH or LOGOUT
                if cs[0] == "AUTH":
                    if cs[1] == "!Q#E%T&U8i6y4r2w":
                        # probably better to return the token as a result of the function
                        self.tokens.append(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)))
                        # updated processCommands to return the last token just added
                        return self.tokens[-1]
                        # print (self.tokens[-1])
                elif cs[0] == "LOGOUT":
                    if cs[1] in self.tokens:
                        self.tokens.remove(cs[1])
                        # if they asked for logout, return a 0
                        return "0"
                else:  # unknown command and since this is UDP implement TCP
                    # self.serverSocket.sendto(b"Invalid Command\n", addr)
                    # have processCommands return a string instead of sending directly
                    return "Invalid Command\n"
            elif c == "SET_DEGF":
                self.deg = "F"
            elif c == "SET_DEGC":
                self.deg = "C"
            elif c == "SET_DEGK":
                self.deg = "K"
            elif c == "GET_TEMP":
                # self.serverSocket.sendto(b"%f\n" % self.getTemperature(), addr)
                # have processCommands return a string instead of sending directly
                return str("%f\n" % self.getTemperature())
            elif c == "UPDATE_TEMP":
                self.updateTemperature()
            elif c:
                # self.serverSocket.sendto(b"Invalid Command\n", addr)
                # have processCommands return a string instead of sending directly
                return "Invalid Command\n"



    def run(self):  # the running function
        while True:
            #updated the areas where there would be a UDP send() to a TCP sendall() within the existing TCP connection
            self.serverSocket.listen(10)
            conn, addr = self.serverSocket.accept()
            with conn:
                data = conn.recv(2048)
                if data:
                    msg = data.decode("utf-8").strip()
                    cmds = msg.split(' ')
                    print(data)
                    if len(cmds) == 1:  # protected commands case
                        semi = msg.find(';')
                        if semi != -1:  # if we found the semicolon
                            # print (msg)
                            if msg[:semi] in self.tokens:  # if its a valid token
                                
                                response = self.processCommands(msg[semi + 1:])
                                byte_response = bytes(response, 'utf-8')
                                print("NETWORK SERVER: Sending temp %d", byte_response)
                                conn.sendall(byte_response)
                            else:
                                response = "Bad Token\n"
                                byte_response = bytes(response, 'utf-8')
                                conn.sendall(byte_response)
                                
                        else:
                            response = "Bad Command\n"
                            byte_response = bytes(response, 'utf-8')
                            conn.sendall(byte_response)
                            
                    elif len(cmds) == 2:
                        if cmds[0] in self.open_cmds:  # if its AUTH or LOGOUT
                            response = str(self.processCommands(msg))
                            if response != 0:
                                byte_response = bytes(response, 'utf-8')
                                print("NETWORK SERVER: Sending Token %d", byte_response)
                                conn.sendall(byte_response)
                                
                            else:
                                fin_message = b"Logged Out Successfully\n"
                                conn.sendall(fin_message)
                                
                               
                        else:
                            response = b"Authenticate First\n"
                            conn.sendall(response)
                            # self.serverSocket1.sendto(b"Authenticate First\n", addr)

                    else:
                        # otherwise bad command
                        response = b"Bad Command\n"
                        conn.sendall(response)
                  
            
            self.updateTemperature()
            time.sleep(self.updatePeriod)


class SimpleClient:
    def __init__(self, therm1, therm2):
        self.fig, self.ax = plt.subplots()
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now - i)) for i in range(30, 0, -1)]
        self.infTemps = [0] * 30
        self.incTemps = [0] * 30
        self.infLn, = plt.plot(range(30), self.infTemps, label="Infant Temperature")
        self.incLn, = plt.plot(range(30), self.incTemps, label="Incubator Temperature")
        plt.xticks(range(30), self.times, rotation=45)
        plt.ylim((20, 50))
        plt.legend(handles=[self.infLn, self.incLn])
        self.infTherm = therm1
        self.incTherm = therm2

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

    def updateTime(self):
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime):
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            # last 30 seconds of of data
            self.times = self.times[-30:]
            self.lastTime = now
            plt.xticks(range(30), self.times, rotation=45)
            plt.title(time.strftime("%A, %Y-%m-%d", time.localtime(now)))

    def updateInfTemp(self, frame):
        self.updateTime()
        self.infTemps.append(self.infTherm.getTemperature() - 273)
        # self.infTemps.append(self.infTemps[-1] + 1)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame):
        self.updateTime()
        self.incTemps.append(self.incTherm.getTemperature() - 273)
        # self.incTemps.append(self.incTemps[-1] + 1)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

