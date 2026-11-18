test:
	pytest

test-fast:
	pytest --no-cov -q

# Regenerate the committed OpenAPI spec from code (no running service needed).
# CI (test.yml) fails when openapi.json drifts from the code.
openapi:
	docker run --rm -v "$(CURDIR):/app" -w /app python:3.12-slim sh -c \
	  "pip install -q -r requirements.txt && python scripts/export_openapi.py app.main:app openapi.json"

.PHONY: test test-fast openapi
