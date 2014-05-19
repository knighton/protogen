#!/usr/bin/python
#
# wrapper around protoc that also generates code for our custom rpc service.
#
# given a .proto, generates protocol buffer and protobuf rpc service definitions
# in each language desired.
#
# example:
#   ../protogen/protogen.py name_info.proto cc=. py=.

import os
import subprocess
import sys

# add the root directory, which is one dir up, to the path, so it can import
# anything in the project.
# s = sys.path[0]
# sys.path.append(s[:s.rfind('/')])

import cc_service_emitter, proto_services_reader, py_service_emitter


def execute_child(command):
  """returns child process's exit code."""
  print '>> executing [%s] from [%s]' % (command, os.getcwd())
  child = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
  streamdata = child.communicate()[0]
  return child.returncode


def make_protoc_command(proto_filename, lang2outdir):
  """(desired lang -> output location) -> protoc command."""
  pglang2protoclang = {
      'cc': '--cpp_out',
      'py': '--python_out',
  }

  ss = ['protoc']
  ss.append(proto_filename)
  for lang, dirname in lang2outdir.iteritems():
    s = pglang2protoclang[lang]
    ss.append(s)
    ss.append(dirname)
  s = ' '.join(ss)
  return s


def get_codebase_root_dir(here_dirs_below_root):
  assert isinstance(here_dirs_below_root, int)
  assert 0 <= here_dirs_below_root
  s = os.path.abspath(__file__)
  s = s[:s.rfind(os.path.sep)]
  for n in range(here_dirs_below_root):
    s = s[:s.rfind(os.path.sep)]
  return s


ROOT_DIR = get_codebase_root_dir(1)


def get_num_dirs_below_root(d):
  """relative file path -> number of directories up to root."""
  # get full path of the given file.
  f = os.path.abspath(d)

  # verify it's below the root dir.
  assert len(ROOT_DIR) <= len(f)
  assert f[:len(ROOT_DIR)] == ROOT_DIR

  # count how many directories between us and the root dir.
  n = f[len(ROOT_DIR):].count(os.path.sep)
  return n


os.path.abspath(__file__)


def generate(proto_filename, lang2outdir):
  # call protoc to generate protocol buffer definitions for the desired
  # languages.
  cmd = make_protoc_command(proto_filename, lang2outdir)
  ret = execute_child(cmd)
  assert ret == 0  # if not 0, failed.

  # make it executable.
  f = os.path.join(lang2outdir['py'],
                   proto_filename[:-len('.proto')] + '_pb2.py')
  assert os.path.exists(f)
  #ret = os.system('chmod +x %s' % f)
  #assert ret == 0

  # extract services from proto.
  # we know it's valid since protoc didn't die.
  assert proto_filename.endswith('.proto')
  proto = proto_services_reader.proto_from_file(proto_filename)
  if not proto.service2rpcs:
    raise Exception('no services in the proto!')

  # generate our own rpc services for each lang.
  lang2handler = {
      'cc': cc_service_emitter.generate_service,
      'py': py_service_emitter.generate_service,
  }
  for service, rpcs in proto.service2rpcs.iteritems():
    # XService -> XServer, XClient.
    if service.endswith('Service'):
      service = service[:-len('Service')]

    for lang, outdir in lang2outdir.iteritems():
      # get the info needed for constructing net/pynet import paths.
      num_dirs_below_root = get_num_dirs_below_root(outdir)

      assert lang2handler[lang](
          proto_filename, num_dirs_below_root, proto.package, service, rpcs,
          outdir)


if 2 <= len(sys.argv):
  # get what languages to generate definitions for, and where to put them.
  pairs = map(lambda s: s.split('='), sys.argv[2:])
  lang2outdir = dict(zip(map(lambda ss: ss[0], pairs),
                         map(lambda ss: ss[1], pairs)))
  proto_filename = sys.argv[1]
  generate(proto_filename, lang2outdir)
else:
  print 'usage: %s file.proto cc=../somedir py=../somedir' % sys.argv[0]
