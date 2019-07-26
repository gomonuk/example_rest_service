from aiopg.sa import create_engine
import asyncio
import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table('users', metadata,
                 sa.Column('id', sa.Integer, primary_key=True),
                 sa.Column('name', sa.String(255)),
                 sa.Column('birthday', sa.DateTime))

emails = sa.Table('emails', metadata,
                  sa.Column('id', sa.Integer, primary_key=True),
                  sa.Column('user_id', None, sa.ForeignKey('users.id')),
                  sa.Column('email', sa.String(255), nullable=False),
                  sa.Column('private', sa.Boolean, nullable=False))


class TasksTableOperations(object):
    def __init__(self):
        self.engine = None

    async def init(self):
        return await create_engine(
            database='postgres',
            user="postgres",
            password="",
            host="localhost",
            port="5431"
        )

    async def create_tables(self, engine):
        async with engine.acquire() as conn:
            await conn.execute('DROP TABLE IF EXISTS emails')
            await conn.execute('DROP TABLE IF EXISTS users')
            await conn.execute('''CREATE TABLE usfgfdgfers (
                                                id serial PRIMARY KEY,
                                                names varchar(255),
                                                birthday timestamp)''')
            await conn.execute('''CREATE TABLE emails (
                                        id serial,
                                        user_ids int references users(id),
                                        email varchar(253),
                                        private bool)''')


async def go():
    a = TasksTableOperations()
    e = await a.init()
    await a.create_tables(e)


loop = asyncio.get_event_loop()
loop.run_until_complete(go())