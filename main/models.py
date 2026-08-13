from django.db import models
 
class Person(models.Model):
    name = models.CharField(max_length=20)
    # age = models.IntegerField()
    email = models.EmailField()
    password = models.CharField(max_length=20)
    balance = models.FloatField()
    role = models.CharField()
