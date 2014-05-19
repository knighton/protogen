#ifndef NET_PROTOCOL_H_
#define NET_PROTOCOL_H_

#include <string>

using std::string;

// Prepend a length uint32 to messages to enable splitting them over an
// arbitrary number of sends/recvs.
//
// Format: "%u%s", data length uint32, data.

enum NetStatus {
  OK = 1,
  HUNG_UP,
  ERROR,
};

// Arbitrary-length send (see format note).
NetStatus ProtocolSend(int sockfd, char* buf, int buf_len,
                       const string& outgoing);

// Arbitrary-length recv (see format note).
NetStatus ProtocolRecv(int sockfd, char* buf, int buf_len, string* incoming);

#include "protocol.cc"

#endif  // NET_PROTOCOL_H_
