from django.db import models
from django.contrib.auth.models import User
from django.db import models
 
class Online(models.Model):
    id:int
    first_name:str
    last_name:str
    email:str
    password:str

class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # Set the default user ID as needed
    imagename = models.ImageField(upload_to='images/')


