#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string>

#include "protocol.h"

using std::string;

Connection::~Connection() {
  Disconnect();
}

void Connection::Disconnect() {
  close(sockfd_);
  if (buf_) {
    delete [] buf_;
    buf_ = NULL;
  }
}

// get sockaddr, IPv4 or IPv6:
void *get_in_addr(struct sockaddr *sa) {
  if (sa->sa_family == AF_INET) {
    return &(((struct sockaddr_in*)sa)->sin_addr);
  }

  return &(((struct sockaddr_in6*)sa)->sin6_addr);
}

bool Connection::Connect(const string& to_ip, short to_port,
                         unsigned buf_len) {
  // Bail if already connected to something.
  if (buf_) {
    return false;
  }

  addrinfo hints, *servinfo, *p;
  int rv;
  char s[INET6_ADDRSTRLEN];

  memset(&hints, 0, sizeof hints);
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;

  char to_port_s[80];
  sprintf(to_port_s, "%hd", to_port);

  if ((rv = getaddrinfo(to_ip.c_str(), to_port_s, &hints, &servinfo)) != 0) {
    fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
    return false;
  }

  // loop through all the results and connect to the first we can
  for (p = servinfo; p != NULL; p = p->ai_next) {
    if ((sockfd_ = socket(p->ai_family, p->ai_socktype,
         p->ai_protocol)) == -1) {
      perror("client: socket");
      continue;
    }

    if (connect(sockfd_, p->ai_addr, p->ai_addrlen) == -1) {
      close(sockfd_);
      perror("client: connect");
      continue;
    }

    break;
  }

  if (p == NULL) {
    fprintf(stderr, "client: failed to connect\n");
    return false;
  }

  inet_ntop(p->ai_family, get_in_addr((sockaddr*)p->ai_addr), s, sizeof s);
  printf("client: connecting to %s\n", s);

  freeaddrinfo(servinfo); // all done with this structure

  // Allocate buffer at the very end.
  buf_ = new char[buf_len];
  buf_len_ = buf_len;
  return true;
}

bool Connection::SendAndReceive(const string& message, string* response) {
  // Bail if not connected to anything.
  if (!buf_) {
    return false;
  }

  NetStatus status = ProtocolSend(sockfd_, buf_, buf_len_, message);
  if (status == HUNG_UP) {
    printf("hungup\n");
  } else if (status == ERROR) {
    perror("Fuck");
  }
  assert(status == OK);

  status = ProtocolRecv(sockfd_, buf_, buf_len_, response);
  assert(status == OK);
  return true;
}
