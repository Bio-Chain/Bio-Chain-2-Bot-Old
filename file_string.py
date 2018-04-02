class FileString:
    """Wrapper for a string that is stored in a file"""
    def __init__(self, filename):
        self.filename = filename
        self.data = ''
        self.update()

    def update(self):
        try:
            with open(self.filename) as f:
                self.data = f.read()
        except:
            pass

    def set(self, data):
        self.data = str(data)
        with open(self.filename, 'w') as f:
            f.write(data)

    def get(self):
        return self.data

    def __str__(self):
        return self.data


if __name__ == '__main__':
    test = FileString('test.txt')
    test.set('foobar')

    test = FileString('test.txt')
    assert test.get() == 'foobar'

    import os
    os.remove('test.txt')
