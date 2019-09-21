LLVM_URL="https://github.com/llvm/llvm-project/releases/download/llvmorg-8.0.1/llvm-8.0.1.src.tar.xz"
CFE_URL="https://github.com/llvm/llvm-project/releases/download/llvmorg-8.0.1/cfe-8.0.1.src.tar.xz"
CLANG_TOOLS_EXTRA_URL="https://github.com/llvm/llvm-project/releases/download/llvmorg-8.0.1/clang-tools-extra-8.0.1.src.tar.xz"

LLVM_ARCHIVE=${LLVM_URL##*/}
CFE_ARCHIVE=${CFE_URL##*/}
CLANG_TOOLS_EXTRA_ARCHIVE=${CLANG_TOOLS_EXTRA_URL##*/}

LLVM_DIRECTORY=${LLVM_ARCHIVE%%.tar.xz}
CFE_DIRECTORY=${CFE_ARCHIVE%%.tar.xz}
CLANG_TOOLS_EXTRA_DIRECTORY=${CLANG_TOOLS_EXTRA_ARCHIVE%%.tar.xz}

function download() {
  if [[ ! -d $3 ]]; then
    if [[ ! -f $2 ]]; then
      wget "$1"
    fi
    tar -xf "$2"
  fi
}

cd /tmp || exit 1

download "$LLVM_URL" "$LLVM_ARCHIVE" "$LLVM_DIRECTORY"
cd $LLVM_DIRECTORY/tools || exit 1
download "$CFE_URL" "$CFE_ARCHIVE" "$CFE_DIRECTORY"
cd $CFE_DIRECTORY/tools || exit 1
download "$CLANG_TOOLS_EXTRA_URL" "$CLANG_TOOLS_EXTRA_ARCHIVE" "$CLANG_TOOLS_EXTRA_DIRECTORY"
