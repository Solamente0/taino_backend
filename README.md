# Taino Backend Source Code

## Running Partially in Docker

If you want to have the python interpreter on your machine, and only have databases in docker, follow the below steps.

### Setup Databases and Services

Use `docker/services.compose.yml`

```sh
docker compose -f docker/services.compose.yml up
```

### Create .env File 

```sh
mv ./docker/.env.sample ./docker/.env
```

**Don't forget to change services hosts to `localhost` in `.env` file.**

### Install Requirements
 
Install requirements in your virtual environment(venv)

### Install Dependencies

Install `libmagic` from [here](https://github.com/ahupp/python-magic?tab=readme-ov-file#installation)

```sh
python3 -m venv venv
source venv/bin/activate
pip3 install -r requiments.txt 
```

### Run Django Development Server

```sh
python3 manage.py makemigrations
python3 manage.py migrate
python3 runserver 0.0.0.0:8000
```

### Add Countries, Cities, and other initialization data

```sh
python manage.py initialize
```

## Running Completely in Docker

If you are willing to have all services in docker follow the below steps.

### Create .env File

```sh
mv ./docker/.env.sample ./docker/.env
```

### Use `restart_taino` makefile command or `docker compose -f docker/docker-compose.yml up`

```sh
make restart_taino
```

Or

```sh
docker compose -f docker/docker-compose.yml up
```

### Add Countries, Cities, and other initialization data

```sh
python manage.py initialize
```

## Coding Style

**Before pushing any code, Please check out [CONTRIBUTING.md](docs/CONTRIBUTING.md) file.**

## Server Links

+ [Dev Swagger](https://backend-dev.taino.ir/api/schema/swagger/)
+ [Dev Admin](https://front-admin-dev.taino.ir)
+ [Dev CV](https://front-dev.taino.ir/)

+ [Stage Swagger](https://backend-stage.taino.ir/api/schema/swagger/)
+ [Stage Admin](https://front-admin-dev.taino.ir)
+ [Stage CV](https://front-dev.taino.ir/)
+ Default Username/Password: `super_admin@taino.ir/super_admin`
 

