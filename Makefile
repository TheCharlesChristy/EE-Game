.PHONY: backend-test frontend-test frontend-build firmware-build release smoke

backend-test:
	cd host/backend && pytest

frontend-test:
	cd host/frontend && npm test

frontend-build:
	cd host/frontend && npm run build

firmware-build:
	cd firmware && pio run -e esp32_arduino

release:
	./scripts/build-release.sh

smoke:
	./scripts/smoke-test.sh
