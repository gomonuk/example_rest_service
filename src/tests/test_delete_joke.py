import json
import unittest

from aiohttp.test_utils import unittest_run_loop
from src.tests.base_class import BaseClass


class TestDeleteJoke(BaseClass):
    @unittest_run_loop
    async def test_1_positive(self):
        resp = await self.client.delete("/joke", params={"apikey": self.apikey,
                                                         "joke_id": self.fake_joke_id
                                                         })
        data = await resp.text()
        json_data = json.loads(data)
        self.assertEqual(first=type(json_data.get("result")),
                         second=str,
                         msg="неверный тип ответа"
                         )

    @unittest_run_loop
    async def test_2_negative(self):
        resp = await self.client.put("/joke", params={"apikey": self.apikey,
                                                      "joke_id": 5,
                                                      })
        data = await resp.text()
        json_data = json.loads(data)
        self.assertEqual(first=type(json_data.get("error")),
                         second=str,
                         msg="Не получено сообщение об ошибке"
                         )


if __name__ == "__main__":
    unittest.main()
