import json
from aiohttp import web, ClientSession
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from asyncio.log import logger

from src.tasks_table_operations import TasksTableOperations
from src.utils import AAAAAA

b = AAAAAA(result=None, error=None)
a = TasksTableOperations()


def json_error(status_code: int, exception: Exception) -> web.Response:
    """
    Returns a Response from an exception.
    Used for error middleware.
    :param status_code:
    :param exception:
    :return:
    """
    return web.Response(
        status=status_code,
        body=json.dumps({
            'error': exception.__class__.__name__,
            'detail': str(exception)
        }).encode('utf-8'),
        content_type='application/json')


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 200:
            return response
    except web.HTTPException as ex:
        logger.warning('Request {} has failed with exception: {}'.format(request, repr(ex)))
        if ex.status == 404:
            return json_error(ex.status, ex)
        raise
    except Exception as e:
        logger.error('Request {} has failed with exception: {}'.format(request, repr(e)))
        return json_error(500, e)


@web.middleware
async def auth_middleware(request, handler):
    data = await request.json()

    if request.path != "do_login":
        # пользователь есть, но ключ не верный
        # пользователя нет
        pass
    # raise HTTPMethodNotAllowed("yr", ["rt"])
    response = await handler(request)
    return response


@web.middleware
async def logger_middleware(request, handler):
    response = await handler(request)
    print("log")
    return response


async def generate_joke(request):
    data = await request.json()

    async with ClientSession() as session:
        response = await session.get("https://geek-jokes.sameerkumar.website/api")
        joke_text = await response.json()

    id_joke = await a.joke_insert(data["apikey"], joke_text)
    return web.Response(body=json.dumps(b.change_and_return({"result": {"joke_id": id_joke.id}})))


async def delete_joke(request):
    data = await request.json()

    await a.joke_delete(data["apikey"], data["joke_id"])
    return web.Response(body=json.dumps(b.get()))


async def get_joke(request):
    data = await request.json()

    await a.joke_delete(data["joke_id"])
    return web.Response(body=json.dumps(b.get()))


async def do_login(request):
    data = await request.json()
    login = data.get("login")

    if login:
        api_key = await a.do_login(login)
        response = b.change_and_return({"result": {"login": login, "api_key": api_key}})
    else:
        response = b.change_and_return({"error": "login dont receive"})

    return web.Response(body=json.dumps(response))


async def on_startup(request):
    await a.init()


app = web.Application(middlewares=[ auth_middleware])
app.router.add_get("/", generate_joke)
app.router.add_post("/do_login", do_login)
app.router.add_post("/joke",   generate_joke)

# app.router.add_put("/joke",    generate_joke)
app.router.add_get("/joke",    get_joke)
app.router.add_delete("/joke", delete_joke)


app.on_startup.append(on_startup)

host = "localhost"
port = 9996

if __name__ == "__main__":
    web.run_app(app, host=host, port=port)