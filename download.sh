#!/usr/bin/env bash
# Fetch every dataset for Spain and its communities.
cd "$(dirname "$0")"
exec python3 -m mery download spain
