from django.shortcuts import render

def rating_view(request):
    return render(request, 'rating.html')
