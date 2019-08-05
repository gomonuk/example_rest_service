from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from src import to
from src.app import generate_joke, update_joke, get_joke, delete_joke, do_registration
from src.middleware import error_middleware, fields_check_middleware


class BaseClass(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application(middlewares=[error_middleware, fields_check_middleware])
        app.router.add_post("/registration", do_registration)
        app.router.add_post("/joke", generate_joke)
        app.router.add_put("/joke", update_joke)
        app.router.add_get("/joke", get_joke, allow_head=False)
        app.router.add_delete("/joke", delete_joke)
        # app.on_startup.append(on_startup)
        await to.init()

        self.apikey = await to.exec_and_get("key", query=to.insert_to_account, tuple_params=("login",))
        joke_id = await to.exec_and_get("id", query=to.insert_to_joke, tuple_params=("joke_text_1",))
        params = {"account_key": self.apikey, "joke_id": joke_id}
        self.fake_joke_id = await to.exec_and_get("fake_joke_id", query=to.insert_to_account_joke, params=params)

        return app


