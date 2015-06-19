Simple P2P protocol
===================

Requirements
------------
The protocol must be:
* P2P, aside from known peers provided by any trackers
* anonymous, no information must be stored about the peers
* secure, communication between peers must be encrypted

Implementation
--------------
The protocol will be implemented over UDP.

### Peer Discovery
Each peer will keep a list of known peers. This list will have the following form:

    IP_address; port; added; last_alive; last_contacted

When adding a peer to the list, its `last_alive` and added fields will be set to the current timestamp, but its `last_contacted` field will be set to 0.

If a peer's `last_contacted` field is old, this means that the current peer will attempt to update it with a `PEERS` packet. It will only send any peers that have been added after the `last_contacted` timestamp. This will set the `last_contacted` field to the current timestamp.

If a peer's `last_alive` field is too old, this means that that peer is likely dead or disconnected and can be removed from the list. If any packets are received before then, the `last_alive` field is updated to the timestamp of the packet.

Initial sketch of the code:

    CONTACT_EVERY = 100
    DELETE_EVERY = 300

    def add_peer(ip, port):
      now = time.time()
      peers.append(ip=ip, port=port,
        added=now, alive=now, contacted=0)

    def added_after(timestamp):
      return filter(lambda i: i.alive>timestamp, peers)

    def heartbeat():
      now = time.time()
      for ip, port, added, alive, contacted in peers:
        if now > contacted + CONTACT_EVERY:
          new_peers = added_after(contacted)
          packet = build_peers_packet(new_peers)
          send((ip, port), packet)
        elif now > alive + DELETE_EVERY:
          delete_peer(ip, port)

### Data
Data packets represent just that - data and message packets moving over the net. Each of these packets consists of two parts: the data itself, and an hash of the data. The hash is used to identify the data packet in the network.

Each peer can `PUBLISH` a list of packets it owns, and adjacent peers can `SUBSCRIBE` to them, asking for any packets they don't own. These packets will then be sent out as `DATA` packets.

This should work as per the Peer Discovery section - I need to add a `last_published` field to the peer list, and send out `PUBLISH` packets separately, for every packet that has been added after the peer was last contacted.

But, as the `last_published` field will be set to 0 once a peer is added to the list this means that any node that connects to the net will publish to them every single packet stored in that node that hasn't been deleted yet.

NOTE: This... shouldn't be too bad. Or is it? :-/

As the `last_published` field is initialized to 0, at the next heartbeat a list of all the packets owned by the server will be published. I need to add a timestamp field to the publish packet, as a peer knows since when it has been offline.

Maybe instead of broadcasting `PEERS` a peer could broadcast a `LIVE` packet, like in my first implementation? And when a `LIVE` packet is sent, the peer will be initialized with its contained data.

This is starting to get complex. I'll just let the peers send `PEERS` packet together with a timestamp. This timestamp is the peer's `last_published`, or the last time it received a `PEERS` packet.

A peer that is just connecting to the net will have 0 in that field, but any other peer will have a reasonable time there.

Then, as per the peer discovery system, every connected peer will be periodically updated with new `PUBLISH` packets. If that peer detects any packet it doesn't own it will store that information in a `known_packets` table, together with the peer that it knows owns it.

Then, it will reply by broadcasting a `SUBSCRIBE` packet for those data packets to all or a few peers that it knows own that particular packet.

These peers will reply to a `SUBSCRIBE` packet by sending a `DATA` packet out, if they haven't send the same packet out very recently.

#### Tables
`known_packets` table

    hash: [peer, peer, peer]

`packets` table

    hash: [last_sent, data]
