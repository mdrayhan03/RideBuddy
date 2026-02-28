from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def login_view(request):
    return render(request, 'login.html')

def signup_view(request):
    return render(request, 'signup.html')

def home_rider(request):
    return render(request, 'home_rider.html')

def home_student(request):
    return render(request, 'home_student.html')

def account_rider(request):
    return render(request, 'account_rider.html')

def account_student(request):
    return render(request, 'account_student.html')

def settings_view(request):
    return render(request, 'settings.html')

def wallet_view(request):
    return render(request, 'wallet.html')

def about_view(request):
    return render(request, 'about.html')
