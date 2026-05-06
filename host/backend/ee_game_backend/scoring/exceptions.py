"""Scoring exceptions."""


class ScoringError(Exception):
    pass


class ManualAdjustmentRejected(ScoringError):
    pass
