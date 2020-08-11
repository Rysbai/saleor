from django.db import models


class Chat(models.Model):
    chat_id = models.CharField(max_length=200)
    username = models.CharField(max_length=100)
