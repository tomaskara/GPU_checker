from django.db import models


# Create your models here.
class Gpu(models.Model):
    name = models.CharField(max_length=90)
    version = models.CharField(max_length=20, null=True)
    shop = models.CharField(max_length=70)
    price = models.IntegerField()
    url = models.URLField(null=True)
    date = models.DateField(null=True)
    updated = models.DateTimeField(auto_now=True)
    stock = models.BooleanField(default=False)




from django.db import models

# Create your models here.
