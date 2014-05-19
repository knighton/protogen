#!/usr/bin/python
#
# TODO: allow importing other protos (don't prefix with package name if things
# are from some other proto).


punct = '[](){}=;'


def remove_double_slash_comments(text):
  lines = text.split('\n')
  for i, s in enumerate(lines):
    n = s.find('//')
    if n != -1:
      lines[i] = s[:n]
  return ''.join(lines)


def tokenize_proto(text):
  text = remove_double_slash_comments(text)
  tokens = []
  buf = []
  for c in text:
    if c.isalnum() or c == '_':
      buf.append(c)
    elif c.isspace():
      if buf:
        tokens.append(''.join(buf))
        buf = []
    elif c in punct:
      if buf:
        tokens.append(''.join(buf))
        buf = []
      tokens.append(c)
    else:
      print '??', c
      assert False
  return tokens


def find_services(tokens):
  # get uses of the word "service" at the top level of the file (with comments
  # extracted).
  service_ii = []
  depth = 0
  for i, s in enumerate(tokens):
    if s == '{':
      depth += 1
    elif s == '}':
      depth -= 1
    elif s == 'service':
      if depth == 0:
        service_ii.append(i)
  return service_ii


class Rpc():
  def __init__(self, name, request_type, response_type):
    self.name = name
    self.request_type = request_type
    self.response_type = response_type

  def __lt__(self, other):
    return self.name < other.name

  def __le__(self, other):
    return self.name <= other.name

  def __eq__(self, other):
    return self.name == other.name

  def __str__(self):
    return ('(Rpc name=%s request_type=%s response_type=%s)' %
            (self.name, self.request_type, self.response_type))


def extract_rpc(ss):
  assert len(ss) == 9
  rpc, name, q_open, request, q_close, returns, a_open, response, a_close = ss
  assert rpc == 'rpc'
  assert name.isalnum()
  assert q_open == '('
  assert request.isalnum()
  assert q_close == ')'
  assert a_open == '('
  assert response.isalnum()
  assert a_close == ')'
  return Rpc(name, request, response)


def extract_service(tokens, service_i):
  assert tokens[service_i] == 'service'
  service_name = tokens[service_i + 1]
  assert service_name.isalnum()
  assert tokens[service_i + 2] == '{'

  rpcs = []
  end_i = None
  last_semicolon_i = service_i + 3
  for i, s in enumerate(tokens[service_i + 3:]):
    if s == ';':
      sub_ss = tokens[last_semicolon_i:service_i + 3 + i]
      _ = extract_rpc(sub_ss)
      rpcs.append(_)
      last_semicolon_i = service_i + 3 + i + 1
    elif s == '}':
      end_i = i
      break
  assert end_i is not None

  return service_name, rpcs


def extract_services(tokens, service_ii):
  service2rpcs = {}
  for i in service_ii:
    name, rpcs = extract_service(tokens, i)
    service2rpcs[name] = rpcs
  return service2rpcs


def extract_package(tokens):
  if not tokens or len(tokens) < 3:
    return None
  if tokens[0] == 'package' and tokens[2] == ';':
    return tokens[1]
  return None


class ProtoDefinition(object):
  """meaning of a .proto file."""

  def __init__(self, package, service2rpcs):
    self.package = package
    self.service2rpcs = service2rpcs

  def __str__(self):
    return ('(ProtoDefinition package=%s service2rpcs=%s)' %
            (self.package, self.service2rpcs))

  def dump(self):
    ss = []
    ss.append('ProtoDefinition {')
    ss.append('  package = %s' % self.package)
    for service, rpcs in sorted(self.service2rpcs.iteritems()):
      ss.append('    service %s {' % service)
      for rpc in rpcs:
        ss.append('      %s' % rpc)
      ss.append('    }')
    ss.append('}')
    return ss.join('\n')


def proto_from_file(filename):
  text = open(filename).read()
  tokens = tokenize_proto(text)
  package = extract_package(tokens)
  ii = find_services(tokens)
  service2rpcs = extract_services(tokens, ii)
  return ProtoDefinition(package, service2rpcs)
