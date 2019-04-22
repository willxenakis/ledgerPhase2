import time
import hashlib
import rsa
import base64
import json

class ChainEncoder(json.JSONEncoder):
    def default(self, object):
        if hasattr(object, 'toJSON'):
            return object.toJSON()
        else:
            return json.JSONEncoder.default(self, object)

class ChainDecoder(json.JSONDecoder):
    def object_hook(self, obj):
        if '__type__' not in obj:
            return obj

        type = obj['__type__']
        if type == 'Transaction':
            obj.pop('__type__')

            rtn = Transaction.parseJSON(obj)
            return rtn
        
        return obj

class Block(object):
    prevHash = None
    currHash = None
    def __init__(self, data, index = 0, prevBlock = None, nextBlock = None):
        self.index = index
        self.data = data
        self.nonce = 0
        self.prevBlock = prevBlock
        self.nextBlock = nextBlock
        self.timeStampt = time.time()
        self.merkleRoot = self.createMerkleRoot()
        
    def getCurrHash(self):    
        hasher = hashlib.sha256()
        hasher.update(str(self.index).encode())
        hasher.update(str(self.prevHash).encode())
        hasher.update(str(self.timeStampt).encode())
        hasher.update(str(self.nonce).encode())
        hasher.update(str(self.merkleRoot).encode())

        # base 16
        return hasher.hexdigest()

    # Transactions should be an array of trnasactions
    def createMerkleRoot(self):
        merkleTree = self.data[:]
        i = 0

        #Hash all the transactions and create a list
        while(not all(isinstance(i, str) for i in merkleTree)):
            merkleTree[i] = merkleTree[i].createHash()
            i += 1
        if len(merkleTree) == 1:
            return merkleTree[0]
        else:
            #Creating merkle root by combining first two hashes in list and then appending to list
            while len(merkleTree) != 1:
                hasher = hashlib.sha256()
                data1 = merkleTree.pop(0)
                data2 = merkleTree.pop(0)
                hasher.update(str(data1).encode())
                hasher.update(str(data2).encode())
                merkleTree.append(hasher.hexdigest())
            return merkleTree[0]

    def toJSON(self):
        jsonObject = {
            "__type__": self.__class__.__name__
        }
        jsonObject.update(self.__dict__)

        return jsonObject
    """
        Returns a JSON of the current block
    """
    def __repr__(self):
        return json.dumps(self, cls=ChainEncoder)


class Transaction(object):
    def __init__(self, receiverWallet, operation, senderWallet = None, timestamp = None,  _hash=None):
        self.senderPub = None
        if(senderWallet != None):
            self.senderPub = senderWallet.public
        if(timestamp != None):
            self.timeStamp = timestamp
        else:
            self.timeStamp = time.time()
        self.receiverPub = receiverWallet.public
        self.timeStamp = time.time()
        self.op = operation

        if(_hash == None):
            if(senderWallet == None):
                thehash = self.createHash()
                self.hash = thehash
            else:
                thehash = self.createHash()
                self.hash = rsa.encryptMessage(senderWallet.private, str(thehash))
        else:
            thehash = self.createHash()
            self.hash = thehash

    def toJSON(self):
        json = {
            "__type__": self.__class__.__name__,
        }
        json.update(self.__dict__)

        return json

    @staticmethod
    def parseJSON(json):

        receiver = Wallet('', json['recv'], '')
        sender = Wallet('', json['sender'], '')

        return Transaction(receiver, json['amount'], sender, 
                                json['timestamp'], json['hash'])

    """
        returns a String in JSON format
    """
    def __repr__(self):
        return json.dumps(self, cls=ChainEncoder)

    def decryptHash(self):
        #Decrypt operation with sender public key
        return rsa.decryptMessage(self.senderPub,str(self.hash))

    def createHash(self):
        hasher = hashlib.sha256()
        if(self.senderPub != None):
            hasher.update(str(self.senderPub).encode())
        else:
            hasher.update("System".encode())
        hasher.update(str(self.receiverPub).encode())
        hasher.update(str(self.timeStamp).encode())
        hasher.update(str(self.op).encode())
        return hasher.hexdigest()
        
class Wallet(object):
    """
    Create a wallet with Base64 encoded strings or with 
    public and private being tuples with numbers.  If tuples
    are used then the value passed for 'n' is ignored.
    """
    def __init__(self, realname, public, private, n = ""):
        if realname == None or len(realname.strip()) == 0:
            realname = ""

        if isinstance(public, tuple):
            n = rsa.intToBase64String(public[1])
            public = rsa.intToBase64String(public[0])

        if isinstance(private, tuple):
            n = rsa.intToBase64String(private[1])
            private = rsa.intToBase64String(private[0])
            

        self.name = realname
        self.public = public+n
        self.private = private+n
    
    def toJSON(self):
        json = {
            "__type__": self.__class__.__name__
        }
        json.update(self.__dict__)
        return json

    def __repr__(self):
        return json.dumps(self, cls=ChainEncoder)


# The Block Chain is a doubly linked list of Blocks
class blockChain(object):
    def __init__(self, creator, difficulty = 2):
        self.difficulty = difficulty
        
        #The creator receives 100 coins from the system (hence the None sender)
        x = Transaction(creator, 100)
        genesis = Block([x])
        genesis.prevHash = None
        genesis.currHash = genesis.getCurrHash()
        while True:
            # Find the nonce that makes the curr hash begin with a difficulty number of 0's
            if(len(genesis.currHash) - len(genesis.currHash.lstrip('0')) < difficulty):
                genesis.nonce += 1
                genesis.timeStampt = time.time()
                genesis.currHash = genesis.getCurrHash()
            else:
                break
        self.head = self.tail = genesis

 
    #Data should be an array of transactions however in this lab there is only one transaction per block
    #The mineBlock function takes a Transaction as a paramater 
    def mineBlock(self, data):
        if len(data) > 255:
            data = data[:255]

        #Transaction that is reward for creator / miner    
        # APubKey = open("Apublic.key" , "r").read()

        APubKey = open("Apublic.key", "r").read()
        APrivKey = open("Aprivate.key", "r").read()
        miner = Wallet("Miner", APubKey, APrivKey)

        #Insert mining reward into front of transactions
        data.insert(0, Transaction(miner, 10))

        newBlock = Block(data)
        
        # Set up everything needed for a doubly linked list node
        newBlock.prevBlock = self.tail
        newBlock.currHash = newBlock.getCurrHash()
        newBlock.prevHash = self.tail.currHash
        newBlock.index = self.tail.index + 1
        while True:
            # Find the nonce that makes the curr hash begin with a difficulty number of 0's
            if(len(newBlock.currHash) - len(newBlock.currHash.lstrip('0')) < self.difficulty):
                newBlock.nonce += 1
                newBlock.timeStampt = time.time()
                newBlock.currHash = newBlock.getCurrHash()
            else:
                break
        
        newBlock.currHash = newBlock.getCurrHash()
        self.tail.nextBlock = newBlock
        self.tail = newBlock
    
    def getLatestBlock(self):
        return self.tail   

    def getHead(self):
        return self.head 
                
    def verifyChain(self):
        tempBlock = self.tail

        # Go through the chain from tail to head rehashing the previous block and checking if 
        # that hash and the prevHash in the current block are the same. Also checking that the decrypted hash of each
        # transaction is the same as the recreated hash of the transaction. Finally check that the merkleRoot is still valid
        # by recreating the merkle root and checking it against the old root.
        while(tempBlock.index!=0):
            for x in tempBlock.data[1:]:
                if x.decryptHash() != x.createHash():
                    return False, tempBlock.index
            if (tempBlock.prevBlock.getCurrHash() != tempBlock.prevHash) or (tempBlock.merkleRoot != tempBlock.createMerkleRoot()):
                return False, tempBlock.index
            tempBlock = tempBlock.prevBlock
        if(tempBlock.merkleRoot != tempBlock.createMerkleRoot()):
            return False, 0
        return True, None

    # Given a user's public id (key) go through the chain from head to tail and check for any transactions
    # involving the user, accumulate a value representing the user's balance
    def getBalance(self, userPubId):
        tempBlock = self.head
        accumulator = 0
        while(tempBlock != None):

            for x in tempBlock.data:
                # If the sender public key is None then the system is sending coins which means the data is not signed
                # and therefor need not be decrypted. Otherwise it needs to be decrypted first before adding or subtracting
                # the amount (operation) based on whether the given user is the sender or receiver
                if x.senderPub == userPubId:
                    accumulator -= x.op
                if x.receiverPub == userPubId:
                    accumulator += x.op
            tempBlock = tempBlock.nextBlock
        return accumulator

    def verifyTransaction(self, transaction):
        key = transaction.senderPub
        if key != None:
            
            operation = transaction.op
            # Given the operation (amount), if it is negative or the sender doesn't have a balance large
            # enough to send the amount, then the transaction is not verified
            if operation<0:
                return False
            elif self.getBalance(transaction.senderPub) < operation:
                return False
            else:
                return True            
        else:
            return True

    # Checks that in a list of transactions which are not yet in the block, which will be valid by taking the 
    # current balance of the user and subtracting from the list of new transactions until overspending occurs
    def noOverspending(self, userId, verifiedTransactions, unverifiedTransaction):
        balance = self.getBalance(userId)
        for x in verifiedTransactions:
            if(x.senderPub == userId):
                balance -= x.op
        if balance - unverifiedTransaction.op < 0:
            return False
        else:
            return True


# # Open and read the wallets of the two users in this test
# print("Reading Pair A...")
# APubKey = open("Apublic.key" , "r").read()
# APrivKey = open("Aprivate.key", "r").read()
# print("Reading Pair B...")
# BPrivKey = open("Bprivate.key", "r").read()
# BPubKey = open("Bpublic.key", "r").read()
# print("Creating BlockChain...")
# creator = Wallet("Creator A", APubKey, APrivKey)
# simpleCoin = blockChain(creator)

# aWallet = Wallet("Wallet A", APubKey, APrivKey)
# bWallet = Wallet("Wallet B", BPubKey, BPrivKey)

# # Create multiple test transactions
# transaction1 = Transaction(bWallet, 40, aWallet)
# transaction2 = Transaction(aWallet, 15, bWallet)
# transaction3 = Transaction(bWallet, 60, aWallet)
# transaction4 = Transaction(bWallet, 20, aWallet)
# transaction5 = Transaction(aWallet, 50, bWallet)



# transactionListPool = [[transaction1, transaction2], [transaction3, transaction4], [transaction5]]

# # Create a ledger of all the users based on the receiver
# ledger = {}
# ledger[simpleCoin.getHead().data[0].receiverPub] = "User 0"



# for indexX, x in enumerate(transactionListPool):
#     verifiedTransactions = []
#     for indexY, y in enumerate(x):
#         if y.receiverPub not in ledger:
#             ledger[y.receiverPub] = "User " + str(len(ledger))
#         if simpleCoin.verifyTransaction(y) and simpleCoin.noOverspending(y.senderPub, verifiedTransactions, y):
#             print("Transaction", indexY+1, "(Amount: " + str(y.op) + "): ", ledger[y.senderPub], "->", ledger[y.receiverPub], " ", "Accepted")
#             verifiedTransactions.append(y)
#         else:
#             print("Transaction", indexY+1, "(Amount: " + str(y.op) + "): ", ledger[y.senderPub], "->", ledger[y.receiverPub], " ", "Declined")
#     if len(verifiedTransactions) !=0:
#         print("Mining Block", simpleCoin.getLatestBlock().index + 1, "... ", end="")
#         simpleCoin.mineBlock(verifiedTransactions)
#         latestBlock = simpleCoin.getLatestBlock()
#         print(latestBlock.nonce, ", ", latestBlock.currHash)

# print("")
# print("Chain Verification... ", end="")

# # This next few line makes the chain invalid
# simpleCoin.getHead().data[0].op = 35
# simpleCoin.getLatestBlock().prevBlock.data[0].op = 10000

# a, b = simpleCoin.verifyChain()
# if not a:
#     print(str(a) + ". Invalid Block at Index", b)
# else:
#     print(a)
#     for x in ledger:
#         print("Amount in ", ledger[x] + "'s Wallet: ", simpleCoin.getBalance(x))