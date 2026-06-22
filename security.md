# Data Security Policy

This policy outlines the security standards and practices taken to protect sensitive personal data (Instagram, Youtube, Kindle history) collected from multiple users.

## Data Encryption
### In Transit
All data streaming from the Python pipeline to the PostgreSQL database is  encrypted using TLS via the connection string configuration sslmode=require. Database authentication utilizes SCRAM-SHA-256, meaning raw passwords are never sent over the wire.
### At Rest
Raw source files containing sensitive data are deleted immediately after ingestion. The resulting database storage volumes use AES-256 block-level encryption.

## Access Control
We employ the Principle of Least Privilege (PoLP) to ensure data can only be accessed by authorized entities.
### Database Access
### Network Firewalls

## Backups

## Logging and monitoring

## Regulatory Compliance
### GDPR
### ISO
