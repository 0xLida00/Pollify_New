from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image
import os

class User(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username

    def get_profile_picture_url(self):
        """Return profile picture URL or default image."""
        if self.profile_picture and default_storage.exists(self.profile_picture.name):
            return self.profile_picture.url  # Return uploaded profile pic

        return f"{settings.MEDIA_URL}profile_pics/default.png"  # Return default image

    def save(self, *args, **kwargs):
        """Resize profile picture to 300x300 pixels if necessary."""
        super().save(*args, **kwargs)

        if self.profile_picture and default_storage.exists(self.profile_picture.name):
            try:
                img_path = self.profile_picture.path

                # Open image and resize if needed
                with Image.open(img_path) as img:
                    if img.height > 300 or img.width > 300:
                        img.thumbnail((300, 300))
                        img.save(img_path)

            except Exception as e:
                print(f"Error processing profile picture: {e}")

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower} follows {self.followed}"