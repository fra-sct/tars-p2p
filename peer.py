#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, select
import threading, queue
import sys, time, json

stdout_lock = threading.Lock()

class Peer(object):
    def __init__(self, config):
        self._config_from_object(config)
        self._initialize_socket()

        self.timer = 0 #debug only

        self.running = True
        self.messages = queue.Queue()
        self.inbound = queue.Queue()
        self.outbound = queue.Queue()
    def stop(self):
        self.running = False
    def run(self):
        self.t_housekeep = threading.Thread(target=self.handle_housekeeping, daemon=True)
        self.t_listen = threading.Thread(target=self.listen, daemon=True)
        self.t_input = threading.Thread(target=self.handle_input)
        self.t_housekeep.start()
        self.t_listen.start()
        self.t_input.start()
    def send(self, address, data):
        self.outbound.put((data, address))
    def broadcast(self, data):
        for peer in self.peers:
            self.send(peer, data)
    def log(self, message):
        self.messages.put(message)
    def add_peer(self, address, port):
        if (address, port) in self.peers or \
           len(self.peers) <= self.max_peers:
            now = time.time()
            self.peers[(address, port)] = now
    def clear_peers(self):
        now = time.time()
        self.peers = {
            peer: timestamp
            for peer, timestamp in self.peers
            if now < (timestamp + self.peer_timeout)
        }
    def _config_from_object(self, config=None):
        self.peers = {} #Connected peers
        self.packets = [] #Last handled packets
        self.hash = {} #Owned data
        self.select_timeout = 0.00001
        self.packet_timeout = 300
        self.peer_timeout = 300
        self.max_peers = 10
        self.address = ""
        self.port = 5000
        self.buffer_size = 4096
        #Now load from the object
        if config:
            self.__dict__.update(config)
    def _initialize_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET,
            socket.SO_REUSEADDR, 1) # Make Socket Reusable
        self.socket.setsockopt(socket.SOL_SOCKET,
            socket.SO_BROADCAST, 1) # Allow incoming broadcasts
        self.socket.bind((self.address, self.port))
    def listen(self):
        while self.running:
            read, write, error = select.select(
                [self.socket], [self.socket], [],
                self.select_timeout)
            for socket in read:
                try:
                    packet = socket.recvfrom(self.buffer_size)
                    data, addr = packet
                    data = data.decode()
                    self.inbound.put((data, addr))
                except ConnectionAbortedError:
                    log("ERR: Connection aborted")
                except ConnectionResetError:
                    log("ERR: Connection reset by peer")
            for socket in write:
                try:
                    packet = self.outbound.get_nowait()
                    data, addr = packet
                    data = data.encode()
                    self.socket.sendto(data, addr)
                except queue.Empty:
                    pass
    def handle_housekeeping(self):
        while self.running:
            self.handle_inbound()
            self.hello()
            self.handle_messages()
            self.clear_peers()
    def hello(self):
        now = time.time()
        if now > self.timer:
            self.log("HELLO from %s!" % now)
            self.timer = now + 5
    def handle_inbound(self):
        try:
            packet = self.inbound.get_nowait()
            data, addr = packet
            self.log("%s :: %s" % (addr, data))
        except queue.Empty:
            pass
    def handle_messages(self):
        try:
            message = self.messages.get_nowait()
            with stdout_lock:
                print(message)
        except queue.Empty:
            pass
    def handle_input(self):
        while self.running:
            input()
            with stdout_lock:
                data = input('>')
                if data == "quit":
                    self.running = False

if __name__ == "__main__":
    config = None
    if len(sys.argv) > 1:
        config = json.loads(open(sys.argv[1], "r").read())
    peer = Peer(config)
    peer.run()
