import json
from asyncio.log import logger

from aiohttp import web

from src import to, r_body

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
            "error": exception.__class__.__name__,
            "detail": str(exception)
        }).encode("utf-8"),
        content_type="application/json")


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 200:
            return response
    except web.HTTPException as ex:
        logger.warning("Request {} has failed with exception: {}".format(request, repr(ex)))
        if ex.status == 404:
            return json_error(ex.status, ex)
        raise
    except Exception as e:
        logger.error("Request {} has failed with exception: {}".format(request, repr(e)))
        return json_error(500, e)


@web.middleware
async def fields_check_middleware(request, handler):
    if "api/doc" in request.path:
        response = await handler(request)
        return response

    data = await request.json()

    apikey = data.get("apikey")
    await to.write_log(key=data.get("apikey"), ip_address=request.remote)
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