"""Shared error types."""


class ArtifactMutationError(Exception):
    """Raised when a specialist attempts to mutate an immutable artifact."""


class InvalidSkillResultError(Exception):
    """Raised when a non-SkillResult object is passed where a SkillResult is required."""
