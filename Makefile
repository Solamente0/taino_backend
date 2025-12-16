
restart_dev:
	echo "Restarting Taino ..."
	docker compose -p taino_back -f docker/docker-compose.yml down && docker compose -p taino_back -f docker/docker-compose.yml up -d

restart_prod:
	echo "Restarting Taino ..."
	cp -rp docker/production/docker/entrypoint.sh docker/entrypoint.sh
	cp -rp docker/production/docker/entrypoint.sh docker/production/scripts/entrypoint.sh
	cp -rp docker/production/.env docker/
	cp -rp docker/production/.env docker/production/docker/
	docker compose -p taino_prod -f docker/production/docker/docker-compose.yml down  && docker compose -p taino_prod -f docker/production/docker/docker-compose.yml up -d

log_taino:
	echo "Logs ..."
	docker compose -p taino_back -f docker/docker-compose.yml logs -f

build_backend:
	echo "Building ..."
	docker build -t taino_api:latest  -f docker/Dockerfile ./
	docker build -t taino_celery:latest  -f docker/celery.Dockerfile ./
	echo "Building Backend Done."

push_develop:
	echo "Pushing to Develop ..."
	git add . && git commit -m "update" && git push origin develop
	git push origin develop
	echo "Pushing Done."

push_stage:
	echo "Pushing to Stage ..."
	git add . && git commit -m "update" && git push origin develop:stage
	git push origin develop:stage
	echo "Pushing Done."

push_main:
	echo "Pushing to Main ..."
	git push origin develop:main
	echo "Pushing Done."


push_all:
	echo "Pushing to All ..."
	git add .
	@read -p "Enter commit message: " message; \
	git commit -m "$$message"
	git push origin develop
	git push origin develop:stage
	git push origin develop:main
	git push devServer develop
	echo "Pushing Done."

push_production:
	echo "Pushing to production ..."
	git push prodServer develop:main
	echo "Pushing Done."

