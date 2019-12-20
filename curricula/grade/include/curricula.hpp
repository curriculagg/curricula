#include <vector>
#include <string>
#include <functional>

#define EXPECT_TRUE(condition) if (!condition) { return 1; }
#define EXPECT_FALSE(condition) if (condition) { return 1; }
#define EXPECT_EQUAL(left, right) if (left != right) { return 1; }
#define EXPECT_UNEQUAL(left, right) if (left == right) { return 1; }
#define EXPECT_THROW(statement)\
{\
    bool caught = false;\
    try { statement; } catch (...) { caught = true; }\
    if (!caught) { return 1; }\
}

#define TEST(name) if (strcmp(argv[1], "test_" #name) == 0)

#define HARNESS_BEGIN \
int main(int argc, char** argv)\
{\
    if (argc < 2)\
    {\
        return 1;\
    }\

#define HARNESS_END \
    return 1;\
}
