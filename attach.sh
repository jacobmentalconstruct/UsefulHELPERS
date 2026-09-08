#!/bin/sh
# Attach a useful-helpers instance to a target directory.
#
# Usage:  sh attach.sh <target-directory>
#
# Run it from anywhere: the cd below makes this release directory the working
# directory, which is what "python -m factory" needs to import the package.

cd "$(dirname "$0")" || exit 1

if [ -z "$1" ]; then
    echo "Usage: sh attach.sh <target-directory>" >&2
    exit 2
fi

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

exec "$PY" -m factory attach "$1"
