from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    #自定义扩展用户类，在用户名、密码、邮箱等属性的基础上，扩展属性
    mobile=models.CharField(max_length=11,unique=True)
    class Meta:
        db_table='tb_users'