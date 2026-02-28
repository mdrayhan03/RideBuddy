from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path('rating/', views.rating_view, name='rating'),
    path('rating.html', views.rating_view, name='rating_html'),
]
