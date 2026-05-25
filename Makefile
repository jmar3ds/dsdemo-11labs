.PHONY: demo demo_prereqs test clean mock

demo: demo_prereqs
	@python3 -m src.run_demo

demo_prereqs:
	@curl -sf http://127.0.0.1:8000/health > /dev/null || (echo "Mock backend not running. Start with: make mock" && exit 1)

test:
	@python3 -m pytest tests/ -v || [ $$? -eq 5 ]

mock:
	@python3 -m mock_backend.server

clean:
	@rm -rf outputs/convai_demo __pycache__ .pytest_cache
	@find . -name "*.pyc" -delete
