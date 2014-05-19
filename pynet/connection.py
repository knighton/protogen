#!/usr/bin/python
#
# encapsulates sending and receiving with a foreign port.
#
# uses data format in protocol.py.

import socket

from pynet import protocol


class Connection():
  def __init__(self):
    self.sock = None

  def connect(self, to_host, to_port):
    assert isinstance(to_host, basestring)
    assert isinstance(to_port, int)
    assert not self.sock
    try:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.connect((to_host, to_port))
      return True
    except:
      try:
        del self.sock
      except:
        pass
      return False

  def send_and_receive(self, message):
    protocol.send(self.sock, message)
    not_hung_up, s = protocol.receive(self.sock)
    assert not_hung_up
    return s

  def is_connected(self):
    return bool(self.sock)

  def disconnect(self):
    assert self.sock
    self.sock.close()
