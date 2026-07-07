class EmailAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class PostTitleAlreadyExistsError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

class NotFoundError(Exception):
    pass

class ForbiddenError(Exception):
    pass