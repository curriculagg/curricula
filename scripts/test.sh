set -e

# Build directory
build=/tmp/assignment

# Build artifacts, set access control
rm -rf "$build"
./scripts/curricula -v build tests/assignment --destination "$build"
chmod -R go-wrx /tmp/assignment/grading

# Grade and format
./scripts/curricula -v grade "$build"/grading/ run "$build"/solution/ -d reports/ --report
./scripts/curricula -v grade "$build"/grading/ format "$build"/grading/report.md reports/*.report.json -d reports/
