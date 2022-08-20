class IntegrityError(Exception):
    """Base exception for application integrity errors"""

    ...


class UserAlreadyExists(IntegrityError):
    """Raised when there is already one user with the same cpf"""

    ...
