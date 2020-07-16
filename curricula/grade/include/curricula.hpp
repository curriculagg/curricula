#ifndef CURRICULA_HPP
#define CURRICULA_HPP

#include <cstring>
#include <iostream>

#define PASS return 0;
#define FAIL return 1;

#define EXPECT_TRUE(condition) if (!(condition)) { std::cerr << "failed on line " << __LINE__ << std::endl; FAIL; }
#define EXPECT_FALSE(condition) if (condition) { std::cerr << "failed on line " << __LINE__ << std::endl; FAIL; }
#define EXPECT_EQUAL(left, right) if ((left) != (right)) { std::cerr << "failed on line " << __LINE__ << std::endl; FAIL; }
#define EXPECT_UNEQUAL(left, right) if ((left) == (right)) { std::cerr << "failed on line " << __LINE__ << std::endl; FAIL; }
#define EXPECT_THROW(statement)\
{\
    bool caught = false;\
    try { statement; } catch (...) { caught = true; }\
    if (!caught) { std::cerr << "failed on line " << __LINE__ << std::endl; FAIL; }\
}

#define TEST(name) if (strcmp(argv[1], #name) == 0)

#define TESTS_BEGIN \
int main(int argc, char** argv)\
{\
    if (argc < 2)\
    {\
        return 3;\
    }\

#define TESTS_END \
    return 2;\
}

#endif
