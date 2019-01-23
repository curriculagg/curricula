#include <chrono>
#include <iostream>
#include <string>

using namespace std;

int main(int argc, char** argv) {
  double seconds = 1;
  if (argc > 1) {
    string arg(argv[1]);
    seconds = stod(arg);
  }
  chrono::steady_clock::time_point begin = chrono::steady_clock::now();
  while (chrono::duration_cast<chrono::seconds>(chrono::steady_clock::now() - begin).count() < seconds);
  return 0;
}
