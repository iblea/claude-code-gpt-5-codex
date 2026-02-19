#!/bin/bash

set -euo pipefail

cd "$(dirname "$(realpath "$0")")"

uv run python -m common.refresh
