set -e
./scripts/curricula -v build tests/assignment
./scripts/curricula -v grade artifacts/assignment/grading/ run artifacts/assignment/solution/ -d reports/ --report
./scripts/curricula -v grade artifacts/assignment/grading/ format artifacts/assignment/grading/report.md reports/*.report.json -d reports/
