from django.db import models
from django.contrib.auth.models import User

class UserTrack(models.Model):
    # Link to Django's built-in User model
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='user_tracks/%Y/%m/')
    filename = models.CharField(max_length=255)
    # Store MD5 hash to prevent duplicate uploads of the same file
    hash = models.CharField(max_length=32, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.user.username})"
