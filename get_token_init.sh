#!/bin/bash

set -euo pipefail

curpath=$(dirname "$(realpath $0)")
cd "$curpath"

uv run python -m common.get_token_init

