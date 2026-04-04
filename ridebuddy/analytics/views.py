from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from accounts.models import User
from rides.models import Ride
from bookings.models import Booking

def is_analytics_user(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name__iexact='analytics').exists() or user.is_staff)

def analytics_login_view(request):
    if request.user.is_authenticated and is_analytics_user(request.user):
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate by username or email
        user = authenticate(request, username=identifier, password=password)
        if user is None:
            try:
                candidate = User.objects.get(email=identifier)
                user = authenticate(request, username=candidate.username, password=password)
            except User.DoesNotExist:
                pass
                
        if user is not None:
            if is_analytics_user(user):
                login(request, user)
                next_url = request.GET.get('next', '/analytics/dashboard/')
                return redirect(next_url)
            else:
                error = "You do not have permission to access the analytics dashboard."
                return render(request, 'analytics/login.html', {'error': error})
        else:
            error = "Invalid username or password."
            return render(request, 'analytics/login.html', {'error': error})
            
    return render(request, 'analytics/login.html')

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def dashboard_view(request):
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate
    from django.utils import timezone
    from datetime import timedelta
    
    total_users = User.objects.count()
    total_students = User.objects.filter(is_student=True).count()
    total_riders = User.objects.filter(is_student=False, is_superuser=False).count()
    total_rides = Ride.objects.count()
    completed_rides = Ride.objects.filter(status='completed').count()
    
    total_bookings = Booking.objects.count()
    gross_income = Booking.objects.filter(status='completed').aggregate(Sum('fare'))['fare__sum'] or 0
    total_income = float(gross_income) * 0.10

    # Bookings Distribution
    pending_bookings = Booking.objects.filter(status='pending').count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()

    # Ride Distribution (assuming status field exists)
    active_rides = Ride.objects.exclude(status__in=['completed', 'cancelled']).count()
    cancelled_rides = Ride.objects.filter(status='cancelled').count()
    
    # Trend Data Generation (Last 7 Days)
    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    date_labels = [d.strftime('%b %d') for d in last_7_days]

    def get_daily_counts(queryset, date_field):
        daily_counts = queryset.filter(**{f"{date_field}__date__gte": last_7_days[0]}) \
                               .annotate(date=TruncDate(date_field)) \
                               .values('date') \
                               .annotate(count=Count('id'))
        counts_dict = {item['date']: item['count'] for item in daily_counts}
        return [counts_dict.get(d, 0) for d in last_7_days]

    ride_trend = get_daily_counts(Ride.objects.filter(status='completed'), 'created_at')
    booking_trend = get_daily_counts(Booking.objects.all(), 'created_at')
    
    # Cumulative User Growth
    user_trend = []
    base_users = User.objects.filter(date_joined__date__lt=last_7_days[0]).count()
    daily_new_users = get_daily_counts(User.objects.all(), 'date_joined')
    current_total = base_users
    for new_u in daily_new_users:
        current_total += new_u
        user_trend.append(current_total)

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_riders': total_riders,
        'completed_rides': completed_rides,
        'total_bookings': total_bookings,
        'total_income': total_income,
        
        # Distributions for Pie Charts
        'completed_bookings': completed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'active_rides': active_rides,
        'cancelled_rides': cancelled_rides,
        
        # Trends
        'date_labels': date_labels,
        'ride_trend': ride_trend,
        'booking_trend': booking_trend,
        'user_trend': user_trend,
    }
    return render(request, 'analytics/dashboard.html', context)

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def students_view(request):
    students_list = User.objects.filter(is_student=True).select_related('student_profile').order_by('-date_joined')
    paginator = Paginator(students_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'analytics/students.html', {'page_obj': page_obj})

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def riders_view(request):
    from django.db.models import Q
    riders_list = User.objects.filter(
        Q(rider_profile__isnull=False) | Q(student_profile__driver_type='self_drive')
    ).select_related('rider_profile', 'student_profile').distinct().order_by('-date_joined')
    paginator = Paginator(riders_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'analytics/riders.html', {'page_obj': page_obj})

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def vehicles_view(request):
    from accounts.models import Vehicle
    vehicles_list = Vehicle.objects.select_related('student_owner__user').all().order_by('-id')
    paginator = Paginator(vehicles_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'analytics/vehicles.html', {'page_obj': page_obj})

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def reviews_view(request):
    from reviews.models import RiderReview
    reviews_list = RiderReview.objects.select_related('rider__user', 'reviewer__student__user', 'ride').all().order_by('-created_at')
    paginator = Paginator(reviews_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'analytics/reviews.html', {'page_obj': page_obj})

from django.shortcuts import get_object_or_404

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def student_detail_view(request, pk):
    student_user = get_object_or_404(User.objects.select_related('student_profile', 'student_profile__vehicle'), pk=pk, is_student=True)
    student_profile = getattr(student_user, 'student_profile', None)
    
    total_bookings = 0
    total_rides = 0
    vehicle = None
    riders = []
    
    if student_profile:
        from bookings.models import Booking
        from rides.models import Ride
        from accounts.models import Rider
        total_bookings = Booking.objects.filter(student=student_profile).count()
        total_rides = Ride.objects.filter(bookings__student=student_profile).distinct().count()
        vehicle = student_profile.vehicle
        riders = Rider.objects.filter(employer_student=student_profile)
        
    context = {
        'student': student_user,
        'student_profile': student_profile,
        'total_bookings': total_bookings,
        'total_rides': total_rides,
        'vehicle': vehicle,
        'riders': riders,
    }
    return render(request, 'analytics/student_detail.html', context)

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def rider_detail_view(request, pk):
    from rides.models import Ride
    from django.db.models import Sum

    rider_user = get_object_or_404(User.objects.select_related('rider_profile', 'student_profile'), pk=pk)
    rider_profile = getattr(rider_user, 'rider_profile', None)
    student_profile = getattr(rider_user, 'student_profile', None)
    
    total_rides = 0
    gross_income = 0
    
    if rider_profile:
        rides = Ride.objects.filter(rider=rider_profile, status='completed')
        total_rides = rides.count()
        gross_income = rides.aggregate(Sum('bookings__fare'))['bookings__fare__sum'] or 0
    elif student_profile and student_profile.driver_type == 'self_drive':
        rides = Ride.objects.filter(created_by=student_profile, status='completed')
        total_rides = rides.count()
        gross_income = rides.aggregate(Sum('bookings__fare'))['bookings__fare__sum'] or 0

    return render(request, 'analytics/rider_detail.html', {
        'rider': rider_user,
        'rider_profile': rider_profile,
        'student_profile': student_profile,
        'total_rides': total_rides,
        'gross_income': gross_income,
    })

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def vehicle_detail_view(request, pk):
    from accounts.models import Vehicle
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'analytics/vehicle_detail.html', {'vehicle': vehicle})

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def review_detail_view(request, pk):
    from reviews.models import RiderReview
    review = get_object_or_404(RiderReview.objects.select_related('rider__user', 'reviewer__student__user', 'ride'), pk=pk)
    return render(request, 'analytics/review_detail.html', {'review': review})

@user_passes_test(is_analytics_user, login_url='/analytics/login/')
def profile_view(request):
    from django.contrib import messages
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_no = request.POST.get('phone_no', user.phone_no)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
            
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('analytics:profile')
    
    return render(request, 'analytics/profile.html')
