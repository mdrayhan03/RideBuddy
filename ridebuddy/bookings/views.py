from django.shortcuts import render

def activity_rider(request):
    return render(request, 'activity_rider.html')

def activity_student(request):
    return render(request, 'activity_student.html')

def history_rider(request):
    return render(request, 'history_rider.html')

def history_student(request):
    return render(request, 'history_student.html')

def individual_history_rider(request):
    return render(request, 'individual_history_rider.html')

def individual_history_student(request):
    return render(request, 'individual_history_student.html')
