class ResponseBody(object):
    def __init__(self):
        self.constant_data = {"result": None, "error": None}

    def error(self, data):
        body = {}
        body.update(self.constant_data)
        body["error"] = data
        return body

    def result(self, data):
        body = {}
        body.update(self.constant_data)
        body["result"] = data
        return body


SQL_SQRIPTS = [
    "DROP TABLE IF EXISTS logs",
    "DROP TABLE IF EXISTS account",
    "DROP TABLE IF EXISTS joke",
    """CREATE OR REPLACE FUNCTION random_between(low INT ,high INT) RETURNS INT AS
                      $$
                      BEGIN
                         RETURN floor(random()* (high-low + 1) + low);
                      END;
                      $$ language 'plpgsql' STRICT;
                      """,
    """create table account
                      (
                          id    serial                                               not null
                              constraint account_pk
                                  primary key,
                          login text                                                 not null,
                          key   integer default random_between(100000000, 999999999) not null,
                          jokes integer[]
                      );
                      alter table account
                          owner to postgres;
                      create unique index account_key_uindex
                          on account (key);
                            """,
    """create table joke
                      (
                          id   serial not null
                              constraint joke_pk
                                  primary key,
                          text text default ''::text,
                          number_of_uses int default 1
                      );
                      alter table joke
                          owner to postgres;
                      create unique index joke_text_uindex
                          on joke (text);
                          """,
    """create table logs (
                        key          integer,
                        ip_address   text,
                        request_time timestamp default now(),
                        id           serial not null
                          constraint logs_pk
                            primary key
                      );
                      alter table logs
                        owner to postgres;
                      """,
    """CREATE OR REPLACE FUNCTION array_unique (ANYARRAY) RETURNS ANYARRAY
                      LANGUAGE SQL
                      AS $body$
                        SELECT array(SELECT DISTINCT UNNEST($1)) ;
                      $body$;""",
]
