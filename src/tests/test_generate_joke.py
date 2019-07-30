import json
import unittest

from aiohttp.test_utils import unittest_run_loop
from src.tests.base_class import BaseClass


class TestGenerateJoke(BaseClass):
    @unittest_run_loop
    async def test_2_positive(self):
        resp = await self.client.post("/joke", data=json.dumps({"apikey": self.apikey}))
        data = await resp.text()
        json_data = json.loads(data)
        self.assertEqual(first=type(json_data.get("result", {}).get("joke_id")),
                         second=int,
                         msg="joke_id неверного типа"
                         )

    @unittest_run_loop
    async def test_3_negative(self):
        resp = await self.client.post("/joke", data=json.dumps({"apikey": 3}))
        data = await resp.text()
        json_data = json.loads(data)
        self.assertEqual(first=type(json_data.get("error")),
                         second=str,
                         msg="Не получено сообщение об ошибке"
                         )


if __name__ == "__main__":
    unittest.main()
