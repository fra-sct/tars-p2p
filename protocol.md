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
Each peer will keep a list of known peers. This list will have the following form:

    IP_address; port; added; last_alive; last_contacted

When adding a peer to the list, its last_alive and added fields will be set to the current timestamp, but its last_contacted field will be set to 0.

If a peer's last_contacted field is old, this means that the current peer will attempt to update it with a PEERS packet. It will only send any peers that have been added after the last_contacted timestamp. This will set the last_contacted field to the current timestamp.

If a peer's last_alive field is too old, this means that that peer is likely dead or disconnected and can be removed from the list. If any packets are received before then, the last_alive field is updated to the timestamp of the packet.

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
