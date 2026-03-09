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
    path('ride_host_student/', views.ride_host_student, name='ride_host_student'),
    path('ride_host_rider/', views.ride_host_rider, name='ride_host_rider'),
    path('ride_live_student/', views.ride_live_student, name='ride_live_student'),
    path('ride_live_rider/', views.ride_live_rider, name='ride_live_rider'),
    path('active-rides-json/', views.active_rides_json, name='active_rides_json'),
    path('api/create-ride/', views.create_ride_api, name='create_ride_api'),
    path('api/ride-details/<int:ride_id>/', views.get_ride_details_api, name='get_ride_details_api'),
    path('api/join-ride/', views.join_ride_api, name='join_ride_api'),
]
