#!/usr/bin/env bash

# Install the package.
python setup.py install

ACTUAL_OUTPUT="$(pysyncdroid 2>&1)"
EXPECTED_OUTPUT="usage: pysyncdroid [-h] -V VENDOR -M MODEL [-s SOURCE] [-d DESTINATION]
                   [-f FILE] [-v] [-u {ignore,remove,synchronize}] [-o]
                   [-i IGNORE_FILE_TYPE [IGNORE_FILE_TYPE ...]]
pysyncdroid: error: the following arguments are required: -V/--vendor, -M/--model"

if [ "$ACTUAL_OUTPUT" != "$EXPECTED_OUTPUT" ]
then
  echo "Unexpected 'pysyncdroid' output"
  exit 1
fi
