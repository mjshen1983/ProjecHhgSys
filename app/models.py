from django.db import models

class AppUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    password_hash = models.CharField(max_length=255)
    display_name = models.CharField(max_length=64)

    class Meta:
        db_table = 'app_users'
        managed = False
