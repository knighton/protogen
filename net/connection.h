#ifndef NET_CONNECTION_H_
#define NET_CONNECTION_H_

#include <string>

using std::string;

// Encapsulates sending and receiving with a foreign port.
//
// Uses the message format in protocol.h.

class Connection {
 public:
  Connection() : sockfd_(~0), buf_(NULL), buf_len_(0) { }

  // Disconnects.
  ~Connection();

  // Set up a connection to another service.
  bool Connect(const string& to_ip, short to_port, unsigned buf_len);

  // Send a message to the other service and get their response (blocking).
  bool SendAndReceive(const string& message, string* response);

  // Disconnect from other service, free resources.
  void Disconnect();

 private:
  int sockfd_;
  char* buf_;
  int buf_len_;
};

#include "connection.cc"

#endif  // NET_CONNECTION_H_
