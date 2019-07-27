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
