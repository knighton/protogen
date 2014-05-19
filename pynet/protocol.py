#!/usr/bin/python
#
# prepend length to messages to handle splitting over an arbitrary number of
# sends/recvs.

import socket
import struct


def send(sock, message):
  """send message."""
  assert sock
  assert isinstance(message, str)

  total_len = len(message) + 4
  net_len_str = struct.pack('I', socket.htonl(total_len))
  sock.send(net_len_str)
  sock.send(message)


def receive(sock):
  """receive message, returns (not hung up, message data)."""
  assert sock

  s = sock.recv(4)
  if len(s) == 0:
    return False, ''

  assert len(s) == 4  # assumes that can get through at once (may have to fix).
  n, = struct.unpack('I', s)
  payload_len = socket.ntohl(n) - 4

  ss = []
  ss_len = 0
  while ss_len < payload_len:
    s = sock.recv(payload_len - ss_len)
    ss_len += len(s)
    ss.append(s)
  return True, ''.join(ss)
