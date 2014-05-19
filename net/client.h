#ifndef NET_CLIENT_H_
#define NET_CLIENT_H_

#include <string>
#include "connection.h"

using std::string;

// Protocol buffer service clients subclass this.
class Client {
 public:
  virtual bool Connect(const string& to_ip, short to_port);

 protected:
  Connection conn_;
};

#include "client.cc"

#endif  // NET_CLIENT_H_
