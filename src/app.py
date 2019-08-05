import json

from aiohttp import web, ClientSession
from aiohttp_swagger import swagger_path, setup_swagger

from src import to, r_body
from src.middleware import error_middleware, fields_check_middleware, logger_middleware


@swagger_path("../swagger_files/generate_joke.yaml")
async def generate_joke(request):
    data = request.rel_url.query

    async with ClientSession() as session:
        response = await session.get("https://geek-jokes.sameerkumar.website/api")
        joke_text = await response.json()

    joke_id = await to.exec_and_get("id", query=to.insert_to_joke, tuple_params=(joke_text,))
    params = {"account_key": data["apikey"], "joke_id": joke_id}
    fake_joke_id = await to.exec_and_get("fake_joke_id", query=to.insert_to_account_joke, params=params)
    return web.Response(body=json.dumps(r_body.result({"joke_id": fake_joke_id})))


@swagger_path("../swagger_files/delete_joke.yaml")
async def delete_joke(request):
    data = request.rel_url.query
    params = {"account_key": data["apikey"], "fake_joke_id": data["joke_id"]}
    deleted_joke = await to.execute(to.delete_joke, params=params)

    if deleted_joke:
        body = json.dumps(r_body.result("Joke successfully deleted"))
    else:
        body = json.dumps(r_body.error("Joke not found"))

    return web.Response(body=body)


@swagger_path("../swagger_files/get_joke.yaml")
async def get_joke(request):
    data = request.rel_url.query
    fake_joke_id = data.get("joke_id")
    parameters = {"account_key": data["apikey"]}
    query = to.select_from_joke

    if fake_joke_id:
        query += " AND fake_joke_id={fake_joke_id}"
        parameters["fake_joke_id"] = fake_joke_id

    joke_list = await to.execute(query, params=parameters)
    return web.Response(body=json.dumps(r_body.result(joke_list)))


@swagger_path("../swagger_files/update_joke.yaml")
async def update_joke(request):
    data = request.rel_url.query
    apikey = data["apikey"]
    fake_joke_id = data["joke_id"]
    joke_text = data["joke_text"]

    joke_id = await to.exec_and_get(get_key="id", query=to.insert_to_joke, tuple_params=(joke_text,))
    params = {"account_key": apikey, "joke_id": joke_id, "fake_joke_id": fake_joke_id}
    new_fake_joke_id = await to.exec_and_get(get_key="fake_joke_id", query=to.update_to_account_joke, params=params)

    if new_fake_joke_id:
        body = json.dumps(r_body.result({"joke_id": new_fake_joke_id}))
    else:
        body = json.dumps(r_body.error("Joke not found"))

    return web.Response(body=body)


@swagger_path("../swagger_files/do_registration.yaml")
async def do_registration(request):
    login = request.rel_url.query["login"]
    api_key = await to.exec_and_get("key", query=to.insert_to_account, tuple_params=(login,))
    response = r_body.result({"login": login, "apikey": api_key})
    return web.Response(body=json.dumps(response))


async def on_startup(request):
    await to.init()

app = web.Application(middlewares=[logger_middleware, error_middleware, fields_check_middleware])
app.router.add_post("/registration", do_registration)
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
