import json

from aiohttp import web, ClientSession
from aiohttp_swagger import swagger_path, setup_swagger

from src import to, r_body
from src.middleware import error_middleware, fields_check_middleware


@swagger_path("../swagger_files/generate_joke.yaml")
async def generate_joke(request):
    data = await request.json()
    async with ClientSession() as session:
        response = await session.get("https://geek-jokes.sameerkumar.website/api")
        joke_text = await response.json()

    id_joke = await to.joke_insert(data["apikey"], joke_text)
    return web.Response(body=json.dumps(r_body.result({"joke_id": id_joke.id})))


@swagger_path("../swagger_files/delete_joke.yaml")
async def delete_joke(request):
    data = await request.json()
    joke = await to.joke_get(key=data["apikey"], joke_id=data["joke_id"])

    if joke:
        await to.joke_delete(data["apikey"], data["joke_id"])
        body = json.dumps(r_body.result("Joke successfully deleted"))
    else:
        body = json.dumps(r_body.error("Joke not found"))

    return web.Response(body=body)


@swagger_path("../swagger_files/get_joke.yaml")
async def get_joke(request):
    data = await request.json()
    joke = await to.joke_get(key=data["apikey"], joke_id=data.get("joke_id") or None)
    return web.Response(body=json.dumps(r_body.result(joke)))


@swagger_path("../swagger_files/update_joke.yaml")
async def update_joke(request):
    data = await request.json()
    apikey = data["apikey"]
    joke_id = data["joke_id"]
    joke_text = data["joke_text"]
    joke = await to.joke_get(key=apikey, joke_id=joke_id)

    if len(joke) == 1:
        await to.joke_delete(key=apikey, joke_id=joke_id)
        new_joke_id = await to.joke_insert(key=apikey, joke_text=str(joke_text))
        body = json.dumps(r_body.result({"new_joke_id": new_joke_id.id}))
    else:
        body = json.dumps(r_body.error("Joke not found"))

    return web.Response(body=body)


@swagger_path("../swagger_files/do_login.yaml")
async def do_login(request):
    data = await request.json()
    login = data.get("login")
    api_key = await to.do_login(login)
    response = r_body.result({"login": login, "apikey": api_key})
    return web.Response(body=json.dumps(response))


async def on_startup(request):
    await to.init()

app = web.Application(middlewares=[error_middleware, fields_check_middleware])
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
