from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from src import to
from src.app import do_login, generate_joke, update_joke, get_joke, delete_joke
from src.middleware import error_middleware, fields_check_middleware


class BaseClass(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application(middlewares=[error_middleware, fields_check_middleware])
        app.router.add_post("/do_login", do_login)
        app.router.add_post("/joke", generate_joke)
        app.router.add_put("/joke", update_joke)
        app.router.add_get("/joke", get_joke, allow_head=False)
        app.router.add_delete("/joke", delete_joke)
        # app.on_startup.append(on_startup)
        await to.init()

        self.apikey = await to.do_login("test_login")
        self.id_joke = await to.joke_insert(self.apikey, "joke_text_1")

        return app


