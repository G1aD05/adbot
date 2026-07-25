import base64


class b64:
    @staticmethod
    def encode(string: str):
        encoded = base64.b64encode(string.encode('utf-8'))
        return encoded.decode('utf-8')

    @staticmethod
    def decode(string: str):
        decoded = base64.b64decode(string)
        return decoded.decode('utf-8')
