import json
import unittest

from aiohttp.test_utils import unittest_run_loop
from src.tests.base_class import BaseClass


class TestDoLogin(BaseClass):
    @unittest_run_loop
    async def test_1_positive(self):
        resp = await self.client.post("/do_login", data=json.dumps({"login": "test_user"}))
        data = await resp.text()
        json_data = json.loads(data)
        self.assertEqual(first=type(json_data.get("result", {}).get("apikey")),
                         second=int,
                         msg="api_key неверного типа"
                         )

    @unittest_run_loop
    async def test_2_negative(self):
        resp = await self.client.post("/do_login", data=json.dumps({"log": "test_user"}))
        data = await resp.text()
        json_data = json.loads(data)
        self.assertEqual(first=type(json_data.get("error")),
                         second=str,
                         msg="Не получено сообщение об ошибке"
                         )


if __name__ == "__main__":
    unittest.main()
