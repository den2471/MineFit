\c vault;

CREATE TABLE IF NOT EXISTS versions (
    id text PRIMARY KEY,
    name text,
    dependencies jsonb,
    game_versions jsonb,
    version_type text,
    loaders jsonb,
    status text,
    date_published timestamptz,
    project_id text
);

CREATE TABLE IF NOT EXISTS invalid_versions (
    id text PRIMARY KEY,
    project_id text
);