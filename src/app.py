import json
from aiohttp import web
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from asyncio.log import logger

from src.tasks_table_operations import TasksTableOperations


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


async def make_task(request):
    resp = None
    print(23)
    error = None
    return web.Response(body=json.dumps({"result": resp, "error": error}))


async def do_login(request):
    resp, error = None, None
    data = await request.json()

    a = TasksTableOperations()
    z = await a.select(1)
    print(z)
    if data.get("login"):
        print(data)
    else:
        print("error login dont receive")
    return web.Response(body=json.dumps({"result": resp, "error": error}))


app = web.Application(middlewares=[error_middleware, logger_middleware, auth_middleware])
app.router.add_get("/", make_task)
app.router.add_post("/do_login", do_login)


host = "localhost"
port = 9996

if __name__ == "__main__":
    web.run_app(app, host=host, port=port)