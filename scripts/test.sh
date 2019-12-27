set -e
./scripts/curricula.sh build tests/assignment
./scripts/curricula.sh grade artifacts/assignment/grading/ run artifacts/assignment/solution/ -f reports/assignment.report.json --report
./scripts/curricula.sh grade artifacts/assignment/grading/ format artifacts/assignment/grading/report.md reports/assignment.report.json -d reports
