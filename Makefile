db_run:
	docker run --name postgres_db -p 5432:5432 -d postgres

test_run:
	python3 -m src.tests.runner