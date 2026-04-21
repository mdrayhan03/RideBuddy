from django.db.models import Q
from decimal import Decimal

def format_ride(ride, similarity=None, ref_booking=None, current_user=None):
    """
    Utility function to format ride data.
    Moves logic from views to service to keep views clean.
    """
    from rides.models import Ride
    from bookings.models import Booking
    
    bookings = ride.bookings.all()
    
    # Determine Rider/Driver Info
    rider_info = {
        'name': 'Searching Rider...',
        'photo': None,
        'type': 'Searching', # 'Self Drive', 'Driver'
        'is_hired': False
    }
    
    # The Host is the creator of the ride
    host_student = ride.created_by

    if ride.rider:
        user = ride.rider.user
        rider_info['name'] = user.get_full_name() or user.username
        rider_info['photo'] = user.profile_picture.url if user.profile_picture else None
        rider_info['license_no'] = ride.rider.license_no
        rider_info['license_picture'] = ride.rider.license_picture.url if ride.rider.license_picture else None
        rider_info['phone'] = user.phone_no
        
        # Check if rider is driving themselves (Self-Drive)
        is_self_drive = False
        ride_has_vehicle = ride.vehicle is not None
        vehicle_owner_user = None
        if ride_has_vehicle and hasattr(ride.vehicle, 'student_owner') and ride.vehicle.student_owner:
            vehicle_owner_user = ride.vehicle.student_owner.user

        rider_info['is_host'] = (host_student and host_student.user == user)
        rider_info['is_owner'] = (vehicle_owner_user and vehicle_owner_user == user)
        if host_student and host_student.user == user:
            is_self_drive = True
            rider_info['type'] = 'Self Drive (Host)'
        elif vehicle_owner_user and vehicle_owner_user == user:
            is_self_drive = True
            rider_info['type'] = 'Self Drive'
        else:
            rider_info['type'] = 'Rider / Driver'
            rider_info['is_hired'] = True
            
        rider_info['is_self_drive'] = is_self_drive

    elif ride.vehicle and hasattr(ride.vehicle, 'student_owner') and ride.vehicle.student_owner:
        user = ride.vehicle.student_owner.user
        rider_info['name'] = user.get_full_name() or user.username
        rider_info['photo'] = user.profile_picture.url if user.profile_picture else None
        rider_info['phone'] = user.phone_no
        rider_info['is_host'] = (host_student and host_student.user == user)
        rider_info['is_owner'] = True
        if host_student and host_student.user == user:
            rider_info['type'] = 'Self Drive (Host)'
            rider_info['is_self_drive'] = True
        else:
            rider_info['type'] = 'Vehicle Owner'
            rider_info['is_self_drive'] = False

    # Vehicle Info
    has_vehicle = ride.vehicle is not None
    vehicle_data = {
        'has_vehicle': has_vehicle,
        'model': ride.vehicle.vehicle_model if has_vehicle else 'No Vehicle Assigned',
        'plate_no': ride.vehicle.vehicle_plate_no if has_vehicle else 'N/A',
        'tax_token_photo': ride.vehicle.tax_token_picture.url if has_vehicle and ride.vehicle.tax_token_picture else None,
        'ac': ride.vehicle.ac_available if has_vehicle else False,
        'capacity': ride.vehicle.capacity if has_vehicle else 2
    }

    # Passenger Info
    passengers_data = []
    rider_is_in_booking = False
    rider_user = ride.rider.user if ride.rider else None
    
    for b in bookings:
        p_user = b.student.user
        is_host = (host_student == b.student)
        is_vehicle_owner = has_vehicle and hasattr(ride.vehicle, 'student_owner') and (ride.vehicle.student_owner == b.student)
        
        is_rider = False
        if rider_user and p_user == rider_user:
            is_rider = True
            rider_is_in_booking = True
            
        passengers_data.append({
            'name': p_user.get_full_name() or p_user.username,
            'photo': p_user.profile_picture.url if p_user.profile_picture else None,
            'is_host': is_host,
            'is_owner': is_vehicle_owner,
            'is_rider': is_rider,
            'initial': p_user.first_name[0] if p_user.first_name else p_user.username[0].upper(),
            'id_no': b.student.id_no,
            'id_photo': b.student.id_picture.url if b.student.id_picture else None,
            'phone': p_user.phone_no,
            'booking_id': b.id,
            'fare': float(b.fare),
            'pickup': b.start_location,
            'drop': b.end_location,
            'waypoints': b.waypoints,
            'start_latlon': b.start_latlon,
            'end_latlon': b.end_latlon,
            'pickup_data': b.pickup,
            'dropoff_data': b.dropoff,
            'status': b.status,
            'is_picked_up': b.pickup is not None,
            'is_user': (p_user == current_user) if current_user else False
        })

    # Calculate Seats
    total_capacity = vehicle_data['capacity']
    
    joined_passenger_count = len(bookings)
    if rider_is_in_booking:
        joined_passenger_count -= 1
        
    # Formula: Passenger Capacity - Other Passengers
    # Since rider_is_in_booking reduces joined_passenger_count, 
    # it effectively makes +1 seat available compared to a normal passenger.
    available_seats = total_capacity - joined_passenger_count

    # Price
    total_fare = sum(float(b.fare) for b in bookings)
    price = 0
    if ref_booking:
        price = float(ref_booking.fare)
    elif bookings.exists():
        price = float(bookings.first().fare)

    return {
        'id': ride.id,
        'status': ride.status,
        'rider': rider_info,
        'vehicle': vehicle_data,
        'passengers': passengers_data,
        'joined_passenger_count': joined_passenger_count,
        'rider_is_in_booking': rider_is_in_booking,
        'vehicle_model': vehicle_data['model'],
        'has_vehicle': has_vehicle,
        'total_seats': total_capacity,
        'available_seats': max(0, available_seats),
        'price': price,
        'total_fare': total_fare,
        'route_summary': f"{bookings.first().start_location.split(',')[0]} → {bookings.first().end_location.split(',')[0]}" if bookings.exists() else "No path",
        'similarity': round(similarity * 100, 1) if similarity is not None else None,
        'ride_type': bookings.first().booking_type if bookings.exists() else 'instant',
        'scheduled_start': ride.scheduled_start.isoformat() if ride.scheduled_start else None,
        'waiting_threshold': ride.waiting_threshold,
        'ac_available': vehicle_data['ac'],
        'created_at': ride.created_at.isoformat(),
        'gender': bookings.filter(student=host_student).first().preference.get('gender', 'any') if host_student and bookings.filter(student=host_student).exists() else 'any'
    }

def get_active_ride_for_user(user):
    """
    Fetches the latest active ride for a rider or student.
    """
    from rides.models import Ride
    
    if user.is_rider:
        return Ride.objects.filter(
            rider=user.rider_profile,
            status__in=['active', 'started']
        ).order_by('-created_at').first()
    
    if user.is_student:
        return Ride.objects.filter(
            bookings__student=user.student_profile,
            status__in=['active', 'started']
        ).order_by('-created_at').first()
        
    return None

def create_ride(student, booking_id, drive_mode='self', use_own_vehicle=True, gender='any'):
    """
    Business logic for creating a ride.
    """
    from rides.models import Ride
    from bookings.models import Booking
    
    try:
        booking = Booking.objects.get(id=booking_id, student=student)
    except Booking.DoesNotExist:
        return {'success': False, 'message': 'Booking not found.'}

    # Check if this specific booking is already in a ride
    if Ride.objects.filter(bookings=booking).exclude(status__in=['completed', 'cancelled']).exists():
        return {'success': False, 'message': 'This booking is already part of an active ride.'}
            
    # Check if the Rider/Vehicle is currently busy with another ride
    active_ride_exists = False
    if student.user.is_rider and hasattr(student.user, 'rider_profile'):
            active_ride_exists = Ride.objects.filter(rider=student.user.rider_profile).exclude(status__in=['completed', 'cancelled']).exists()
    
    if not active_ride_exists:
            # Check if their car/rider is already hosting something
            active_ride_exists = Ride.objects.filter(rider__employer_student=student).exclude(status__in=['completed', 'cancelled']).exists()
            
    if active_ride_exists:
            return {'success': False, 'message': 'You or your vehicle are already busy in an active ride.'}

    # Update booking preference with gender
    if not booking.preference:
            booking.preference = {}
    booking.preference['gender'] = gender
    booking.save()

    # Create the Ride with creator student
    ride = Ride.objects.create(
        created_by=student,
        status='active'
    )

    if use_own_vehicle and student.has_vehicle:
        ride.vehicle = student.vehicle
        
        if drive_mode == 'self' and hasattr(student.user, 'rider_profile'):
            ride.rider = student.user.rider_profile
        elif drive_mode == 'driver':
            # Assign their hired driver if they have one
            hired_rider = student.hired_riders.first()
            if hired_rider:
                ride.rider = hired_rider

    ride.bookings.add(booking)
    
    # Update booking status to accepted
    booking.status = 'accepted'
    booking.save()
    
    ride.save()
    
    # Ensure owner fare is 0
    update_owner_fare(ride)
    
    # Calculate total fare based on bookings
    ride.update_total_fare()

    return {
        'success': True,
        'message': 'Ride created successfully!',
        'ride_id': ride.id
    }

def join_ride(student, ride_id, booking_id, use_own_vehicle=False, drive_mode='self'):
    """
    Business logic for joining a ride.
    """
    from rides.models import Ride
    from bookings.models import Booking
    
    try:
        ride = Ride.objects.get(id=ride_id)
        booking = Booking.objects.get(id=booking_id, student=student)
    except Ride.DoesNotExist:
        return {'success': False, 'message': 'Ride not found'}
    except Booking.DoesNotExist:
        return {'success': False, 'message': 'Booking not found'}

    # 1. Check if student is already in a ride
    if Ride.objects.filter(bookings=booking).exclude(status__in=['completed', 'cancelled']).exists():
            return {'success': False, 'message': 'You are already in an active ride'}

    # 2. Update Rider/Vehicle if needed
    if not ride.rider and not ride.vehicle and use_own_vehicle and student.has_vehicle:
            # This student is "taking over" the ride as a rider/provider
            ride.vehicle = student.vehicle
            if drive_mode == 'self' and hasattr(student.user, 'rider_profile'):
                ride.rider = student.user.rider_profile
            elif drive_mode == 'driver':
                hired_rider = student.hired_riders.first()
                if hired_rider:
                    ride.rider = hired_rider
            
            if not ride.created_by:
                ride.created_by = student
    
    # 3. Check if ride is full
    if ride.vehicle:
        if ride.bookings.count() >= ride.vehicle.capacity:
                return {'success': False, 'message': 'Ride is already full'}
    else:
        if ride.bookings.count() >= 4:
            return {'success': False, 'message': 'Ride request is full'}

    ride.bookings.add(booking)
    
    # Update booking status to accepted
    booking.status = 'accepted'
    booking.save()
    
    ride.save()
    
    # Ensure owner fare is 0
    update_owner_fare(ride)

    # Calculate total fare based on bookings
    ride.update_total_fare()

    return {
        'success': True, 
        'message': 'Joined ride successfully!',
        'ride_id': ride.id
    }

def get_ride_map_data(ride):
    """
    Compiles map markers and routing data for a ride based on business logic.
    Identifies the "Main Ride" path and assigns specific icons based on user roles.
    """
    from bookings.models import Booking
    from rides.models import Ride

    bookings = ride.bookings.select_related('student', 'student__user').all()
    if not bookings.exists():
        return None

    # 1. Determine "Main" Route (Largest waypoints count and distance)
    # The longest path (usually the host/rider's) defines the primary route line.
    main_booking = None
    max_score = -1
    
    for b in bookings:
        points_count = 0
        if b.waypoints and isinstance(b.waypoints, dict):
            # Prefer 'count' key if available as per user spec, otherwise len of points
            points_count = b.waypoints.get('count', len(b.waypoints.get('points', [])))
        
        # Scoring based on distance and waypoint complexity
        score = (float(b.distance or 0) * 10) + points_count
        if score > max_score:
            max_score = score
            main_booking = b
            
    if not main_booking:
        main_booking = bookings.first()

    # 2. Compile Markers & Filter Logic
    markers = []
    rider_user = ride.rider.user if ride.rider else None
    host_student = ride.created_by
    has_vehicle = ride.vehicle is not None
    
    # A. Rider/Vehicle Marker (Always priority for tracking)
    # If the ride has started or is active, we track the rider's phone location.
    if rider_user:
        latest_loc = rider_user.locations.order_by('-updated_at').first()
        if latest_loc:
            markers.append({
                'id': f'rider_{rider_user.id}',
                'type': 'rider',
                'name': rider_user.get_full_name() or rider_user.username,
                'lat': latest_loc.latitude,
                'lng': latest_loc.longitude,
                'icon': '/static/assets/media/vehiclemarker.png',
                'popup': f"<b>Vehicle:</b> {ride.vehicle.vehicle_model if has_vehicle else 'Rider'}<br>Plate: {ride.vehicle.vehicle_plate_no if has_vehicle else 'N/A'}",
                'is_live': True
            })

    # B. Passenger Markers (Start & End Points + Live Location)
    passenger_colors = ['memberblue.png', 'memberred.png']
    live_passenger_colors = ['liveblue.png', 'livered.png']
    color_idx = 0
    
    for b in bookings:
        student = b.student
        p_user = student.user
        
        # LOGIC: If student is also the rider, ignore their specific booking markers
        # We focus on the 'vehiclemarker' for the rider's actual live position instead.
        if rider_user and p_user == rider_user:
            continue
            
        is_host = (host_student == student)
        is_owner = has_vehicle and hasattr(ride.vehicle, 'student_owner') and (ride.vehicle.student_owner == student)
        
        # Icon Color Logic: Owner (Yellow) > Host (Green) > Others (Blue/Red)
        if is_owner:
            icon_name = 'memberyellow.png'
            live_icon_name = 'liveyellow.png'
        elif is_host:
            icon_name = 'membergreen.png'
            live_icon_name = 'livegreen.png'
        else:
            idx = color_idx % len(passenger_colors)
            icon_name = passenger_colors[idx]
            live_icon_name = live_passenger_colors[idx]
            color_idx += 1
            
        icon_url = f'/static/assets/media/{icon_name}'
        live_icon_url = f'/static/assets/media/{live_icon_name}'
        name_display = p_user.get_full_name() or p_user.username
        
        # 1. Static Markers (Pickup & Drop)
        if b.start_latlon:
            markers.append({
                'id': f'booking_start_{b.id}',
                'type': 'pickup',
                'name': name_display,
                'lat': b.start_latlon.get('lat'),
                'lng': b.start_latlon.get('lng'),
                'icon': icon_url,
                'popup': f"<b>{name_display} (Pickup)</b><br>{b.start_location}"
            })
            
        if b.end_latlon:
            markers.append({
                'id': f'booking_end_{b.id}',
                'type': 'drop',
                'name': name_display,
                'lat': b.end_latlon.get('lat'),
                'lng': b.end_latlon.get('lng'),
                'icon': icon_url,
                'popup': f"<b>{name_display} (Destination)</b><br>{b.end_location}"
            })

        # 2. Live Location Marker
        # Fetch latest location from UserLocation for the passenger
        latest_p_loc = p_user.locations.order_by('-updated_at').first()
        if latest_p_loc:
            markers.append({
                'id': f'live_user_{p_user.id}',
                'type': 'student_live',
                'name': name_display,
                'lat': latest_p_loc.latitude,
                'lng': latest_p_loc.longitude,
                'icon': live_icon_url,
                'popup': f"<b>{name_display}</b><br>Live Tracking",
                'is_live': True
            })

    # 3. Routing Data (LRM Waypoints)
    # The "Main Route" defined by the host/best-path booking
    main_waypoints = []
    if main_booking.start_latlon:
        main_waypoints.append({'lat': main_booking.start_latlon['lat'], 'lng': main_booking.start_latlon['lng']})
        
    # Other passenger points act as mid-waypoints if they exist
    for b in bookings:
        # Ignore if this booking belongs to the person who is also the rider
        if rider_user and b.student.user == rider_user:
            continue
            
        if b != main_booking:
            if b.start_latlon:
                main_waypoints.append({'lat': b.start_latlon['lat'], 'lng': b.start_latlon['lng']})
            if b.end_latlon:
                main_waypoints.append({'lat': b.end_latlon['lat'], 'lng': b.end_latlon['lng']})
                
    if main_booking.end_latlon:
        main_waypoints.append({'lat': main_booking.end_latlon['lat'], 'lng': main_booking.end_latlon['lng']})

    return {
        'ride_id': ride.id,
        'main_booking_id': main_booking.id,
        'is_live': ride.status in ['active', 'started'],
        'waypoints': main_waypoints,
        'markers': markers,
        'main_route_geometry': main_booking.waypoints # Optional for direct drawing
    }

def calculate_wait_left(ride):
    """
    Calculates remaining wait time in minutes based on created_at and waiting_threshold.
    """
    from django.utils import timezone
    import math
    
    if not ride.created_at or not ride.waiting_threshold:
        return 0
        
    now = timezone.now()
    elapsed = now - ride.created_at
    elapsed_minutes = elapsed.total_seconds() / 60
    
    remaining = ride.waiting_threshold - elapsed_minutes
    return max(0, math.floor(remaining))

def update_owner_fare(ride):
    """
    If any booking in the ride belongs to the owner of the ride's vehicle, sets its fare to 0.
    """
    if not ride.vehicle or not hasattr(ride.vehicle, 'student_owner') or not ride.vehicle.student_owner:
        return
        
    owner_student = ride.vehicle.student_owner
    owner_bookings = ride.bookings.filter(student=owner_student)
    for b in owner_bookings:
        if b.fare != Decimal('0.00'):
            b.fare = Decimal('0.00')
            b.save()
