from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

@login_required
def activity_rider(request):
    if not request.user.is_rider:
        return redirect('accounts:home_student')
    return render(request, 'activity_rider.html')

@login_required
def activity_student(request):
    if not request.user.is_student:
        return redirect('accounts:home_rider')
    return render(request, 'activity_student.html')

@login_required
def history(request):
    return render(request, 'history.html')

@login_required
def individual_history(request):
    return render(request, 'individual_history.html')

from django.http import JsonResponse
import json
from .models import Booking
from accounts.models import Student
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import datetime

@csrf_exempt
@login_required
def create_booking_api(request):
    """
    Creates a booking for a student. Checks for student profile.
    """
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Prepare booking type
        booking_type = data.get('booking_type')
        if not booking_type:
            # Fallback for older clients or transition
            is_scheduled = data.get('is_scheduled', False)
            booking_type = 'schedule' if is_scheduled else 'instant'
        
        # Look for student profile
        try:
            student = request.user.student_profile
            
            if booking_type == 'instant':
                if Booking.objects.filter(student=student, booking_type='instant').exclude(status__in=['completed', 'cancelled', 'rejected']).exists():
                    return JsonResponse({'success': False, 'message': 'You already have an active instant ride request. Please complete or cancel it first.'}, status=400)
            
            from rides.models import Ride
            # Check if student is currently IN a ride (Started or Active)
            is_in_ride = Ride.objects.filter(bookings__student=student).exclude(status__in=['completed', 'cancelled']).exists()
            
            if not is_in_ride:
                 # Check if their car/rider is busy (if they are car owner)
                 if student.user.is_rider and hasattr(request.user, 'rider_profile'):
                      is_in_ride = Ride.objects.filter(rider=request.user.rider_profile).exclude(status__in=['completed', 'cancelled']).exists()
                 if not is_in_ride:
                      is_in_ride = Ride.objects.filter(rider__employer_student=student).exclude(status__in=['completed', 'cancelled']).exists()
            
            # Block instant bookings if physically in a ride. Allow scheduling future rides.
            if is_in_ride and booking_type == 'instant':
                return JsonResponse({'success': False, 'message': 'You are currently in an active ride.'}, status=400)
                
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Only students can create bookings'}, status=403)
        
        # Calculate fare (base 50 + distance based)
        try:
            distance = float(data.get('distance', 5))
        except (ValueError, TypeError):
            distance = 5
        
        scheduled_start = data.get('scheduled_start')
        waiting_threshold = int(data.get('waiting_threshold', 15))
        
        if scheduled_start:
            # Parse ISO date string
            try:
                scheduled_start = timezone.datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                scheduled_start = None

        booking = Booking.objects.create(
            student=student,
            start_location=data.get('pickup_name'),
            end_location=data.get('drop_name'),
            start_latlon={'lat': data.get('pickup_lat'), 'lng': data.get('pickup_lng')},
            end_latlon={'lat': data.get('drop_lat'), 'lng': data.get('drop_lng')},
            waypoints={
                'points': data.get('waypoints', []),
                'count': len(data.get('waypoints', []))
            },
            distance=distance,
            preference=data.get('preference', {}),
            fare=0, # Temporary
            ride_type=data.get('ride_type', 'car'),
            status='pending',
            booking_type=booking_type,
            scheduled_start=scheduled_start,
            waiting_threshold=waiting_threshold
        )
        
        # Now calculate the real fare using the new logic
        from .services.fare_calculation import calculate_fare
        booking.fare = calculate_fare(booking)
        booking.save()
        
        # Store booking_id in session for ease of access? (Optional)
        request.session['last_booking_id'] = booking.id
        
        return JsonResponse({
            'success': True,
            'message': 'Booking created!',
            'booking_id': booking.id
        })
        
    except Exception as e:
        print(f"CRITICAL Booking Error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def individual_history_student(request):
    # Backward compatibility or redirect
    return redirect('bookings:individual_history')

@login_required
def get_student_activity_api(request):
    """Returns all current active bookings and rides for a student."""
    try:
        student = request.user.student_profile
        activities = []
        has_instant = False
        
        from rides.models import Ride
        
        # 1. Rides being HOSTED by this student (as creator, rider, owner, or employer)
        hosted_rides = Ride.objects.filter(
            models.Q(created_by=student) |
            models.Q(rider__user=request.user) | 
            models.Q(rider__employer_student=student) |
            models.Q(vehicle__student_owner=student)
        ).exclude(status__in=['completed', 'cancelled']).distinct().order_by('-created_at')
        
        hosted_ride_ids = set()
        for ride in hosted_rides:
            is_instant = (ride.scheduled_start is None)
            if is_instant: has_instant = True
            
            hosted_ride_ids.add(ride.id)
            bookings = ride.bookings.all()
            first_booking = bookings.first()
            activities.append({
                'type': 'hosting',
                'id': ride.id,
                'status': ride.status,
                'is_instant': is_instant,
                'passenger_count': bookings.count(),
                'max_seats': (ride.vehicle.capacity - 1) if ride.vehicle else 3,
                'vehicle': ride.vehicle.vehicle_model if ride.vehicle else "Vehicle",
                'pickup': first_booking.start_location if first_booking else "Pickup",
                'drop': first_booking.end_location if first_booking else "Drop",
                'p_lat': first_booking.start_latlon.get('lat') if first_booking and first_booking.start_latlon else None,
                'p_lng': first_booking.start_latlon.get('lng') if first_booking and first_booking.start_latlon else None,
                'd_lat': first_booking.end_latlon.get('lat') if first_booking and first_booking.end_latlon else None,
                'd_lng': first_booking.end_latlon.get('lng') if first_booking and first_booking.end_latlon else None,
            })

        # 2. Bookings where student is a PASSENGER
        # We show: 1. Pending (Searching) 2. Accepted (Riding in someone else's ride)
        passenger_bookings = Booking.objects.filter(student=student, status__in=['pending', 'accepted']).order_by('-created_at')
        
        for booking in passenger_bookings:
            # Check if this booking is already in a Ride
            active_ride = Ride.objects.filter(bookings=booking).exclude(status__in=['completed', 'cancelled']).first()
            
            if active_ride and active_ride.id in hosted_ride_ids:
                # Student is the host of this ride, already added in section 1
                continue

            is_instant = (booking.booking_type == 'instant')
            if is_instant: has_instant = True

            if active_ride:
                # This is the "RIDING" option - matched with a rider
                rider_user = active_ride.rider.user if active_ride.rider else None
                activities.append({
                    'type': 'riding',
                    'id': booking.id,
                    'ride_id': active_ride.id,
                    'is_instant': is_instant,
                    'status': active_ride.status,
                    'rider_name': rider_user.get_full_name() if rider_user else "Searching...",
                    'vehicle': active_ride.vehicle.vehicle_model if active_ride.vehicle else "Car",
                    'pickup': booking.start_location,
                    'drop': booking.end_location,
                    'fare': float(booking.fare)
                })
            elif booking.status == 'pending':
                # This is the "SEARCHING" option - strictly pending
                activities.append({
                    'type': 'searching',
                    'id': booking.id,
                    'is_instant': is_instant,
                    'status': 'searching',
                    'pickup': booking.start_location,
                    'drop': booking.end_location,
                    'fare': float(booking.fare),
                    'p_lat': booking.start_latlon.get('lat') if booking.start_latlon else None,
                    'p_lng': booking.start_latlon.get('lng') if booking.start_latlon else None,
                    'd_lat': booking.end_latlon.get('lat') if booking.end_latlon else None,
                    'd_lng': booking.end_latlon.get('lng') if booking.end_latlon else None,
                })
        
        return JsonResponse({
            'success': True,
            'activities': activities,
            'has_instant': has_instant
        })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def get_rider_activity_api(request):
    """Returns the current active ride for a rider."""
    try:
        if not request.user.is_rider:
            return JsonResponse({'success': False, 'message': 'Not a rider'}, status=403)
            
        from rides.models import Ride
        from django.utils import timezone
        
        # 1. Fetch all non-completed/non-cancelled rides for the rider
        rider_rides = Ride.objects.filter(
            models.Q(rider__user=request.user) | 
            models.Q(rider__employer_student__user=request.user)
        ).exclude(status__in=['completed', 'cancelled']).order_by('-created_at')

        if not rider_rides.exists():
            return JsonResponse({'success': True, 'state': 'none', 'rides': []})
            
        activities = []
        for ride in rider_rides:
            from rides.services import format_ride, get_ride_map_data
            
            # Use format_ride for consistent data across all views
            ride_data = format_ride(ride, current_user=request.user)
            ride_data['map_data'] = get_ride_map_data(ride)
            
            activities.append(ride_data)

        # If there's a ride that is 'started', we prioritize that view
        started_ride = next((r for r in activities if r['status'] == 'started'), None)
        
        return JsonResponse({
            'success': True,
            'state': 'list',
            'rides': activities,
            'server_time': timezone.now().isoformat()
        })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
@csrf_exempt
@login_required
def cancel_activity_api(request):
    """Cancels a booking or a ride."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
        
    try:
        data = json.loads(request.body)
        act_id = data.get('id')
        act_type = data.get('type') # 'hosting' or 'searching'/'riding' (booking)

        if not act_id or not act_type:
            return JsonResponse({'success': False, 'message': 'Missing ID or Type'}, status=400)

        from rides.models import Ride
        
        if act_type == 'ride_status':
            # Update Ride Status (Start/Complete)
            new_status = data.get('status')
            ride = Ride.objects.get(id=act_id)
            # Ensure user is authorized (Rider, Employer of Rider, or the Host/Creator)
            is_authorized = (ride.rider and ride.rider.user == request.user) or \
                            (ride.rider and ride.rider.employer_student.user == request.user) or \
                            (ride.created_by.user == request.user)
            
            if not is_authorized:
                return JsonResponse({'success': False, 'message': 'Unauthorized to update this ride.'}, status=403)
            
            if new_status not in ['started', 'completed']:
                return JsonResponse({'success': False, 'message': 'Invalid status update.'})
                
            if new_status == 'completed':
                ride.status = 'completed'
                from django.utils import timezone
                ride.dropped_time = timezone.now()
                ride.save()
                
                # Mark all associated bookings as completed
                for b in ride.bookings.all():
                    b.status = 'completed'
                    if not b.dropoff:
                         b.dropoff = {'drop': 'done', 'time': timezone.now().isoformat()}
                    b.save()
                
                # Ensure Rider receives their platform/student reviews
                from reviews.services.review_service import generate_pending_reviews_for_rider
                generate_pending_reviews_for_rider(ride)
            else:
                ride.status = new_status
                ride.save()
                
            return JsonResponse({'success': True, 'message': f'Ride {new_status} successfully'})

        elif act_type == 'hosting':
            # Cancel a Ride
            ride = Ride.objects.get(id=act_id)
            # Ensure user is the host/owner
            student = request.user.student_profile
            is_host = (ride.created_by == student) or \
                      (ride.rider and ride.rider.user == request.user) or \
                      (ride.rider and ride.rider.employer_student == student)
            
            if not is_host:
                return JsonResponse({'success': False, 'message': 'Unauthorized to cancel this ride.'}, status=403)
            
            ride.status = 'cancelled'
            ride.save()
            
            for b in ride.bookings.all():
                b.status = 'cancelled'
                b.save()
                
            return JsonResponse({'success': True, 'message': 'Ride cancelled successfully'})

        else:
            # Cancel a Booking
            booking = Booking.objects.get(id=act_id, student=request.user.student_profile)
            booking.status = 'cancelled'
            booking.save()
            
            return JsonResponse({'success': True, 'message': 'Booking cancelled successfully'})
                
    except (Ride.DoesNotExist, Booking.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Activity not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_POST
def update_booking_event_api(request):
    """API for the rider to record pickup/drop events."""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        event_type = data.get('event_type') # 'pickup' or 'drop'
        rider_loc = data.get('rider_location') # [lat, lon]
        user_loc = data.get('user_location') # [lat, lon]
        
        if not booking_id or not event_type:
            return JsonResponse({'success': False, 'message': 'Missing data'}, status=400)
            
        from .services.booking_service import update_pickup_status, update_drop_status
        
        if event_type == 'pickup':
            success, msg = update_pickup_status(booking_id, rider_loc, user_loc)
        elif event_type == 'drop':
            success, msg = update_drop_status(booking_id, rider_loc, user_loc)
        else:
            return JsonResponse({'success': False, 'message': 'Invalid event type'}, status=400)
            
        return JsonResponse({'success': success, 'message': msg})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@login_required
@require_POST
def update_booking_preferences_api(request):
    """
    API to update booking preferences (filters) on every click.
    """
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        preferences = data.get('preferences')

        if not booking_id:
            return JsonResponse({'success': False, 'message': 'Booking ID required'}, status=400)

        from .services.booking_service import update_booking_preferences
        
        student = request.user.student_profile
        success, msg = update_booking_preferences(booking_id, student, preferences)
        
        return JsonResponse({'success': success, 'message': msg}, status=200 if success else 400)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def get_history_api(request):
    try:
        student = request.user.student_profile
        history_items = []
        
        from rides.models import Ride
        
        # 1. Rides hosted by student that are completed or cancelled
        hosted_rides = Ride.objects.filter(
            models.Q(created_by=student) |
            models.Q(rider__user=request.user) | 
            models.Q(rider__employer_student=student) |
            models.Q(vehicle__student_owner=student)
        ).filter(status__in=['completed', 'cancelled']).distinct().order_by('-created_at')
        
        hosted_ride_ids = set()
        for ride in hosted_rides:
            hosted_ride_ids.add(ride.id)
            bookings = ride.bookings.all()
            first_booking = bookings.first()
            history_items.append({
                'id': ride.id,
                'type': 'hosting',
                'status': ride.status,
                'pickup': first_booking.start_location if first_booking else "Pickup",
                'drop': first_booking.end_location if first_booking else "Drop",
                'date': ride.created_at.isoformat(),
                'driver_name': ride.rider.user.get_full_name() if ride.rider else "Unknown",
                'fare': float(sum([b.fare for b in bookings]) if bookings else 0), # total fare generated
            })

        # 2. Bookings where student is PASSENGER (cancelled, rejected, or completed)
        passenger_bookings = Booking.objects.filter(
            student=student, 
            status__in=['completed', 'cancelled', 'rejected']
        ).order_by('-created_at')
        
        for booking in passenger_bookings:
            # Check if this booking is in a Ride we already processed as host
            active_ride = Ride.objects.filter(bookings=booking).first()
            if active_ride and active_ride.id in hosted_ride_ids:
                continue
                
            history_items.append({
                'id': booking.id,
                'type': 'riding', # or searching
                'status': booking.status,
                'pickup': booking.start_location,
                'drop': booking.end_location,
                'date': booking.created_at.isoformat(),
                'driver_name': active_ride.rider.user.get_full_name() if active_ride and active_ride.rider else "Unknown",
                'fare': float(booking.fare)
            })
            
        # Sort history by date descending
        history_items.sort(key=lambda x: x['date'], reverse=True)
        
        return JsonResponse({'success': True, 'history': history_items})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def get_individual_history_api(request):
    try:
        activity_id = request.GET.get('id')
        activity_type = request.GET.get('type') # 'hosting' or 'riding'
        
        if not activity_id or not activity_type:
            return JsonResponse({'success': False, 'message': 'Missing parameters'}, status=400)
            
        student = request.user.student_profile
        from rides.models import Ride
        
        if activity_type == 'hosting':
            ride = Ride.objects.get(id=activity_id)
            # return full ride details
            from rides.services import format_ride, get_ride_map_data
            ride_data = format_ride(ride, current_user=request.user)
            ride_data['map_data'] = get_ride_map_data(ride)
            
            # Add driver information explicitly to response
            driver_info = None
            if ride.rider:
                driver_info = {
                    'name': ride.rider.user.get_full_name(),
                    'phone': getattr(ride.rider, 'mobile_number', None),
                    'is_student': getattr(ride.rider, 'is_student_rider', False),
                }
            
            # Since user is host, show all passengers
            return JsonResponse({'success': True, 'data': ride_data, 'driver': driver_info})
            
        else:
            booking = Booking.objects.get(id=activity_id, student=student)
            active_ride = Ride.objects.filter(bookings=booking).first()
            
            data = {
                'id': booking.id,
                'booking_status': booking.status,
                'pickup_location': booking.start_location,
                'dropoff_location': booking.end_location,
                'fare': float(booking.fare),
                'created_at': booking.created_at.isoformat(),
                'pickup': booking.pickup,
                'dropoff': booking.dropoff,
            }
            
            # map data logic
            map_data = {
                 'pickup': booking.start_latlon,
                 'dropoff': booking.end_latlon,
                 'waypoints': booking.waypoints.get('points', []) if booking.waypoints else []
            }
            data['map_data'] = map_data
            
            if active_ride:
                 data['ride_status'] = active_ride.status
                 data['start_time'] = active_ride.start_time.isoformat() if active_ride.start_time else None
                 data['dropped_time'] = active_ride.dropped_time.isoformat() if active_ride.dropped_time else None
                 data['driver'] = {
                     'name': active_ride.rider.user.get_full_name() if active_ride.rider and hasattr(active_ride.rider, 'user') else (active_ride.created_by.user.get_full_name() if getattr(active_ride, 'created_by', None) else None),
                     'phone': getattr(active_ride.rider.user, 'phone_no', None) if active_ride.rider and hasattr(active_ride.rider, 'user') else getattr(active_ride.created_by.user, 'phone_no', None) if getattr(active_ride, 'created_by', None) else None,
                     'photo': active_ride.rider.user.profile_picture.url if active_ride.rider and hasattr(active_ride.rider, 'user') and active_ride.rider.user.profile_picture else (active_ride.created_by.user.profile_picture.url if getattr(active_ride, 'created_by', None) and active_ride.created_by.user.profile_picture else None),
                     'license_picture': active_ride.rider.license_picture.url if active_ride.rider and active_ride.rider.license_picture else None,
                     'type': 'Rider / Driver',
                 }
                 data['vehicle'] = {
                     'model': active_ride.vehicle.vehicle_model if active_ride.vehicle else None,
                     'plate': active_ride.vehicle.vehicle_plate_no if active_ride.vehicle else None,
                     'color': active_ride.vehicle.vehicle_color if active_ride.vehicle else None,
                     'ac': getattr(active_ride.vehicle, 'ac_available', False) if active_ride.vehicle else None,
                     'tax_token_photo': active_ride.vehicle.tax_token_picture.url if active_ride.vehicle and active_ride.vehicle.tax_token_picture else None,
                 }
                 
                 # Fetch rating given BY THIS STUDENT for THIS RIDE
                 from reviews.models import RiderReview, VehicleReview
                 rider_review = RiderReview.objects.filter(reviewer=booking, ride=active_ride).first()
                 data['rider_rating'] = rider_review.rating if rider_review else None
                 
            return JsonResponse({'success': True, 'data': data})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
