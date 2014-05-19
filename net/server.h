#ifndef NET_SERVER_H_
#define NET_SERVER_H_

#include <string>
#include "../base/closure.h"

using std::string;

// A simple select server, originally based on:
//
//   http://beej.us/guide/bgnet/output/html/multipage/clientserver.html
//   http://beej.us/guide/bgnet/output/html/multipage/advanced.html
//
// It communicates using messages prepended with a length u32 (protocol.h).
//
// For each message, it calls the following function on the payload and returns
// the response to the caller:
//
//   bool Server::Handle(const string& input, string* response);
//
// (If Handle() returns false, the server will shut down.)
//
// Calls on_ready_ when ready to serve, and on_shutdown_ when stopping serving.

class Server {
 public:
  // Basic constructor/destructor.
  Server() : port_(0), on_ready_(NULL), on_shutdown_(NULL), buf_len_(0),
             buf_(NULL) {}
  virtual ~Server();

  // Accessors.
  const string& service_name() const { return service_name_; }
  const string& host() const { return host_; }
  short port() const { return port_; }

  // Init, can fail.
  bool Init(const string& service_name, short port, Closure* on_ready,
            Closure* on_shutdown, unsigned buf_len);

  // Enter the serve loop.  Calls on_ready_, on_shutdown_.
  // Returns false on error, calls shutdown callback if called ready.
  bool Loop();

  // Called to statelessly respond to each input.
  // If returns false, the server will shut down.
  virtual bool Handle(const string& request, string* response) { return true; }

 private:
  string service_name_;
  string host_;
  short port_;

  // The closures are called once if ever and are expected to delete themselves.
  Closure* on_ready_;
  Closure* on_shutdown_;

  unsigned buf_len_;
  char* buf_;
};

#include "server.cc"

#endif  // NET_SERVER_H_
