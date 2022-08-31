class IntegrityError(Exception):
    """Base exception for application integrity errors"""

    pass


class UserAlreadyExists(IntegrityError):
    """Raised when there is already one user with the same cpf"""

    pass


class DomainError(Exception):
    """Base exception for application domain errors"""

    pass


class ScheduleNotAvailable(DomainError):
    """Raised when schedule is not available"""

    pass
