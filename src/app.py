import json

from aiohttp import web, ClientSession
from asyncio.log import logger

from src.table_operations import TableOperations
from src.utils import AAAAAA

b = AAAAAA(result=None, error=None)
to = TableOperations()


METHOD_INFO = {"POST": {"/do_login": {"fields": {"login"}},
                        "/joke": {"fields": {"apikey"}}},
               "GET": {"/joke": {"fields": {"apikey"}}},
               "PUT": {"/joke": {"fields": {"apikey", "joke_id", "joke_text"}}},
               "DELETE": {"/joke": {"fields": {"apikey", "joke_id"}}},
               }


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
    apikey = data.get("apikey")

    required_fields = METHOD_INFO[request.method][request.path]["fields"]
    fields = required_fields - set(data.keys())

    if fields:
        error_msg = "Required fields not received. For the endpoint '{} {}' required fields: {}"
        return web.Response(body=json.dumps(b.change_and_return(
            {"error": error_msg.format(request.method, request.path, str(required_fields))})))

    if request.path != "/do_login":
        check_apikey = await to.check_apikey(apikey)
        if not check_apikey:
            return web.Response(body=json.dumps(b.change_and_return(
                {"error": "apikey '{}' does not exist".format(apikey)})))

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

    id_joke = await to.joke_insert(data["apikey"], joke_text)
    return web.Response(body=json.dumps(b.change_and_return({"result": {"joke_id": id_joke.id}})))


async def delete_joke(request):
    data = await request.json()
    joke = await to.joke_get(key=data["apikey"], joke_id=data.get("joke_id"))

    if joke:
        await to.joke_delete(data["apikey"], data["joke_id"])
        body = json.dumps(b.change_and_return({"result": "Joke successfully deleted"}))
    else:
        body = json.dumps(b.change_and_return({"error": "Joke not found"}))

    return web.Response(body=body)


async def get_joke(request):
    data = await request.json()
    joke = await to.joke_get(key=data["apikey"], joke_id=data.get("joke_id"))
    return web.Response(body=json.dumps(b.change_and_return({"result": joke})))


async def update_joke(request):
    data = await request.json()
    apikey = data["apikey"]
    joke_id = data["joke_id"]
    joke_text = data["joke_text"]

    joke = await to.joke_get(key=apikey, joke_id=joke_id)

    if joke:
        await to.joke_delete(key=apikey, joke_id=joke_id)
        new_joke_id = await to.joke_insert(key=apikey, joke_text=joke_text)
        body = json.dumps(b.change_and_return({"result": {"new_joke_id": new_joke_id.id}}))
    else:
        body = json.dumps(b.change_and_return({"error": "Joke not found"}))

    return web.Response(body=body)


async def do_login(request):
    data = await request.json()
    login = data.get("login")

    if login:
        api_key = await to.do_login(login)
        response = b.change_and_return({"result": {"login": login, "api_key": api_key}})
    else:
        response = b.change_and_return({"error": "login dont receive"})

    return web.Response(body=json.dumps(response))


async def on_startup(request):
    await to.init()


app = web.Application(middlewares=[error_middleware,auth_middleware])
app.router.add_post("/do_login", do_login)
app.router.add_post("/joke", generate_joke)

app.router.add_put("/joke", update_joke)
app.router.add_get("/joke", get_joke)
app.router.add_delete("/joke", delete_joke)

app.on_startup.append(on_startup)

host = "localhost"
port = 9996

if __name__ == "__main__":
    web.run_app(app, host=host, port=port)
