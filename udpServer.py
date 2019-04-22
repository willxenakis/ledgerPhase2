import socket
import time
import sys
import json
import threading
from flask import request
from random import randint
from SimpleCoinComplete import Wallet
import rsa
import util

ledger = list()
creatorKey = open("Apublic.key" , "r").read()
creatorPrivKey = open("Aprivate.key" , "r").read()
nonce = str(randint(0,2000))
encryptedNonce = rsa.encryptMessage(creatorPrivKey, nonce)

class Udp(object):
    def __init__(self, ledgers):
        ledger = ledgers
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server2.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.server2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server.bind(("", 5001))
        self.server2.bind(("", 5002))

    def runUdpBroadcaster(self):
        tosend = dict()
        tosend['coin']= "simplecoin"
        tosendJson = json.dumps(tosend)
        message = tosendJson.encode()
        while True:
            self.server2.sendto(message, ('<broadcast>', 5001))
            print("message sent!")
            time.sleep(5)

    def runUdpReceiver(self):
        while True:
            data, addr = self.server.recvfrom(1024)
            dataJson = json.loads(data)
            if(dataJson["coin"]=="simplecoin"):
                # address = "http://" + addr[0] + ":"+ str(addr[1])
                # Address of ledger on other client should be on port 8001
                address = "http://" + addr[0] + ":"+ str(8001)
                tosend = dict()
                tosend['ip']= socket.gethostbyname(socket.gethostname())
                tosend['encryptedNonce']=encryptedNonce
                tosend['wallet']=Wallet("new Name", creatorKey, "")

                # At this point I have sent a  post request and am saving the response which is a list of all known peers and 
                # an ecrypted nonce, and a public key
                r = request.post(url = address+"/peers", data = tosend)

                postResponse = r.getresponse()

                if(postResponse.text == ""):
                    print("already registered with other peer")
                else:
                    postData = postResponse.read()
                    alldata = JSON.parse(postData)
                    encryptedNonced = alldata['encryptedNonce']
                    publicKey = alldata['publicKey']
                    decryptedNonced = rsa.decryptMessage(publicKey, encryptedNonced)
                    if(decryptedNonced == nonce):
                        currPeerList = ledger.getPeerList()
                        newPostPeers = alldata['peerList']
                        util.joinPeerLists(newPostPeers, currPeerList)
                    


    def runSameTime(self):
        client = threading.Thread(target=self.runUdpBroadcaster)
        server = threading.Thread(target=self.runUdpReceiver)
        client.start()
        server.start()
        client.join()
        server.join()