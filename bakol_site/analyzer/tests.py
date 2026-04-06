from django.db import models
from django.contrib.auth.models import User

class UserTrack(models.Model):
    user = models.ForeignKey(User, on_visit=models.CASCADE)
    file = models.FileField(upload_to='user_tracks/')
    filename = models.CharField(max_length=255)
    hash = models.CharField(max_length=32, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.filename}"
