build:
	docker build \
		-t c2dhunilu/journal-of-digital-history-backend \
		--build-arg GIT_TAG=$(shell git describe --tags) \
		--build-arg GIT_BRANCH=$(shell git rev-parse --abbrev-ref HEAD) \
		--build-arg GIT_REVISION=$(shell git rev-parse --short HEAD) .