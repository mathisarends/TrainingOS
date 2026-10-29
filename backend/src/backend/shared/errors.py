class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class InvalidInput(Exception):
    """Messages contain only deliberately public domain validation details."""


class AuthenticationRequired(Exception):
    pass


class Forbidden(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


class RateLimited(Exception):
    pass
