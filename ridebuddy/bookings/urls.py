from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path('activity_rider/', views.activity_rider, name='activity_rider'),
    path('activity_rider.html', views.activity_rider, name='activity_rider_html'),
    path('activity_student/', views.activity_student, name='activity_student'),
    path('activity_student.html', views.activity_student, name='activity_student_html'),
    path('history/', views.history, name='history'),
    path('history.html', views.history, name='history_html'),
    path('history_rider/', views.history, name='history_rider'),
    path('history_rider.html', views.history, name='history_rider_html'),
    path('history_student/', views.history, name='history_student'),
    path('history_student.html', views.history, name='history_student_html'),
    path('individual_history/', views.individual_history, name='individual_history'),
    path('individual_history.html', views.individual_history, name='individual_history_html'),
    path('individual_history_rider/', views.individual_history, name='individual_history_rider'),
    path('individual_history_rider.html', views.individual_history, name='individual_history_rider_html'),
    path('individual_history_student/', views.individual_history, name='individual_history_student'),
    path('individual_history_student.html', views.individual_history, name='individual_history_student_html'),
    path('create-booking-api/', views.create_booking_api, name='create_booking_api'),
    path('student-activity-api/', views.get_student_activity_api, name='get_student_activity_api'),
    path('rider-activity-api/', views.get_rider_activity_api, name='get_rider_activity_api'),
    path('cancel-activity-api/', views.cancel_activity_api, name='cancel_activity_api'),
    path('update-booking-event-api/', views.update_booking_event_api, name='update_booking_event_api'),
    path('update-booking-preferences-api/', views.update_booking_preferences_api, name='update_booking_preferences_api'),
    path('history-api/', views.get_history_api, name='get_history_api'),
    path('individual-history-api/', views.get_individual_history_api, name='get_individual_history_api'),
]
