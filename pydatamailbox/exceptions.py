class Talk2mBaseException(BaseException):
    pass


class Talk2mConnectionError(Talk2mBaseException):
    pass


class Talk2mResponseError(Talk2mBaseException):
    pass


class Talk2mStatusError(Talk2mBaseException):
    pass


class Talk2mArgsError(AttributeError):
    pass
