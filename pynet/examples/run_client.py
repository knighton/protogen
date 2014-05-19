#!/usr/bin/python

from pynet import connection

conn = connection.Connection()
assert conn.connect('localhost', 1337)
s = conn.send_and_receive('what the fuck')
print 'got back: [%s]' % s
assert s == 'WHAT THE FUCK'
s = conn.send_and_receive('righto')
print 'got back: [%s]' % s
assert s == 'RIGHTO'
