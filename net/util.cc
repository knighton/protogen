#include <stdio.h>
#include <sys/types.h>
#include <ifaddrs.h>
#include <netinet/in.h>
#include <string.h>
#include <arpa/inet.h>
#include <string>
#include "../base/string_util.h"

using std::string;

bool NetUtil::GetOwnIpAddress(string* out_addr) {
  ifaddrs* addrs = NULL;
  ifaddrs* a = NULL;

  getifaddrs(&addrs);

  for (a = addrs; a != NULL; a = a->ifa_next) {
    if (a->ifa_addr->sa_family == AF_INET) {  // if IPv4
      void* p = &((sockaddr_in*)a->ifa_addr)->sin_addr;
      char buf[INET_ADDRSTRLEN];
      inet_ntop(AF_INET, p, buf, INET_ADDRSTRLEN);
      if (StringUtil::BeginsWith(buf, "192.168.")) {
        *out_addr = buf;
        break;
      }
    }
  }
  if (addrs) {
    freeifaddrs(addrs);
  }
  if (out_addr->empty()) {
    *out_addr = "localhost";
  }
  return !out_addr->empty();
}

// Parse "host:port" or just "port" with default host = "localhost".
bool NetUtil::ParseAddress(const string& in, string* host, short* port) {
  int x = in.find(':');
  if (x == -1) {
    if (!NetUtil::GetOwnIpAddress(host)) {
      return false;
    }
    if (!StringUtil::ToInt(in, port)) {
      return false;
    }
  } else {
    *host = in.substr(0, x);
    if (!StringUtil::ToInt(in.substr(x + 1), port)) {
      return false;
    }
  }
  return true;
}
