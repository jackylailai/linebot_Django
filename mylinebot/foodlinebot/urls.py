from django.urls import path
from . import views
 
urlpatterns = [
    path('callback', views.callback)
]
# 設定這個LINE Bot應用程式(APP)的連結網址