#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>
#include <unistd.h>
#include "protocol.h"
#include "util.h"

#define DEFAULT_SS_BUF_LEN 1024

// get sockaddr, IPv4 or IPv6:
void *get_inet_addr(sockaddr *sa) {
  if (sa->sa_family == AF_INET) {
    return &(((sockaddr_in*)sa)->sin_addr);
  }
  return &(((sockaddr_in6*)sa)->sin6_addr);
}

Server::~Server() {
  buf_len_ = 0;
  if (buf_) {
    delete [] buf_;
    buf_ = NULL;
  }
}

bool Server::Init(const string& service_name, short port, Closure* on_ready,
                  Closure* on_shutdown, unsigned buf_len=DEFAULT_SS_BUF_LEN) {
  service_name_ = service_name;
  if (!NetUtil::GetOwnIpAddress(&host_)) {
    return false;
  }
  port_ = port;

  on_ready_ = on_ready;
  on_shutdown = on_shutdown;

  buf_len_ = buf_len;
  buf_ = new char[buf_len];
  return true;
}

bool Server::Loop() {
  char port_str[80];
  sprintf(port_str, "%hd", port_);

  fd_set master;     // master file descriptor list
  fd_set read_fds;   // temp file descriptor list for select()
  int fdmax;         // maximum file descriptor number

  int listener;      // listening socket descriptor
  int newfd;         // newly accept()ed socket descriptor
  struct sockaddr_storage remoteaddr; // client address
  socklen_t addrlen;

  char remoteIP[INET6_ADDRSTRLEN];

  int yes = 1;       // for setsockopt() SO_REUSEADDR, below
  int i, rv;

  struct addrinfo hints, *ai, *p;

  FD_ZERO(&master);  // clear the master and temp sets
  FD_ZERO(&read_fds);

  // get us a socket and bind it
  memset(&hints, 0, sizeof hints);
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_flags = AI_PASSIVE;
  if ((rv = getaddrinfo(NULL, port_str, &hints, &ai)) != 0) {
    fprintf(stderr, "selectserver: %s\n", gai_strerror(rv));
    return false;
  }

  for (p = ai; p != NULL; p = p->ai_next) {
    listener = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
    if (listener < 0) {
      continue;
    }

    // lose the pesky "address already in use" error message
    setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int));

    if (bind(listener, p->ai_addr, p->ai_addrlen) < 0) {
      close(listener);
      continue;
    }

    break;
  }

  // if we got here, it means we didn't get bound
  if (p == NULL) {
    fprintf(stderr, "selectserver: failed to bind\n");
    return false;
  }

  freeaddrinfo(ai);  // all done with this

  // listen
  if (listen(listener, 10) == -1) {
    perror("listen");
    return false;
  }

  // add the listener to the master set
  FD_SET(listener, &master);

  // keep track of the biggest file descriptor
  fdmax = listener;  // so far, it's this one

  if (on_ready_) {
    on_ready_->Run();
  }

  // main loop
  while (true) {
    read_fds = master;  // copy it
    if (select(fdmax + 1, &read_fds, NULL, NULL, NULL) == -1) {
      perror("select");
      if (on_shutdown_) {
        on_shutdown_->Run();
      }
      return false;
    }

    // run through the existing connections looking for data to read
    for (i = 0; i <= fdmax; i++) {
      if (FD_ISSET(i, &read_fds)) {  // we got one!!
        if (i == listener) {
          // handle new connections
          addrlen = sizeof remoteaddr;
          newfd = accept(listener, (sockaddr*)&remoteaddr, &addrlen);

          if (newfd == -1) {
            perror("accept");
          } else {
            FD_SET(newfd, &master);  // add to master set
            if (newfd > fdmax) {     // keep track of the max
              fdmax = newfd;
            }
            printf("selectserver: new connection from %s on socket %d\n",
                   inet_ntop(remoteaddr.ss_family,
                             get_inet_addr((sockaddr*)&remoteaddr), remoteIP,
                             INET6_ADDRSTRLEN),
                   newfd);
          }
        } else {
          string message_in;
          // handle data from a client
          NetStatus status = ProtocolRecv(i, buf_, buf_len_, &message_in);
          if (status != OK) {
            // got error or connection closed by client
            if (status == HUNG_UP) {
              // connection closed
              printf("selectserver: socket %d hung up\n", i);
            } else if (status == ERROR) {
              perror("recv:133");
            } else {
              assert(false);
            }
            close(i);  // bye!
            FD_CLR(i, &master);  // remove from master set
          } else {
            string message_out;
            bool keep_going = Handle(message_in, &message_out);
            status = ProtocolSend(i, buf_, buf_len_, message_out);
            assert(status == OK);
            if (!keep_going) {
              goto shutdown;
            }
          }
        }
      }
    }
  }

shutdown:
  if (on_shutdown_) {
    on_shutdown_->Run();
  }
  return true;
}
