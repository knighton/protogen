#include <cassert>
#include <string>

using std::string;

NetStatus ProtocolSend(int sockfd, char* buf, int buf_len,
                       const string& outgoing) {
  int net_len = htonl(sizeof(uint32_t) + outgoing.size());

  int n = send(sockfd, &net_len, sizeof(net_len), 0);
  if (n < 0) {
    return ERROR;
  } else if (n == 0) {
    return HUNG_UP;
  } else {
    assert(n == sizeof(net_len));  // Expect buffers >= 4 bytes long.
  }

  unsigned total = 0;
  while (total < outgoing.size()) {
    n = send(sockfd, outgoing.data() + total, outgoing.size() - total, 0);
    if (n < 0) {
      return ERROR;
    } else if (n == 0) {
      return HUNG_UP;
    } else {
      total += n;
    }
  }
  assert(total == outgoing.size());
  return OK;
}

NetStatus ProtocolRecv(int sockfd, char* buf, int buf_len, string* incoming) {
  int total_len;
  int n = recv(sockfd, &total_len, sizeof(total_len), 0);
  if (n < 0) {
    return ERROR;
  } else if (n == 0) {
    return HUNG_UP;
  } else {
    assert(n == 4);  // Expect buffers >= 4 bytes long.
  }

  total_len = ntohl(total_len);
  unsigned len_need = total_len - sizeof(total_len);

  incoming->clear();
  incoming->reserve(len_need);
  while (incoming->size() < len_need) {
    n = recv(sockfd, buf, buf_len, 0);
    if (n < 0) {
      return ERROR;
    } else if (n == 0) {
      return HUNG_UP;
    } else {
      incoming->append(buf, n);
    }
  }
  assert(len_need == incoming->size());
  return OK;
}
