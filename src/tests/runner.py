import unittest

from src.tests.test_delete_joke import TestDeleteJoke
from src.tests.test_do_login import TestDoLogin
from src.tests.test_generate_joke import TestGenerateJoke
from src.tests.test_get_joke import TestGetJoke
from src.tests.test_update_joke import TestUpdateJoke

testCases = [
    TestDeleteJoke,
    TestDoLogin,
    TestGenerateJoke,
    TestGetJoke,
    TestUpdateJoke,
]

testLoad = unittest.TestLoader()

suites = []
for tc in testCases:
    suites.append(testLoad.loadTestsFromTestCase(tc))

res_suite = unittest.TestSuite(suites)

runner = unittest.TextTestRunner(verbosity=2)
runner.run(res_suite)
