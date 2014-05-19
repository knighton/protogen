#ifndef NET_UTIL_H_
#define NET_UTIL_H_

#include <string>

using std::string;

class NetUtil {
 public:
  static bool GetOwnIpAddress(string* addr_out);

  // Parse "host:port" or just "port" with default host.
  static bool ParseAddress(const string& in, string* host, short* port);
};

#include "util.cc"

#endif  // NET_UTIL_H_
