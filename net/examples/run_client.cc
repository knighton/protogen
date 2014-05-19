#include <cassert>
#include <string>
#include "../connection.h"

using std::string;

int main() {
  Connection conn;
  assert(conn.Connect("localhost", 1337, 1024));

  string in = "what the fuck are you doing?";
  string out;
  assert(conn.SendAndReceive(in, &out));
  printf("got = [%s]\n", out.c_str());

  in = out;
  assert(conn.SendAndReceive(in, &out));
  printf("got = [%s]\n", out.c_str());
}
