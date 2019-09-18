#include <iostream>
#include <string>

using namespace std;

int main(int argc, char** argv)
{
    if (argc == 1) {
        return -1;
    }

    cout << argv[1] << endl;
}
