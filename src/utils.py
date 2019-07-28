class AAAAAA(object):
    def __init__(self, **kwargs):
        self.constant_data = kwargs

    def change_and_return(self, data):
        d = {}
        d.update(self.constant_data)
        d.update(data)
        return d

    def get(self):
        return self.constant_data


def convert(resultproxy):
    d, a = {}, []
    for rowproxy in resultproxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return a
