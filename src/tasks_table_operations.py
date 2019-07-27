from aiopg.sa import create_engine
import sqlalchemy as sa


metadata = sa.MetaData()

account = sa.Table("account", metadata,
                   sa.Column("id", sa.Integer, primary_key=True),
                   sa.Column("login", sa.String(255)),
                   sa.Column("key", sa.String(255)),
                   sa.Column("jokes", sa.ARRAY(sa.Integer))
                   )

joke = sa.Table("joke", metadata,
                sa.Column("id", sa.Integer, primary_key=True),
                sa.Column("text", sa.String(255)))


class TasksTableOperations(object):
    def __init__(self):
        self.engine = None

    async def init(self):
        self.engine = await create_engine(
            database="postgres",
            user="postgres",
            password="",
            host="localhost",
            port="5433",
        )
        await self.__create_tables()

    async def __create_tables(self):
        async with self.engine.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS logs")
            await conn.execute("DROP TABLE IF EXISTS account")
            await conn.execute("DROP TABLE IF EXISTS joke")
            await conn.execute("""CREATE OR REPLACE FUNCTION random_between(low INT ,high INT) RETURNS INT AS
                                  $$
                                  BEGIN
                                     RETURN floor(random()* (high-low + 1) + low);
                                  END;
                                  $$ language 'plpgsql' STRICT;
                                  
                                  """)
            await conn.execute("""create table account
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
                                        """)
            await conn.execute('''create table joke
                                  (
                                      id   serial not null
                                          constraint joke_pk
                                              primary key,
                                      text text default ''::text
                                  );
                                  alter table joke
                                      owner to postgres;
                                  create unique index joke_text_uindex
                                      on joke (text);
                                      ''')

    async def do_login(self, login):
        async with self.engine.acquire() as conn:
            # update(users).where(users.c.id == 5). \
            #     values(name='user #5')
            # ins = users.insert().values(name='jack', fullname='Jack Jones')

            # query = (sa.insert(account).values(login=login))
            # query = account.insert().returning(sa.literal_column('*')).values(login=login)            query = account.insert().returning(sa.literal_column('*')).values(login=login)
            query = account.insert().returning(account.c.key).values(login=login)

            async for row in conn.execute(query):
                return row.key

    async def joke_insert(self, key, joke_text: str):
        joke_id = None

        async with self.engine.acquire() as conn:
            query = joke.select().where(joke.c.text == joke_text.strip())
            async for row in conn.execute(query):
                joke_id = row

            if not joke_id:
                query = joke.insert().returning(joke.c.id).values(text=joke_text.strip())
                async for row in conn.execute(query):
                    joke_id = row

            query = account.update().where(account.c.key == key).values(jokes=account.c.jokes + sa.cast([joke_id.id], sa.ARRAY(sa.Integer)))
            await conn.execute(query)
        return joke_id

    async def joke_delete(self, key, joke_id):
        async with self.engine.acquire() as conn:
            query = joke.delete().where(joke.c.id == joke_id)
            await conn.execute(query)

            query = account.update().where(account.c.key == key).values(jokes=sa.func.array_remove(account.c.jokes, joke_id))
            await conn.execute(query)


    async def joke_get(self, joke_id):
        async with self.engine.acquire() as conn:
            query = joke.select().where(joke.c.id == joke_id)
             async for row in conn.execute(query):
                joke_id = row

        return joke_id