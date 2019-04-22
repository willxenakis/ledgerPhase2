import threading

lock = threading.Lock()

# Given two peer lists, join the peerLists, if old list is not given default is ledger Peer List
def joinPeerLists(self, newList, oldList):
    for newPeer in newList:
        newPeerIsNew = True
        for oldPeer in oldList:
            if(newPeer.address == oldPeer.address):
                newPeerIsNew = False
        if(newPeerIsNew):
            lock.acquire(blocking=True)
            peerList.append(newPeer)
            lock.release()