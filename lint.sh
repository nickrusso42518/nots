#!/bin/bash
# File:    lint.sh
# Version: Bash 3.2.57(1)
# Author:  Nicholas Russo (http://njrusmc.net)
# Purpose: First-stage CI check to ensure code is free from defect
#          or common styling errors. It prints out when linting starts
#          and ends, plus the name of each file discovered for linting.
#          Only YAML, Python, and markdown files are supported today.
#
# Return code used to sum the rc from individual lint tests
rc=0
#
echo "YAML linting started"
for f in $(find . -name "*.yml"); do
  # Print the filename, then run 'yamllist' in strict mode
  echo "checking $f"
  yamllint -s $f
  # Sum the rc from yamllint with the sum
  rc=$((rc + $?))
done
echo "YAML linting complete"
#
#
echo "Python linting started"
for f in $(find . -name "*.py"); do
  # Print the filename, then run 'pylint'
  echo "checking $f"
  pylint $f
  # Sum the rc from pylint with the sum
  rc=$((rc + $?))
done
echo "Python linting complete"
#
#
echo "Markdown linting started"
for f in $(find . -name "*.md"); do
  # Print the filename, then run 'markdownlint'
  echo "checking $f"
  markdownlint $f
  # Sum the rc from markdownlint with the sum
  rc=$((rc + $?))
done
echo "Markdown linting complete"
#
# Exit using the total rc computed. 0 means success, any else is failure
echo "All linting complete, rc=$rc"
exit $rc
