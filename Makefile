db_run:
	docker run --name postgres_db -p 5431:5432 -d postgres

login:
	curl -X POST 0.0.0.0:9996/do_login -d '{"login": "gomonuk"}'

bad_login:
	curl -X POST 0.0.0.0:9996/do_login -d '{"login": ""}'