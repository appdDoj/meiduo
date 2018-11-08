from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register('skus/search', views.SKUSearchViewSet, base_name='skus_search')

urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/hotskus/$', views.HotSKUListView.as_view()),
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),
    url(r'^categories/(?P<pk>\d+)/$', views.CategoryView.as_view()),
    url(r'^skus/(?P<sku_id>\d+)/comments/$', views.SKUCommentsListView.as_view()),
]

urlpatterns += router.urls
