from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('login/', views.analytics_login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('students/', views.students_view, name='students'),
    path('students/<int:pk>/', views.student_detail_view, name='student_detail'),
    path('riders/', views.riders_view, name='riders'),
    path('riders/<int:pk>/', views.rider_detail_view, name='rider_detail'),
    path('vehicles/', views.vehicles_view, name='vehicles'),
    path('vehicles/<int:pk>/', views.vehicle_detail_view, name='vehicle_detail'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('reviews/<int:pk>/', views.review_detail_view, name='review_detail'),
    path('profile/', views.profile_view, name='profile'),
]
