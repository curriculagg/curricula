#include <iostream>
#include <sstream>

using namespace std;

int main(int argc, char** argv)
{
    string mode(argv[1]);

    istringstream stream(argv[2]);
    int count;
    if (!(stream >> count)) {
      cerr << "Invalid number: " << argv[1] << endl;
    } else if (!stream.eof()) {
      cerr << "Trailing characters after number: " << argv[1] << endl;
    }

    int match = 0;

    if (mode == "linear") {
        for (int i = 0; i < count; ++i) {
            ++match;
        }
    }

    cout << match << endl;
}
