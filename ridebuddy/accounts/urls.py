from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "accounts"

urlpatterns = [
    path('', views.index, name='index'),
    path('index.html', views.index, name='index_html'), # For legacy support
    path('login/', views.login_view, name='login'),
    path('login.html', views.login_view, name='login_html'),
    path('login-api/', views.login_api, name='login_api'),
    path('logout-api/', views.logout_api, name='logout_api'),
    path('signup/', views.signup_view, name='signup'),
    path('signup.html', views.signup_view, name='signup_html'),
    path('signup-api/', views.signup_api, name='signup_api'),
    path('home_rider/', views.home_rider, name='home_rider'),
    path('home_rider.html', views.home_rider, name='home_rider_html'),
    path('home_student/', views.home_student, name='home_student'),
    path('home_student.html', views.home_student, name='home_student_html'),
    path('account/', views.account_view, name='account'),
    path('settings/', views.settings_view, name='settings'),
    path('settings.html', views.settings_view, name='settings_html'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet.html', views.wallet_view, name='wallet_html'),
    path('payments/', views.payments_view, name='payments'),
    path('invoice/<int:commission_id>/', views.invoice_view, name='invoice'),
    path('make-payment/<int:commission_id>/', views.make_payment_view, name='make_payment'),
    path('about/', views.about_view, name='about'),
    path('about.html', views.about_view, name='about_html'),
    path('update-location-api/', views.update_location_api, name='update_location_api'),
    path('get-participant-locations-api/', views.get_participant_locations_api, name='get_participant_locations_api'),
    path('update-student-api/', views.update_student_api, name='update_student_api'),
    path('change-password-api/', views.change_password_api, name='change_password_api'),
    path('verify-otp-api/', views.verify_otp_api, name='verify_otp_api'),
    path('switch-role-api/', views.switch_role_api, name='switch_role_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
