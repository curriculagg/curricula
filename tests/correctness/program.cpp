#include <iostream>
#include <string>

using namespace std;

int main(int argc, char** argv)
{
    if (argc == 1)
    {
        return -1;
    }

    // Typical correctness conditions
    if (strcmp(argv[1], "pass") == 0 || strcmp(argv[1], "fail") == 0)
    {
        cout << argv[1];
        if (argc > 2) cout << " " << argv[2];
        cout << endl;
        return 0;
    }

    // Actual runtime error
    if (strcmp(argv[1], "error") == 0)
    {
        throw "error";
    }

    // Segmentation fault
    if (strcmp(argv[1], "fault") == 0)
    {
        int *a = NULL;
        return *a;
    }

    // Hang
    if (strcmp(argv[1], "hang") == 0)
    {
        while (true);
    }
}
