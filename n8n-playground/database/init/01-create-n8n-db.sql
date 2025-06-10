-- Create the n8n database that n8n service expects
CREATE DATABASE n8n;

-- Grant all privileges to postgres user on n8n database
GRANT ALL PRIVILEGES ON DATABASE n8n TO postgres;