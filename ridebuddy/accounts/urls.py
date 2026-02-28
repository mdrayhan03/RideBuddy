from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('', views.index, name='index'),
    path('index.html', views.index, name='index_html'), # For legacy support
    path('login/', views.login_view, name='login'),
    path('login.html', views.login_view, name='login_html'),
    path('signup/', views.signup_view, name='signup'),
    path('signup.html', views.signup_view, name='signup_html'),
    path('home_rider/', views.home_rider, name='home_rider'),
    path('home_rider.html', views.home_rider, name='home_rider_html'),
    path('home_student/', views.home_student, name='home_student'),
    path('home_student.html', views.home_student, name='home_student_html'),
    path('account_rider/', views.account_rider, name='account_rider'),
    path('account_rider.html', views.account_rider, name='account_rider_html'),
    path('account_student/', views.account_student, name='account_student'),
    path('account_student.html', views.account_student, name='account_student_html'),
    path('settings/', views.settings_view, name='settings'),
    path('settings.html', views.settings_view, name='settings_html'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet.html', views.wallet_view, name='wallet_html'),
    path('about/', views.about_view, name='about'),
    path('about.html', views.about_view, name='about_html'),
]
