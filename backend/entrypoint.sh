#!/usr/bin/env bash
set -eo pipefail

alembic upgrade head

exec "$@"
