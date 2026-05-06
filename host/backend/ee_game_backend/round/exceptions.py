"""Round service exceptions."""


class RoundError(Exception):
    pass


class NoActiveRoundError(RoundError):
    pass


class InvalidRoundTransitionError(RoundError):
    pass


class UnknownGameError(RoundError):
    pass
