#!/usr/bin/python

import socket


def get_own_ip_address(target='192.168.0.0'):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect((target, 8000))
  ip = s.getsockname()[0]
  s.close()
  return ip


def is_port(n):
  return isinstance(n, int) and 0 < n < 65536
