# Data Security Policy

This policy outlines the security standards and practices taken to protect sensitive personal data (Instagram, Youtube, Kindle history) collected from multiple users.

## Data Encryption
### In Transit
All data streaming from the Python pipeline to the PostgreSQL database is  encrypted using TLS via the connection string configuration sslmode=require. Database authentication utilizes SCRAM-SHA-256, meaning raw passwords are never sent over the wire.
### At Rest
Raw source files containing sensitive data are deleted immediately after ingestion, if the ENVIRONMENT is set to production. The resulting database storage volumes use AES-256 block-level encryption.

## Access Control
We employ the Principle of Least Privilege (PoLP) to ensure data can only be accessed by authorized entities.
### Database Access
Database credentials (DB_USER, DB_PASS) are stored securely as environment variables and never hardcoded in application code. Authentication utilizes SCRAM-SHA-256 protocol, ensuring credentials are never transmitted in plain text. Application connections use dedicated database user accounts with minimal required permissions for data ingestion and retrieval operations. Access is limited to the specific user_metrics table and associated data modification operations.
### Network Firewalls
Database network access is restricted to authorized application servers through firewall rules. PostgreSQL connections are limited to the designated application host(s) and port (5432). All incoming database connections require TLS encryption and are denied if sslmode=require is not negotiated.

## Logging and Monitoring
All database connections and authentication events are logged with timestamps and context. There is also security alert functionality implemented.

## Regulatory Compliance
### GDPR
The code includes helper methods for deleting user data, exporting user data, and enforcing a retention policy.