from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxFileSize:
    """Rejects uploads over the size limit."""

    def __init__(self, megabytes):
        self.megabytes = megabytes

    def __call__(self, f):
        if f.size > self.megabytes * 1024 * 1024:
            raise ValidationError(f'File too large. Maximum size is {self.megabytes}MB.')
