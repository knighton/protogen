#!/usr/bin/python

import select
import socket
from pynet import protocol, util


class Server(object):
  def __init__(self, port, on_ready=None, on_shutdown=None, backlog=5):
    assert util.is_port(port)
    if on_ready:
      assert isinstance(on_ready, list)
    if on_shutdown:
      assert isinstance(on_shutdown, list)
    assert isinstance(backlog, int)
    assert 0 < backlog

    self.port = port
    self.on_ready_callbacks = on_ready if on_ready else []
    self.on_shutdown_callbacks = on_shutdown if on_shutdown else []
    self.backlog = backlog

  def loop(self):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', self.port))
    server.listen(self.backlog)

    inputs = [server]

    # call the on-ready callbacks, if any.
    map(apply, self.on_ready_callbacks)

    keep_running = True
    while True:
      try:
        in_ready, out_ready, err_ready = select.select(inputs, [], [])
      except select.error, e:
        print 'select error', e
        break
      except socket.error, e:
        print 'socket error', e
        break

      for sock in in_ready:
        if sock == server:  # handle the server socket.
          client, address = server.accept()
          print 'got connection %s from %s' % (client.fileno(), address)
          inputs.append(client)
        else:  # handle all other sockets.
          try:
            not_hung_up, data = protocol.receive(sock)
            if not not_hung_up:
              print '%d hung up' % (sock.fileno(),)
              inputs.remove(sock)
              sock.close()
            else:
              response, keep_running = self.handle(data)
              protocol.send(sock, response)
          except socket.error, e:
            print 'socket error', e
            inputs.remove(sock)

      if not keep_running:
        break

    # call the on-shutdown callbacks, if any.
    map(apply, self.on_shutdown_callbacks)
