class DataMailboxBaseException(BaseException):
    pass


class DataMailboxConnectionError(DataMailboxBaseException):
    pass


class DataMailboxResponseError(DataMailboxBaseException):
    pass


class DataMailboxStatusError(DataMailboxBaseException):
    pass


class DataMailboxArgsError(AttributeError):
    pass
