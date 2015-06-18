Simple P2P protocol
===================

Requirements
------------
The protocol must be:
* P2P, aside from known peers provided any trackers
* anonymous, no information must be stored about the peers
* secure, communication between peers must be encrypted

Implementation
--------------
The protocol will be implemented over UDP.

### Peer Discovery
Peer discovery will be bootstrapped by providing one (or more) known peers, or by tracker services. Once a peer has obtained a list of these peers, it will insert them into a list and timestamp them, and then attempt to contact them to download a list of their known peers.

It will do so by sending to each of them in turn a PEER 0 packet, which will prompt each of these peers, if connected, to answer in kind with a list of the peers it knows.

**How should a peer act upon a PEERS packet?** Or, do I need to distinguish between the act of asking for peers and broadcasting them?

I can simply split this in two actions - one is the asking for peers (PEERS?/PEERS 0), and the other is the publishing of peers.

Or... I don't even need to do that.

A peer will periodically attempt to publish the list of its known peers to all of them, both to update them and to keep the connection from being dropped.

A peer will blindly add any of the peer it doesn't knows to its list, and then attempt to contact them later.

The list will have this form:

    IP; PORT; LAST_ALIVE; LAST_CONTACTED

Once a PEERS 0 (or any packet, for that matter) is received by a peer, it will add the recipiend to this list, with its LAST_ALIVE field set to now(), and its LAST_CONTACTED field set to 0.

This means that it will instantly try to contact that peer, by means of a PEERS broadcast, and then to update the LAST_CONTACTED field with the current timestamp. A peer will periodically attempt to contact any peer in its list.
