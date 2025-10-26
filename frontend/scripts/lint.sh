#!/usr/bin/env bash

set -e
# set -x

cd "$(dirname "$0")/.."

# Ensure we're using the correct Node version
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20.19.2

yarn lint:check
yarn type-check
