#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -m src.main "$@"
