from src.table_operations import TableOperations


class ResponseBody(object):
    def __init__(self):
        self.constant_data = {"result": None, "error": None}

    def error(self, data):
        body = {}
        body.update(self.constant_data)
        body["error"] = data
        return body

    def result(self, data):
        body = {}
        body.update(self.constant_data)
        body["result"] = data
        return body


r_body = ResponseBody()
to = TableOperations()
