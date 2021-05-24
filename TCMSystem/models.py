from django.db import models

# Create your models here.

class User(models.Model):
    '''用户表'''

    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
