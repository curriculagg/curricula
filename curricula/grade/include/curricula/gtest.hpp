#ifndef CURRICULA_GTEST_MAIN
#define CURRICULA_GTEST_MAIN

#include <iostream>
#include "gtest/gtest.h"

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Expected test name!" << endl;
        return -1;
    }

    argc = 1;

    ::testing::GTEST_FLAG(filter) = argv[1];
    ::testing::InitGoogleTest(&argc, argv);
    int result = RUN_ALL_TESTS();

    if (result != 0) {
        return result;
    } else if (::testing::Test::HasFailure()) {
        return 1;
    } else {
        return 0;
    }
}

#endif
