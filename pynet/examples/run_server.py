#!/usr/bin/python

from pynet import server

class DemoServer(server.Server):
  def Handle(self, s):
    return s.upper()

server = DemoServer(1337)
server.loop()
