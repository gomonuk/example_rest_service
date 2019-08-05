import json
from asyncio.log import logger

from aiohttp import web

from src import to, r_body

METHOD_INFO = {"POST": {"/registration": {"fields": {"login"}},
                        "/joke": {"fields": {"apikey"}}},
               "GET": {"/joke": {"fields": {"apikey"}}},
               "PUT": {"/joke": {"fields": {"apikey", "joke_id", "joke_text"}}},
               "DELETE": {"/joke": {"fields": {"apikey", "joke_id"}}},
               }


def json_error(status_code: int, exception: Exception) -> web.Response:
    exception_msg = exception.__class__.__name__ + " detail: " + str(exception)
    return web.Response(
        status=status_code,
        body=json.dumps(r_body.error(exception_msg)).encode("utf-8"),
        content_type="application/json")


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 200:
            return response
    except web.HTTPException as ex:
        if ex.status == 404:
            return json_error(ex.status, ex)
        raise
    except Exception as e:
        return json_error(500, e)


@web.middleware
async def logger_middleware(request, handler):
    response = await handler(request)
    json_data = json.dumps({"response.status": response.status, "path_qs": request.path_qs, "method": request.method})
    apikey = request.rel_url.query.get("apikey")
    logger.info("Apikey: {} make request {}".format(apikey, json_data))
    await to.execute(to.insert_to_logs, tuple_params=(apikey, request.remote, json_data))
    return response


@web.middleware
async def fields_check_middleware(request, handler):
    if "api/doc" in request.path:
        response = await handler(request)
        return response

    data = request.rel_url.query
    apikey = data.get("apikey")
    required_fields = METHOD_INFO[request.method][request.path]["fields"]
    fields = required_fields - set(data.keys())

    if fields:
        error_msg = "Required fields not received. For the endpoint '{} {}' required fields: {}"
        return web.Response(body=json.dumps(r_body.error(
            error_msg.format(request.method, request.path, str(required_fields))
        )))

    if request.path != "/registration":
        check_apikey = await to.execute(to.select_from_account, params={"account_key": apikey})
        if not check_apikey:
            return web.Response(body=json.dumps(r_body.error(
                "apikey '{}' does not exist".format(apikey)
            )))

    response = await handler(request)
    return response
