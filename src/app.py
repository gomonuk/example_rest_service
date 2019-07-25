import json
from aiohttp import web


async def make_task( request):
    data = await request.json()
    resp = None
    error = None

    return web.Response(body=json.dumps({"result": resp, "error": error}))

app = web.Application()
app.router.add_get('/', get_index)

host = 'localhost'
port = 9996

if __name__ == '__main__':
    web.run_app(app, host=host, port=port)