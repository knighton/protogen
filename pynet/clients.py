#!/usr/bin/python
#
# Client base class.

import connection


class Client():
  def __init__(self):
    self.conn = connection.Connection()
