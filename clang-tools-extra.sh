git clone --depth 1 https://github.com/llvm/llvm-project.git
cd llvm-project || exit 1

mkdir build
cd build || exit 1

cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLLVM_ENABLE_PROJECTS="clang-tools-extra" ../llvm
make install-clang-tidy
