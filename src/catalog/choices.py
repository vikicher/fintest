from django.db import models


class Trend(models.TextChoices):
    UP = "up", "Up"
    DOWN = "down", "Down"
    SAME = "same", "Same"