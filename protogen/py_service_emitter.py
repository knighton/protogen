#!/usr/bin/python
#
# emit protocol buffer rpc services in python.

import os
import re


SERVER_CALL_TEMPLATE = """
    {if} method_id == {method_id}:
      q = {service_module}.{request_type}()
      q.ParseFromString(payload)
      r, keep_running = self.{handle}(q)
      assert isinstance(r, {service_module}.{response_type})
      r = r.SerializeToString()
"""


def make_server_calls(service_module, rpcs, method2define):
  blocks = []
  for i, rpc in enumerate(rpcs):
    text = SERVER_CALL_TEMPLATE
    for key, value in {
        'if':             'if' if i == 0 else 'elif',
        'method_id':      method2define[rpc.name],
        'service_module': service_module,
        'request_type':   rpc.request_type,
        'handle':         rpc.name,
        'response_type':  rpc.response_type,
    }.iteritems():
      text = text.replace('{%s}' % key, value)
    blocks.append(text)
  return ''.join(map(lambda _: _[:-1], blocks))


SERVER_DEF_TEMPLATE = """
  def {name}(self, q):
    \"\"\"{request_type} -> {response_type}, keep_running.\"\"\"
    raise NotImplementedError
"""


def make_server_defs(rpcs):
  blocks = []
  for rpc in rpcs:
    text = SERVER_DEF_TEMPLATE
    for key, value in {
        'name':          rpc.name,
        'request_type':  rpc.request_type,
        'response_type': rpc.response_type,
    }.iteritems():
      text = text.replace('{%s}' % key, value)
    blocks.append(text)
  return ''.join(blocks)[1:-1]


CLIENT_DEF_TEMPLATE = """
  def {name}(self, q):
    \"\"\"{request_type} -> {response_type}.\"\"\"
    assert isinstance(q, {service_module}.{request_type})
    s = q.SerializeToString()
    s = struct.pack('i', socket.htonl({method_id})) + s
    a_str = self.conn.send_and_receive(s)
    a = {service_module}.{response_type}()
    a.ParseFromString(a_str)
    return a
"""


def make_client_defs(service_module, rpcs, method2define):
  blocks = []
  for rpc in rpcs:
    text = CLIENT_DEF_TEMPLATE
    for key, value in {
        'service_module': service_module,
        'name':           rpc.name,
        'request_type':   rpc.request_type,
        'response_type':  rpc.response_type,
        'method_id':      method2define[rpc.name],
    }.iteritems():
      text = text.replace('{%s}' % key, value)
    blocks.append(text)
  return ''.join(blocks)[1:-1]


FILE_TEMPLATE = """
#!/usr/bin/python
#
# client and server base class definitions for the {service_camel} service.
# subclass the server with your own impls (search for NotImplementedError).
#
# AUTO-GENERATED BY protogen -- DO NOT EDIT!

import socket
import struct
from pynet import clients, servers
from {import_dirpath} import {service_module}

{method_defs}

class {service_camel}ServerBase(servers.Server):
  def handle(self, message):
    \"\"\"input blob -> output blob, keep_running.\"\"\"
    _ = struct.unpack('i', message[:4])[0]
    method_id = socket.ntohl(_)
    payload = message[4:]
{server_calls}
    else:
      assert False
    return r, keep_running

{server_defs}

class {service_camel}Client(clients.Client):
{client_defs}
"""


def camel_case_to_underscores(name):
  s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def make_import_dirpath(proto_filename):
  path = os.path.abspath(proto_filename)

  xx = []
  for i, c in enumerate(path):
    if c == os.path.sep:
      xx.append(i)
  assert xx

  # note: pynet/ is a top-level directory in the codebase directory structure,
  # so we use that to tell where the top is for creating the import.
  xx = list(reversed(xx))
  for x in xx:
    if 'pynet' in os.listdir(path[:x]):  # work upward looking for top level.
      return path[x + 1:xx[0]].replace(os.path.sep, '.')

  assert False


def generate_file(proto_filename, service_name, rpcs):
  import_dirpath = make_import_dirpath(proto_filename)

  service_module = camel_case_to_underscores(service_name) + '_pb2'

  # method name -> constant.
  method2define = {}
  for rpc in rpcs:
    s = '_%s_%s_METHOD_ID' % (service_name.upper(), rpc.name.upper())
    method2define[rpc.name] = s

  # create the list of constants.
  ss = []
  for i, rpc in enumerate(rpcs):
    ss.append('%s = %s' % (method2define[rpc.name], i))
  method_defs = '\n'.join(ss)

  # server calls.
  server_calls = make_server_calls(service_module, rpcs, method2define)

  # server defs.
  server_defs = make_server_defs(rpcs)

  # client defs.
  client_defs = make_client_defs(service_module, rpcs, method2define)

  text = FILE_TEMPLATE
  for key, value in {
      'import_dirpath': import_dirpath,
      'service_module': service_module,
      'method_defs':    method_defs,
      'service_camel':  service_name,
      'server_calls':   server_calls,
      'server_defs':    server_defs,
      'client_defs':    client_defs,
  }.iteritems():
    text = text.replace('{%s}' % key, value)
  return text[1:-1]


def make_filename(outdir, service_name):
  ss = [outdir]
  if not outdir.endswith('/'):
    ss.append('/')
  ss.append(camel_case_to_underscores(service_name))
  ss.append('_service')
  ss.append('.py')
  s = ''.join(ss)
  return s


def generate_service(proto_filename, _, package, service_name, rpcs, outdir):
  # package name is ignored in python (module-level namespacing for free).

  text = generate_file(proto_filename, service_name, rpcs)
  filename = make_filename(outdir, service_name)
  open(filename, 'w').write(text)

  # make executable.  note: don't use spaces and other weird characters in file
  # names.
  f = filename.replace(' ', '\ ')
  #os.system('chmod +x %s' % f)
  return True
