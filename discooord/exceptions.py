class DiscordError(Exception):
    _message = None

    def __init__(self, message=None):
        if message is not None:
            self.message = message
        super(DiscordError, self).__init__(self.message)

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.message))

    def __repr__(self):
        return str(self)


class ApiError(DiscordError):
    code = None
    response = None

    def __init__(self, message=None, code=None, response=None):
        if message is None and code is None and response is not None:
            try:
                data = response.json()
                message = data['message']

                if data['code'] == 0:
                    code = response.status_code
                else:
                    code = data['code']
            except ValueError:
                message = 'No error data supplied in response'

        self.code = code
        self.response = response

        super(ApiError, self).__init__(message)

    def __str__(self):
        return '{}({}, {})'.format(self.__class__.__name__, repr(self.message), repr(self.code))


class InvalidToken(DiscordError):
    _message = 'Invalid authentication token provided'


class GatewayError(DiscordError):
    pass


class UnknownOperation(GatewayError):
    def __init__(self, opcode):
        message = 'Unknown operation received in gateway payload ({})'.format(opcode)
        super(UnknownOperation, self).__init__(message)


class UnknownEvent(GatewayError):
    def __init__(self, event):
        message = 'Unknown event received in gateway payload ({})'.format(event)
        super(UnknownOperation, self).__init__(message)
