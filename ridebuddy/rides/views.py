from django.shortcuts import render

def available_ride_student(request):
    return render(request, 'available_ride_student.html')

def confirm_ride_student(request):
    return render(request, 'confirm_ride_student.html')

def ride_start_rider(request):
    return render(request, 'ride_start_rider.html')

def ride_student(request):
    return render(request, 'ride_student.html')

def share_ride_student(request):
    return render(request, 'share_ride_student.html')
