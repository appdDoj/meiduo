import xadmin

from . import models

# Register your models here.

xadmin.site.register(models.ContentCategory)
xadmin.site.register(models.Content)