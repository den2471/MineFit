CREATE USER worker WITH LOGIN;
GRANT SELECT ON versions, invalid_versions TO worker;

CREATE USER requester WITH LOGIN;
GRANT INSERT ON versions, invalid_versions TO requester;

GRANT USAGE ON SCHEMA public TO worker, requester;