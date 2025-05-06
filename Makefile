BUILD_TAG ?= latest

run-dev:
	GIT_TAG=$(shell git describe --tags) \
	GIT_BRANCH=$(shell git rev-parse --abbrev-ref HEAD) \
	GIT_REVISION=$(shell git rev-parse --short HEAD) \
	pipenv run ./manage.py runserver 8889

build-docker-image:
	docker buildx build \
		--platform=linux/amd64 \
		-t c2dhunilu/journal-of-digital-history-backend:${BUILD_TAG} \
		--push \
		--build-arg GIT_TAG=$(shell git describe --tags) \
		--build-arg GIT_BRANCH=$(shell git rev-parse --abbrev-ref HEAD) \
		--build-arg GIT_REVISION=$(shell git rev-parse --short HEAD) .
