.PHONY: install install-dev lint format test data upload clean
install:
	pip install -r requirements.txt
install-dev: install
	pip install pytest pytest-cov black flake8
lint:
	flake8 scripts/ airflow/ tests/ --max-line-length=100 --ignore=E501,W503
	black --check --line-length 100 scripts/ airflow/ tests/
format:
	black --line-length 100 scripts/ airflow/ tests/
test:
	pytest tests/ -v
data:
	python scripts/generate_data.py --customers 200 --products 50 --orders 2000 --out data/
upload:
	for t in customers products orders order_items; do \
		gsutil cp data/$$t.csv gs://$(GCS_ECOMMERCE_BUCKET)/landing/$$t/$$t.csv; \
	done
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/
