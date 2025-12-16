# Taino Production Setup

This directory contains the production configuration for the Taino application.

## Directory Structure

- **backups/**: Database backups
- **certs/**: SSL certificates
- **configs/**: Configuration files for services
- **data/**: Persistent data storage
- **docker/**: Docker configuration files
- **logs/**: Log files
- **metrics/**: Prometheus and Grafana data
- **scripts/**: Utility scripts

## Initial Setup

1. Update the `.env` file with secure passwords and API keys
2. Place SSL certificates in the `certs` directory
3. Run the following command to start the services:

```bash
docker compose -f docker/docker-compose.yml up -d
```

4. Initialize the database:

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py migrate
docker compose -f docker/docker-compose.yml exec api python manage.py initialize
```

5. Create a superuser:

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py createsuperuser
```

## SSL Configuration

Place your SSL certificates in the `certs` directory:
- `certs/fullchain.pem`: Full certificate chain
- `certs/privkey.pem`: Private key

You can use Let's Encrypt to generate certificates.

## ArvanCloud Setup

1. Create a bucket in your ArvanCloud account
2. Update the `ARVAN_*` settings in the `.env` file
3. Make sure the bucket permissions are set correctly

## Backup and Restore

Automated backups run daily at 1:00 AM. Manual backups can be triggered with:

```bash
docker compose -f docker/docker-compose.yml exec backup /usr/local/bin/backup.sh
```

To restore a backup:

```bash
# Restore PostgreSQL
docker compose -f docker/docker-compose.yml exec backup pg_restore -h postgres -U $DB_USER -d $DB_NAME /backups/postgres_TIMESTAMP.dump

# Restore MongoDB
docker compose -f docker/docker-compose.yml exec backup mongorestore --host mongodb --port 27017 --username $MONGO_USER --password $MONGO_PASS --authenticationDatabase admin --gzip --archive=/backups/mongo_TIMESTAMP.gz
```

## Monitoring

Access the monitoring dashboard at https://g-monitor.taino.ir with the credentials set in the `.env` file.

## Maintenance

### Updating the Application

```bash
# Pull the latest code
git pull

# Rebuild and restart the containers
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

### Checking Logs

```bash
docker compose -f docker/docker-compose.yml logs -f [service-name]
```

### Scaling Services

To scale services horizontally:

```bash
docker compose -f docker/docker-compose.yml up -d --scale api=3 --scale chat=2
```

## Security Notes

- Change all default passwords in the `.env` file
- Regularly update SSL certificates
- Keep the system updated with security patches
- Perform regular security audits
