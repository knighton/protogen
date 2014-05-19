#!/usr/bin/python
#
# emit protocol buffer rpc services in c++.

import os
import re
import sys
import proto_services_reader


METHOD_HANDLER_TEMPLATE = """
      %s%s in_pb;
      assert(in_pb.ParseFromString(in_payload));
      %s%s out_pb;
      keep_running = %s(in_pb, &out_pb);
      out_pb.SerializeToString(out);
"""


def generate_method_handler(namespace_str, rpc):
  text = METHOD_HANDLER_TEMPLATE % (
      namespace_str, rpc.request_type, namespace_str, rpc.response_type,
      rpc.name)
  return text.split('\n')


CLIENT_DEF_TEMPLATE = """
  bool %s(const %s%s& in, %s%s* out) {
    string in_str;
    in.SerializeToString(&in_str);
    string message = string(4, (char)0);
    *(uint32_t*)&(*message.begin()) = htonl(%s);
    message.reserve(message.size() + in_str.size());
    message += in_str;

    string out_str;
    if (!conn_.SendAndReceive(message, &out_str)) {
      return false;
    }

    if (!out->ParseFromString(out_str)) {
      return false;
    }

    return true;
  }
"""


def generate_client_method(namespace_str, rpc, method_define):
  return CLIENT_DEF_TEMPLATE % (
      rpc.name, namespace_str, rpc.request_type, namespace_str,
      rpc.response_type, method_define)


FILE_TEMPLATE = """
#ifndef {header_guard}
#define {header_guard}

// AUTO-GENERATED BY protogen -- DO NOT EDIT!

#include <netinet/in.h>
#include <string>
#include "{up_to_root}net/server.h"
#include "{up_to_root}net/client.h"
#include "{filename_pb_h}"

using std::string;

{method_id_defines}

class {service_name}ServerBase : public Server {
 public:
  // Receive and respond to input.
  // Returns whether to continue serving.
  bool Handle(const string& in, string* out) {
    uint32_t method_id = *(uint32_t*)&(*in.begin());
    method_id = ntohl(method_id);
    string in_payload = in.substr(sizeof(method_id));
    bool keep_running = false;
{handle_callouts}
    } else {
      assert(false);
    }
    return keep_running;
  }

{handlers}
};

class {service_name}Client : public Client {
 public:
{client_impl}
};

#endif  // {header_guard}
"""


def random_uppercase_str(length):
  import random
  import string
  ss = []
  for _ in range(length):
    c = random.choice(string.uppercase)
    ss.append(c)
  return ''.join(ss)


def generate_file(proto_filename, num_dirs_below_root, package, service_name,
                  rpcs):
  # add c++ namespace for package in protobuf definition, if any.
  namespace_str = package.replace('.', '::') + '::' if package else ''

  # decide header guard.
  header_guard = 'PROTOGEN_%s_%s_H_' % (service_name.upper(),
                                        random_uppercase_str(8))

  up_to_root = os.path.sep.join(['..' + os.path.sep] * num_dirs_below_root)

  # pb.h include.
  filename_pb_h = proto_filename[:-len('.proto')] + '.pb.h'

  # method name -> #define name.
  method2define = {}
  for rpc in rpcs:
    s = '_%s_%s_METHOD_ID' % (service_name.upper(), rpc.name.upper())
    method2define[rpc.name] = s

  # create the list of #defines.
  defines = []
  for i, rpc in enumerate(rpcs):
    defines.append('#define %s %s' % (method2define[rpc.name], i))
  method_id_defines_str = '\n'.join(defines)

  # handling code: each method uses the strings as different types.
  handle_callouts = []
  for i, rpc in enumerate(rpcs):
    if i == 0:
      handle_callouts.append('    if (method_id == %s) {' %
                          (method2define[rpc.name],))
    else:
      handle_callouts.append('    } else if (method_id == %s) {' %
                          (method2define[rpc.name],))
    handle_callouts += filter(bool, generate_method_handler(namespace_str, rpc))
  handle_callouts_str = '\n'.join(handle_callouts)

  # create server-side virtual method definitions for user implementation.
  handlers = []
  for rpc in rpcs:
    handlers.append('  virtual bool %s(const %s%s& in, %s%s* out) = 0;' %
                    (rpc.name, namespace_str, rpc.request_type, namespace_str,
                     rpc.response_type))
  handlers_str = '\n'.join(handlers)

  # create client-side methods.
  client_impl = []
  for rpc in rpcs:
    text = generate_client_method(namespace_str, rpc, method2define[rpc.name])
    client_impl.append(text)
  client_impl_str = ''.join(client_impl)[1:-1]

  s = FILE_TEMPLATE
  for key, value in {
      'header_guard':      header_guard,
      'up_to_root':        up_to_root,
      'filename_pb_h':     filename_pb_h,
      'method_id_defines': method_id_defines_str,
      'service_name':      service_name,
      'handle_callouts':   handle_callouts_str,
      'handlers':          handlers_str,
      'client_impl':       client_impl_str,
  }.iteritems():
    s = s.replace('{%s}' % key, value)
  return s[1:-1]


def camel_case_to_underscores(name):
  s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def make_filename(outdir, service_name):
  ss = [outdir]
  if not outdir.endswith('/'):
    ss.append('/')
  ss.append(camel_case_to_underscores(service_name))
  ss.append('_service')
  ss.append('.h')
  s = ''.join(ss)
  return s


def generate_service(proto_filename, num_dirs_below_root, package, service_name,
                     rpcs, outdir):
  text = generate_file(proto_filename, num_dirs_below_root, package,
                       service_name, rpcs)
  filename = make_filename(outdir, service_name)
  open(filename, 'w').write(text)
  return True