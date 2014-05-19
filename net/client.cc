bool Client::Connect(const string& to_ip, short to_port) {
  return conn_.Connect(to_ip, to_port, 1024);
}
