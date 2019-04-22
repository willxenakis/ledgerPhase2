from flask import Flask
from flask import render_template
from flask import request
from SimpleCoinComplete import blockChain
from SimpleCoinComplete import Transaction
from SimpleCoinComplete import Wallet
from SimpleCoinComplete import ChainEncoder
import publicPrivateKey
import rsa
import hashlib
import json
import udpServer
import threading
from udpServer import Udp
import util

ledger = Flask(__name__)

creatorKey = open("Apublic.key" , "r").read()
creatorPrivKey = open("Aprivate.key" , "r").read()
creator = Wallet("Creator A", creatorKey, creatorPrivKey)
simpleCoin = blockChain(creator)

peerList = list()

def getPeerList(self):
    return peerList

class Peer(object):
    def __init__(self, address, wallet=None):
        self.address = address
        if wallet == None:
            temp = publicPrivateKey.publicPrivateDirectVals()
            self.wallet = Wallet("new User", temp[0], "")
        else:
            self.wallet = wallet

    def toJSON(self):
        tojson = {
            "__type__": self.__class__.__name__,
            "address": self.address,
            "public": self.wallet
        }
        return tojson

    

# All unspecified paths will return an error page
@ledger.route('/<path:path>')
def catchPath(path):
    return render_template('error.html'), 404

# This path shows the post with the given id, the id is an integer
# If the id is not an integer or a block is not found, an error page is returned
@ledger.route('/transactions/<id>')
def transaction(id):
    try:
        blockId = int(id)
        temp = simpleCoin.getHead()
        while temp!=None:
            if(temp.index == blockId):
                return render_template('singleBlock.html', blockId = blockId, block=temp,)
            else:
                temp = temp.nextBlock
    except:
        return render_template('error.html'), 404

    return render_template('error.html'), 404

# This path acts as both a path for Posting new transactions or getting all blocks and transactions starting at a given id
# For each transaction, verify the transaction and check no overspending then add the transaction to a verifiedTransactions list then mine the block
# For get, if start is not given return all blocks
@ledger.route('/transactions', methods=['GET', 'POST'])
def template():
    if request.method == 'POST':
        data = json.loads(request.get_data().decode('UTF-8'))
        transactionsArray = []

        for i in range(len(data['transactions'])):
            senderWallet = Wallet("DNE", data['transactions'][i]["senderPub"], "")
            receiverWallet = Wallet("IDK", data['transactions'][i]["receiverPub"], "")
            timeStamp = data['transactions'][i]["timeStamp"]
            operation = data['transactions'][i]["op"]
            _hash = data['transactions'][i]["hash"]

            newTransaction = Transaction(receiverWallet, operation, senderWallet, timeStamp, _hash)
            transactionsArray.append(newTransaction)

        verifiedTransactions = []

        for indexY, y in enumerate(transactionsArray):
            if simpleCoin.verifyTransaction(y) and simpleCoin.noOverspending(y.senderPub, verifiedTransactions, y):
                verifiedTransactions.append(y)
        if len(verifiedTransactions) !=0:
            simpleCoin.mineBlock(verifiedTransactions)
            latestBlock = simpleCoin.getLatestBlock()
            return ("Block Mined with " + str(len(verifiedTransactions)) + " transactions\nStatus Okay \n")
        return "Block Unable to be Mined"
    else:
        start = request.args.get('start')
        try:
            if(start != None):
                start = int(start)

                if(start<0):
                    return render_template('error.html'), 404

                temp = simpleCoin.getHead()
                blocks = []
                while temp!=None:
                    if(temp.index >= start):
                        blocks.append(temp)
                    temp = temp.nextBlock  
                if(len(blocks)==0):
                    return render_template('error.html'), 404
                return render_template('startBlock.html', start = start, blocks=blocks,)
            else:
                temp = simpleCoin.getHead()
                blocks = []
                while temp!=None:
                    blocks.append(temp)
                    temp = temp.nextBlock
                return render_template('startBlock.html', start = 0, blocks=blocks,)
        except:
            return render_template('error.html'), 404

# POST - registers a new peer; Data sent is the client ledger's public key, a nonce, and the client's IP address 
# all encrypted by the client's private key; If validated and actually new, the server's response should be all known 
# peers (with IPs and public keys) PLUS the nonce all encrypted with the client's public key. 

# GET - If mode = json, return unencrypted peer list, otherwise return an html page with all known peers
@ledger.route('/peers', methods=['GET', 'POST'])
def test1():
    if request.method == 'POST':
        
        data = json.loads(request.get_data().decode('UTF-8'))
        encryptedNonce = data['encryptedNonce']
        publicKey = data['wallet']['publicKey']
        name = data['wallet']['name']
        ip = data['ip']
        decryptedNonce = rsa.decryptMessage(publicKey, encryptedNonce)
        reEncryptedNonce = rsa.encryptMessage(creatorPrivKey, decryptedNonce)

        if self.isDuplicate(ip):
            # don't send back peer list
            return ""
        else:
            # add to my list
            lock.acquire(blocking=True)
            peerList.append(Peer(ip, Wallet(name, publicKey)))
            lock.release()
            # send get request at /peers?mode=json
            g = requests.get(url = address+"/peers?mode=json")
            getResponse = g.getresponse()
            getData = getResponse.read()
            allGetData = JSON.parse(getData)
            # peerList is returned in unencrypted json
            newList = allGetData["peerList"]
            util.joinPeerLists(newList, peerList)

            # send back all known peers with encrypted nonce with my private key
            tosend = {
                "peerList": peerList,
                "publicKey": creatorKey,
                "encryptedNonce": reEncryptedNonce
            }
            jsonPeerList = json.dumps(peerList, indent=4, cls=ChainEncoder)
            return jsonPeerList
    else:
        mode = request.args.get('mode')
        if(mode == "json"):
            # returns an unencrypted JSON with a list of all known peers
            tosend = {
                "peerList": peerList,
            }
            jsonPeerList = json.dumps(peerList, indent=4, cls=ChainEncoder)
            return jsonPeerList
        else:
            # returns an HTML page populated with a list of all known peers 
            return render_template('startBlock.html', peers=peerList,)

# Check if a peer is already in the peer List by checking ip address
def isDuplicate(self, ip):
    for peer in peerList:
        if(peer.address==ip):
            return True
    return False


# Run the http Ledger
def runLedger():
    ledger.run(port=8001)

# Create a udp server object and run the broadcaster and receiver at the same time
def runUdpThread():
    bob = Udp(peerList)
    bob.runSameTime()

# Run both ledger and Udp Server at the same time
def runTogether():
    ledgerThread = threading.Thread(target=runLedger)
    udpServerThread = threading.Thread(target=runUdpThread)
    ledgerThread.start()
    udpServerThread.start()
    ledgerThread.join()
    udpServerThread.join()

runTogether()