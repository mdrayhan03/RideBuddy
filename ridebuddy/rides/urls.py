from django.urls import path
from . import views

app_name = "rides"

urlpatterns = [
    path('available_ride_student/', views.available_ride_student, name='available_ride_student'),
    path('available_ride_student.html', views.available_ride_student, name='available_ride_student_html'),
    path('confirm_ride_student/', views.confirm_ride_student, name='confirm_ride_student'),
    path('confirm_ride_student.html', views.confirm_ride_student, name='confirm_ride_student_html'),
    path('ride_start_rider/', views.ride_start_rider, name='ride_start_rider'),
    path('ride_start_rider.html', views.ride_start_rider, name='ride_start_rider_html'),
    path('ride_student/', views.ride_student, name='ride_student'),
    path('ride_student.html', views.ride_student, name='ride_student_html'),
    path('share_ride_student/', views.share_ride_student, name='share_ride_student'),
    path('share_ride_student.html', views.share_ride_student, name='share_ride_student_html'),
]
