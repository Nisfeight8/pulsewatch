class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidOrExpiredTokenError(Exception):
    pass


class EmailNotVerifiedError(Exception):
    pass
