#include <cassert>
#include "../server.h"

class DemoServer : public Server {
 public:
  bool Handle(const string& input, string* response) {
    *response = string("<<<") + input + ">>>";
    return true;
  }
};

int main() {
  DemoServer serv;
  assert(serv.Init("stupid_service", 1337, NULL, NULL));
  serv.Loop();
}
