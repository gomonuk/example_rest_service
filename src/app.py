import json

from aiohttp import web, ClientSession
from asyncio.log import logger
from aiohttp_swagger import *

from src.table_operations import TableOperations
from src.utils import ResponseBody

r_body = ResponseBody()
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
async def fields_check_middleware(request, handler):
    if "/api/doc" in request.path:
        response = await handler(request)
        return response

    data = await request.json()
    apikey = data.get("apikey")

    required_fields = METHOD_INFO[request.method][request.path]["fields"]
    fields = required_fields - set(data.keys())

    if fields:
        error_msg = "Required fields not received. For the endpoint '{} {}' required fields: {}"
        return web.Response(body=json.dumps(r_body.error(
            error_msg.format(request.method, request.path, str(required_fields))
        )))

    if request.path != "/do_login":
        check_apikey = await to.check_apikey(apikey)
        if not check_apikey:
            return web.Response(body=json.dumps(r_body.error(
                "apikey '{}' does not exist".format(apikey)
            )))

    response = await handler(request)
    return response


@web.middleware
async def logger_middleware(request, handler):
    data = await request.json()
    await to.write_log(key=data.get("apikey"), ip_address=request.remote)
    response = await handler(request)
    return response


async def generate_joke(request):
    """
    tags:
    - Операции с шутками
    summary: Сгенерировать шутку
    description: Сгенерировать шутку.
    produces:
    - application/json
    parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          apikey:
            type: integer
            description: Передайте ключ полученый после регистрации
        required:
            - apikey
    responses:
    "200":
      description: successful operation
    """

    data = await request.json()
    async with ClientSession() as session:
        response = await session.get("https://geek-jokes.sameerkumar.website/api")
        joke_text = await response.json()

    id_joke = await to.joke_insert(data["apikey"], joke_text)
    return web.Response(body=json.dumps(r_body.result({"joke_id": id_joke.id})))


async def delete_joke(request):
    """
    tags:
    - Операции с шутками
    summary: Удалить шутку
    description: Удалить вашу шутку.
    produces:
    - application/json
    parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          apikey:
            type: integer
            description: Передайте ключ полученый после регистрации
          joke_id:
            type: integer
            description: Передайте id шутки
        required:
            - apikey
            - joke_id
    responses:
    "200":
      description: successful operation
    """

    data = await request.json()
    joke = await to.joke_get(key=data["apikey"], joke_id=data["joke_id"])

    if joke:
        await to.joke_delete(data["apikey"], data["joke_id"])
        body = json.dumps(r_body.result("Joke successfully deleted"))
    else:
        body = json.dumps(r_body.error("Joke not found"))

    return web.Response(body=body)


async def get_joke(request):
    """
       tags:
       - Операции с шутками
       summary: Получить шутку
       description: Возвращает список ваших шуток.
       produces:
       - application/json
       parameters:
       - in: body
         name: body
         required: true
         schema:
           type: object
           properties:
             apikey:
               type: integer
               description: Передайте ключ полученый после регистрации
             joke_id:
               type: integer
               description: Передайте id шутки, чтобы получить конкретную шутку
           required:
               - apikey
       responses:
       "200":
         description: successful operation
       """

    data = await request.json()
    joke = await to.joke_get(key=data["apikey"], joke_id=data.get("joke_id") or None)
    return web.Response(body=json.dumps(r_body.result(joke)))


async def update_joke(request):
    """
    tags:
    - Операции с шутками
    summary: Обновить шутку
    description: Обновить текст вашей шутки.
    produces:
    - application/json
    parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          apikey:
            type: integer
            description: Передайте ключ полученый после регистрации
          joke_id:
            type: integer
            description: Передайте id шутки
          joke_text:
            type: string
            description: Придумайте имя пользователя
        required:
            - apikey
            - joke_id
            - joke_text
    responses:
    "200":
      description: successful operation
    """

    data = await request.json()
    apikey = data["apikey"]
    joke_id = data["joke_id"]
    joke_text = data["joke_text"]

    joke = await to.joke_get(key=apikey, joke_id=joke_id)

    if joke:
        await to.joke_delete(key=apikey, joke_id=joke_id)
        new_joke_id = await to.joke_insert(key=apikey, joke_text=joke_text)
        body = json.dumps(r_body.result({"new_joke_id": new_joke_id.id}))
    else:
        body = json.dumps(r_body.error("Joke not found"))

    return web.Response(body=body)


async def do_login(request):
    """
    tags:
    - Операции с пользователем
    summary: Регистрация пользователя
    description: Регистрация пользователя и получение ключа.
    produces:
    - application/json
    parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          login:
            type: string
            description: Придумайте имя пользователя
        required:
            - login
    responses:
    "200":
      description: successful operation
    """

    data = await request.json()
    login = data.get("login")
    api_key = await to.do_login(login)
    response = r_body.result({"login": login, "api_key": api_key})
    return web.Response(body=json.dumps(response))


async def on_startup(request):
    await to.init()

app = web.Application(middlewares=[error_middleware, fields_check_middleware, logger_middleware])
app.router.add_post("/do_login", do_login)
app.router.add_post("/joke", generate_joke)
app.router.add_put("/joke", update_joke)
app.router.add_get("/joke", get_joke, allow_head=False)
app.router.add_delete("/joke", delete_joke)

app.on_startup.append(on_startup)
setup_swagger(app)

host = "localhost"
port = 9996

if __name__ == "__main__":
    web.run_app(app, host=host, port=port)
