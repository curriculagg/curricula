void f() {
    int* y = new int[1];
}

int main(int argc, char** argv)
{
    int* x = new int[1];
    f();
    f();
}
