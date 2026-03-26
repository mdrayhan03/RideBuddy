from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from .models import Ride
from bookings.models import Booking
from .services import create_ride, join_ride, format_ride, get_active_ride_for_user, get_ride_map_data, calculate_wait_left, RideMatcher

@login_required
def available_ride_student(request):
    if not request.user.is_student:
        return redirect('accounts:home_rider')
    return render(request, 'available_ride_student.html')

@login_required
def confirm_ride_student(request):
    if not request.user.is_student:
        return redirect('accounts:home_rider')
    return render(request, 'confirm_ride_student.html', {'student': request.user.student_profile})

@login_required
def ride_start_rider(request):
    if not request.user.is_rider:
        return redirect('accounts:home_student')
    return render(request, 'ride_start_rider.html')

def active_rides_json(request):
    """
    Returns active rides with detailed profile (Rider/Driver/Owner) and passenger information.
    """
    booking_id = request.GET.get('booking_id')
    booking = None
    matches = None

    if booking_id:
        try:
            booking = Booking.objects.get(id=booking_id)
            matcher = RideMatcher(booking)
            matches = matcher.match()
        except Booking.DoesNotExist:
            pass

    active_rides_data = []
    if matches is not None:
        for match in matches:
            active_rides_data.append(format_ride(
                match['ride'], 
                similarity=match['similarity'], 
                ref_booking=booking
            ))
    else:
        rides = Ride.objects.filter(status='active').select_related(
            'rider', 'vehicle', 'rider__user', 'created_by'
        ).prefetch_related('bookings', 'bookings__student__user')
        for ride in rides:
            active_rides_data.append(format_ride(ride))

    response_data = {'rides': active_rides_data}
    if booking:
        response_data['user_fare'] = float(booking.fare)
        response_data['user_distance'] = float(booking.distance)
        response_data['booking_id'] = booking.id

    return JsonResponse(response_data)

@login_required
def ride_student(request):
    if not request.user.is_student:
        return redirect('accounts:home_rider')
    return render(request, 'ride_student.html', {'student': request.user.student_profile})

@login_required
def ride_host_student(request):
    if not request.user.is_student:
        return redirect('accounts:home_rider')
        
    active_ride = get_active_ride_for_user(request.user)
    
    ride_data = None
    map_data_json = "null"
    wait_left = 0
    
    if active_ride:
        ride_data = format_ride(active_ride, current_user=request.user)
        map_data = get_ride_map_data(active_ride)
        map_data_json = json.dumps(map_data) if map_data else "null"
        wait_left = calculate_wait_left(active_ride)
        
    return render(request, 'ride_host_student.html', {
        'ride': ride_data,
        'map_data': map_data_json,
        'wait_left': wait_left
    })

@login_required
def ride_host_rider(request):
    if not request.user.is_rider:
        return redirect('accounts:home_student')
        
    active_ride = get_active_ride_for_user(request.user)
    map_data_json = "null"
    if active_ride:
        map_data = get_ride_map_data(active_ride)
        map_data_json = json.dumps(map_data) if map_data else "null"
        
    return render(request, 'ride_host_rider.html', {'map_data': map_data_json})

@login_required
def ride_live_rider(request):
    if not request.user.is_rider:
        return redirect('accounts:home_student')
    return render(request, 'ride_live_rider.html')

@login_required
def ride_live_student(request):
    if not request.user.is_student:
        return redirect('accounts:home_rider')
    return render(request, 'ride_live_student.html')

@login_required
def get_ride_details_api(request, ride_id):
    """
    Returns detailed JSON data for a specific ride.
    """
    try:
        # Handle both admin and student access safely
        student = getattr(request.user, 'student_profile', None)
        ride = Ride.objects.select_related('rider', 'vehicle', 'rider__user').prefetch_related('bookings', 'bookings__student__user').get(id=ride_id)
        
        # Optional: Get extra booking details for map routing
        booking_info = None
        user_booking_id = request.GET.get('booking_id')
        if user_booking_id and student:
            try:
                b = Booking.objects.get(id=user_booking_id, student=student)
                booking_info = {
                    'id': b.id,
                    'start_latlon': b.start_latlon,
                    'end_latlon': b.end_latlon,
                    'waypoints': b.waypoints
                }
            except Booking.DoesNotExist:
                pass
            
        map_data = get_ride_map_data(ride)

        return JsonResponse({
            'success': True, 
            'ride': format_ride(ride),
            'map_data': map_data,
            'user_booking': booking_info
        })
    except Ride.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Ride not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def create_ride_api(request):
    """
    Creates a Ride object from a student's booking.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        student = request.user.student_profile
        booking_id = data.get('booking_id')
        
        if not booking_id:
            return JsonResponse({'success': False, 'message': 'Booking ID required'}, status=400)

        result = create_ride(
            student=student,
            booking_id=booking_id,
            drive_mode=data.get('drive_mode', 'self'),
            use_own_vehicle=data.get('use_own_vehicle', True),
            gender=data.get('gender_preference', 'any')
        )
        
        return JsonResponse(result, status=200 if result['success'] else 400)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def join_ride_api(request):
    """
    Handles a student joining an existing ride.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        student = request.user.student_profile
        ride_id = data.get('ride_id')
        booking_id = data.get('booking_id')

        if not ride_id or not booking_id:
            return JsonResponse({'success': False, 'message': 'Ride ID and Booking ID required'}, status=400)

        result = join_ride(
            student=student,
            ride_id=ride_id,
            booking_id=booking_id,
            use_own_vehicle=data.get('use_own_vehicle', False),
            drive_mode=data.get('drive_mode', 'self')
        )

        return JsonResponse(result, status=200 if result['success'] else 400)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
