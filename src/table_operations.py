from aiopg.sa import create_engine


class TableOperations(object):
    def __init__(self):
        self.engine = None
        self.init_scripts = [
            """DROP TABLE IF EXISTS logs""",
            """DROP TABLE IF EXISTS account""",
            """DROP TABLE IF EXISTS proxy_id_joke""",
            """DROP TABLE IF EXISTS account_joke""",
            """DROP TABLE IF EXISTS joke""",
            """CREATE OR REPLACE FUNCTION random_between(low INT ,high INT) RETURNS INT AS
               $$
               BEGIN
                  RETURN floor(random()* (high-low + 1) + low);
               END;
               $$ language 'plpgsql' STRICT;""",
            """create table account (
                 id    serial                                               not null
                   constraint account_pk
                     primary key,
                 login text                                                 not null,
                 key   integer default random_between(100000000, 999999999) not null
               );
               alter table account
                 owner to postgres;
               create unique index account_key_uindex
                 on account (key);
        """,
            """create table joke (
                id             serial not null
                  constraint joke_pk
                    primary key,
                text           text    default ''::text
              );
              alter table joke
                owner to postgres;
              create unique index joke_text_uindex
                on joke (text);""",
            """create table account_joke (
                 fake_joke_id integer,
                 joke_id      integer
                   constraint proxy_id_joke_joke_id_fk
                     references joke
                     on delete cascade,
                 account_id   integer,
                 constraint proxy_id_joke_pk
                   unique (joke_id, account_id)
               );
               alter table account_joke
                 owner to postgres;
               create index proxy_id_joke_fake_joke_id_fake_joke_id_index
                 on account_joke (fake_joke_id, fake_joke_id);""",
            """create table logs (
               key          integer,
               ip_address   text,
               request_time timestamp default now(),
               id           serial not null
                 constraint logs_pk
                   primary key,
               data     json      default '{}'::json
             );
             alter table logs
               owner to postgres;
        """,
            """CREATE OR REPLACE FUNCTION remove_joke() returns trigger
                 language plpgsql
               as
               $$
               BEGIN
                 DELETE
                 FROM joke
                 WHERE joke.id = OLD.joke_id
                   AND NOT EXISTS(
                     SELECT * FROM account_joke WHERE account_joke.joke_id = OLD.joke_id
                   );
                   RETURN OLD;
               END;
               $$;""",
            """CREATE TRIGGER remove_joke_trigger
               AFTER INSERT OR UPDATE OR DELETE  
               ON account_joke
               FOR EACH ROW EXECUTE PROCEDURE remove_joke();""",
        ]
        self.insert_to_logs = """INSERT INTO logs (id, key, ip_address, request_time, data)
                                 VALUES  (DEFAULT,  %s, %s, DEFAULT, %s)
                                 RETURNING id;"""
        self.insert_to_account = """INSERT INTO account (id, login, key)
                                    VALUES (DEFAULT, %s, DEFAULT)
                                    RETURNING *;"""
        self.select_from_account = """SELECT * FROM account WHERE account.key = {account_key}"""
        self.insert_to_joke = """INSERT INTO joke (id, text) 
                                     VALUES (DEFAULT, %s)
                                 ON CONFLICT (text) DO UPDATE SET text = EXCLUDED.text
                                 RETURNING id;"""
        self.delete_joke = """
                with data as (
                  SELECT fake_joke_id, account_joke.joke_id, account.id
                  FROM account
                         JOIN account_joke ON account_joke.account_id = account.id
                         JOIN joke j on account_joke.joke_id = j.id
                  WHERE account.key = {account_key}
                    AND fake_joke_id = {fake_joke_id}
                )
                DELETE FROM account_joke
                  USING data
                  WHERE account_joke.account_id = data.id
                    AND account_joke.joke_id = data.joke_id
                  RETURNING account_joke.fake_joke_id;
              """
        self.select_from_joke = """SELECT fake_joke_id AS joke_id
                                        , text 
                                   FROM account
                                       JOIN account_joke ON account_joke.account_id = account.id
                                       JOIN joke j on account_joke.joke_id = j.id
                                   WHERE account.key = {account_key}"""
        self.insert_to_account_joke = """WITH previos_joke AS (
                                              SELECT fake_joke_id AS id
                                              FROM account_joke
                                                     JOIN account ON account_joke.account_id = account.id
                                              WHERE account.key = {account_key}
                                              ORDER BY fake_joke_id DESC
                                              LIMIT 1 ), 
                                              data AS (
                                        SELECT coalesce((SELECT id FROM previos_joke), 0) AS previos_fake_joke_id
                                       ,(SELECT id FROM account WHERE key = {account_key}) AS account_id)
                                       INSERT
                                       INTO account_joke (fake_joke_id, joke_id, account_id)
                                       SELECT previos_fake_joke_id + 1, {joke_id}, data.account_id
                                       FROM data
                                       ON CONFLICT (joke_id, account_id)
                                       DO UPDATE SET account_id = EXCLUDED.account_id
                                       RETURNING fake_joke_id;"""
        self.update_to_account_joke = """UPDATE account_joke
                                         SET joke_id = {joke_id}
                                         FROM account
                                         WHERE account.key = {account_key}
                                           AND account_joke.account_id = account.id
                                           AND account_joke.fake_joke_id = {fake_joke_id}
                                           AND NOT EXISTS(SELECT * FROM account_joke
                                                            JOIN account ON account_joke.account_id = account.id
                                                     WHERE account.key = {account_key} AND joke_id={joke_id})
                                           RETURNING *"""

    async def init(self):
        self.engine = await create_engine(
            database="postgres",
            user="postgres",
            password="",
            host="postgres",
            port="5432",
        )
        await self.__setup_database()

    async def __setup_database(self):
        async with self.engine.acquire() as conn:
            for script in self.init_scripts:
                await conn.execute(script)

    async def base(self):
        async with self.engine.acquire() as conn:
            await conn.close()

    async def execute(self, query, params=None, tuple_params=()):
        params = params or {}
        returned_value = []
        async with self.engine.acquire() as conn:
            async for row in conn.execute(query.format(**params), tuple_params):
                returned_value.append(dict(row))

        return returned_value

    async def exec_and_get(self, get_key, **kwargs):
        values_list = await self.execute(**kwargs)
        return values_list and values_list[0].get(get_key)
