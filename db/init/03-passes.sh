#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname vault <<-EOSQL
    ALTER ROLE worker WITH PASSWORD '$WORKER_PASS';
    ALTER ROLE requester WITH PASSWORD '$REQUESTER_PASS';
EOSQL