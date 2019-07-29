from aiopg.sa import create_engine
import sqlalchemy as sa

from src.utils import SQL_SQRIPTS

metadata = sa.MetaData()
account = sa.Table("account", metadata,
                   sa.Column("id", sa.Integer, primary_key=True),
                   sa.Column("login", sa.String(255)),
                   sa.Column("key", sa.String(255)),
                   sa.Column("jokes", sa.ARRAY(sa.Integer))
                   )

joke = sa.Table("joke", metadata,
                sa.Column("id", sa.Integer, primary_key=True),
                sa.Column("text", sa.String(255)),
                sa.Column("number_of_uses", sa.Integer)
                )

logs = sa.Table("logs", metadata,
                sa.Column("key", sa.Integer),
                sa.Column("ip_address", sa.String(255)),
                sa.Column("request_time", sa.DateTime)
                )


class TableOperations(object):
    def __init__(self):
        self.engine = None

    async def init(self):
        self.engine = await create_engine(
            database="postgres",
            user="postgres",
            password="",
            host="localhost",
            port="5431",
        )
        await self.__setup_database()

    async def __setup_database(self):
        async with self.engine.acquire() as conn:
            for script in SQL_SQRIPTS:
                await conn.execute(script)

    async def write_log(self, key, ip_address):
        async with self.engine.acquire() as conn:
            query = logs.insert().values(key=key,
                                         ip_address=ip_address)
            await conn.execute(query)

    async def do_login(self, login):
        async with self.engine.acquire() as conn:
            query = account.insert().returning(account.c.key).values(login=login)
            async for row in conn.execute(query):
                return row.key

    async def check_apikey(self, apikey):
        async with self.engine.acquire() as conn:
            query = account.select().where(account.c.key == apikey)
            async for row in conn.execute(query):
                return row.key

    async def joke_insert(self, key, joke_text: str):
        joke_id = None

        async with self.engine.acquire() as conn:
            query = joke.select().where(joke.c.text == joke_text.strip())
            async for row in conn.execute(query):
                joke_id = row

            if joke_id:
                query = joke.update().where(joke.c.id == joke_id.id).values(number_of_uses=joke.c.number_of_uses + 1)
                await conn.execute(query)
            else:
                query = joke.insert().returning(joke.c.id).values(text=joke_text.strip())
                async for row in conn.execute(query):
                    joke_id = row
            query = account.update().where(account.c.key == key).values(
                jokes=sa.func.array_unique(account.c.jokes + sa.cast([joke_id.id], sa.ARRAY(sa.Integer)))
            )

            await conn.execute(query)
        return joke_id

    async def joke_delete(self, key, joke_id):
        async with self.engine.acquire() as conn:
            query = """
                       UPDATE joke SET number_of_uses = number_of_uses - 1 
                       FROM account Where array_append(ARRAY[]::integer[], joke.id) <@ account.jokes
                       AND joke.id = {joke_id}
                       AND account.key = {account_key}
                       RETURNING *;
                       """

            await conn.execute(query.format(joke_id=joke_id, account_key=key))
            query = account.update().returning(account.c.id).where(account.c.key == key).values(
                jokes=sa.func.array_remove(account.c.jokes, joke_id)
            )
            await conn.execute(query)

    async def joke_get(self, key, joke_id=None):
        if joke_id:
            conditions = sa.and_(joke.c.id == joke_id, account.c.key == key)
        else:
            conditions = account.c.key == key

        account_joke_join = sa.join(account, joke, joke.c.id == sa.func.any(account.c.jokes))
        query13 = sa.select([joke.c.id, joke.c.text]).select_from(account_joke_join).where(conditions)
        async with self.engine.acquire() as conn:
            jokes_row = []
            async for row in conn.execute(query13):
                jokes_row.append(dict(row))
        return jokes_row
