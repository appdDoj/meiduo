# from django.contrib import admin
#
# from . import models
# from celery_tasks.html.tasks import generate_static_sku_detail_html
# # Register your models here.
#
#
# class SKUAdmin(admin.ModelAdmin):
#
#     def save_model(self, request, obj, form, change):
#         """
#         保存数据时会被自动调用的
#         :param request: 本次保存数据的请求
#         :param obj: 本次保存的模型对象,sku对象
#         :param form: 本次操作的表单
#         :param change: 本次操作的跟上次的不同
#         :return: None
#         """
#         # 必须带上'obj.save()'，可以帮助我们去实现底层的保存操作。如果不带上，保存obj的操作需要我们自己写代码完成
#         obj.save()
#
#         # 完成了保存操作，触发异步任务,生成静态的主页
#         # sku.id == obj.id
#         generate_static_sku_detail_html.delay(obj.id)
#
#
# class SKUSpecificationAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         obj.save()
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(obj.sku.id)
#
#     def delete_model(self, request, obj):
#         sku_id = obj.sku.id
#         obj.delete()
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(sku_id)
#
#
# class SKUImageAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         obj.save()
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(obj.sku.id)
#
#         # 设置SKU默认图片
#         sku = obj.sku
#         if not sku.default_image_url:
#             sku.default_image_url = obj.image.url
#             sku.save()
#
#     def delete_model(self, request, obj):
#         """
#         当在站点其中删除某一条记录时会自动的调用的
#         :param request: 本次删除的请求
#         :param obj: 本次要删除的对象
#         :return: None
#         """
#         sku_id = obj.sku.id
#         obj.delete()
#         from celery_tasks.html.tasks import generate_static_sku_detail_html
#         generate_static_sku_detail_html.delay(sku_id)
#
# class GoodsCategoryAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         obj.save()
#         from celery_tasks.html.tasks import generate_static_list_search_html
#         generate_static_list_search_html.delay()
#
#     def delete_model(self, request, obj):
#         obj.delete()
#         from celery_tasks.html.tasks import generate_static_list_search_html
#         generate_static_list_search_html.delay()
#
#
# admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
# admin.site.register(models.GoodsChannel)
# admin.site.register(models.Goods)
# admin.site.register(models.Brand)
# admin.site.register(models.GoodsSpecification)
# admin.site.register(models.SpecificationOption)
# admin.site.register(models.SKU, SKUAdmin)
# admin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
# admin.site.register(models.SKUImage, SKUImageAdmin)