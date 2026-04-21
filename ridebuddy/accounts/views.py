from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db import transaction
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from django.contrib.auth.forms import PasswordChangeForm
import json
import random
import base64
import traceback
from .models import User, UserLocation, OTP, Student, Rider, Community, Vehicle

@ensure_csrf_cookie
def index(request):
    if request.user.is_authenticated:
        # Check session for preferred role mode
        active_role = request.session.get('active_role')
        
        if active_role == 'rider' and request.user.is_rider:
            return redirect('accounts:home_rider')
        elif active_role == 'student' and request.user.is_student:
            return redirect('accounts:home_student')
            
        # Default priority
        if request.user.is_student:
             return redirect('accounts:home_student')
        elif request.user.is_rider:
             return redirect('accounts:home_rider')
    return render(request, 'index.html')

@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        active_role = request.session.get('active_role')
        if active_role == 'rider' and request.user.is_rider:
            return redirect('accounts:home_rider')
        elif active_role == 'student' and request.user.is_student:
            return redirect('accounts:home_student')

        if request.user.is_student:
             return redirect('accounts:home_student')
        elif request.user.is_rider:
             return redirect('accounts:home_rider')
    return render(request, 'login.html')

@csrf_exempt
def update_location_api(request):
    """
    API for real-time location tracking. Supports both Student and Rider.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        if lat is None or lng is None:
            return JsonResponse({'message': 'Coordinates missing'}, status=400)
            
        # Try to update existing record OR create new one safely
        location = UserLocation.objects.filter(user=request.user).first()
        if location:
            location.latitude = lat
            location.longitude = lng
            location.save()
        else:
            UserLocation.objects.create(
                user=request.user,
                latitude=lat,
                longitude=lng
            )
        
        return JsonResponse({'success': True, 'message': 'Location updated'})
        
    except Exception as e:
        print(f"Location Update Error: {str(e)}") # Log for server debugging
        return JsonResponse({'message': str(e)}, status=500)

@login_required
def get_participant_locations_api(request):
    """
    Fetches the latest locations of all participants for a specific ride.
    Query Params: ride_id
    """
    ride_id = request.GET.get('ride_id')
    if not ride_id:
        return JsonResponse({'success': False, 'message': 'Ride ID missing'}, status=400)
        
    try:
        from rides.models import Ride
        ride = Ride.objects.get(id=ride_id)
        
        # All users involved in the ride
        users_in_ride = []
        if ride.rider:
            users_in_ride.append(ride.rider.user)
            
        for b in ride.bookings.all():
            if b.student.user not in users_in_ride:
                users_in_ride.append(b.student.user)
                
        locations = []
        for user in users_in_ride:
            loc = UserLocation.objects.filter(user=user).order_by('-updated_at').first()
            if loc:
                locations.append({
                    'user_id': user.id,
                    'name': user.get_full_name() or user.username,
                    'is_rider': hasattr(user, 'rider_profile') and (ride.rider and user == ride.rider.user),
                    'lat': loc.latitude,
                    'lng': loc.longitude,
                    'last_updated': loc.updated_at.isoformat()
                })
                
        return JsonResponse({
            'success': True,
            'locations': locations
        })
    except Ride.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Ride not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def login_api(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        identifier = data.get('username') # This is the multi-purpose identifier
        password = data.get('password')
        
        # 1. Try Authenticate by Username (Standard)
        user = authenticate(request, username=identifier, password=password)
        
        # 2. Try Authenticate by Email
        if user is None:
            try:
                candidate = User.objects.get(email=identifier)
                user = authenticate(request, username=candidate.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            # Standard login
            login(request, user)
            
            # Handle Remember Me
            remember_me = data.get('remember_me', False)
            if remember_me:
                # 2 weeks
                request.session.set_expiry(1209600)
            else:
                # Browser close
                request.session.set_expiry(0)
            
            # Django's middleware will handle session persistence automatically
            
            
            # Determine redirect based on role
            # Determine redirection based on preferred role
            request.session['active_role'] = 'student' if user.is_student else 'rider'
            
            if user.is_student:
                redirect_url = reverse('accounts:home_student')
            elif user.is_rider:
                redirect_url = reverse('accounts:home_rider')
            else:
                return JsonResponse({'message': 'User has no assigned role (Student/Rider)'}, status=403)
                
            return JsonResponse({
                'success': True,
                'message': 'Login successful! Redirecting...',
                'redirect_url': redirect_url,
                'user': {
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'username': user.username,
                    'profile_pic': user.profile_picture.url if user.profile_picture else None,
                    'is_student': user.is_student,
                    'is_rider': user.is_rider
                }
            })
        else:
            return JsonResponse({'success': False, 'message': 'Invalid credentials. Please check your username/email/license and password.'}, status=401)
            
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def logout_api(request):
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})

@login_required
@csrf_exempt
def switch_role_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        target_role = data.get('role') # 'student' or 'rider'
        
        if target_role == 'student' and not request.user.is_student:
            return JsonResponse({'success': False, 'message': 'You do not have a student profile'}, status=403)
        if target_role == 'rider' and not request.user.is_rider:
            return JsonResponse({'success': False, 'message': 'You do not have a rider profile'}, status=403)
            
        request.session['active_role'] = target_role
        
        redirect_url = reverse('accounts:home_student') if target_role == 'student' else reverse('accounts:home_rider')
        
        return JsonResponse({
            'success': True, 
            'message': f'Switched to {target_role} view',
            'redirect_url': redirect_url
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



@ensure_csrf_cookie
def signup_view(request):
    communities = Community.objects.all()
    return render(request, 'signup.html', {'communities': communities})

def data_url_to_file(data_url, name_prefix):
    if not data_url or ';base64,' not in data_url:
        return None
    format, imgstr = data_url.split(';base64,')
    ext = format.split('/')[-1]
    return ContentFile(base64.b64decode(imgstr), name=f"{name_prefix}.{ext}")

@transaction.atomic
def signup_api(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        community_id = data.get('community')
        community = Community.objects.get(id=community_id)
        
        id_no = data.get('iub_id')
        username = f"{id_no}_{community.short_name}".lower()
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'message': 'User with this ID already exists in this community'}, status=400)

        # 1. Create Student User
        student_user = User.objects.create_user(
            username=username,
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'), # Primary official email
            phone_no=data.get('phone_no'), # Primary phone
            emergency_contact=data.get('emergency_phone'),
            is_student=True,
            is_active=False # Deactivated until OTP verification
        )
        
        # 2. Generate and Send OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        OTP.objects.create(user=student_user, code=otp_code, otp_type='signup')
        
        send_mail(
            'Verify your RideBuddy Account',
            f'Hi {student_user.first_name}, your 6-digit verification code is: {otp_code}',
            None, # Uses DEFAULT_FROM_EMAIL from settings
            [student_user.email],
            fail_silently=False,
        )
        
        # Save profile picture
        if data.get('profile_pic'):
            student_user.profile_picture = data_url_to_file(data.get('profile_pic'), f"{username}_profile")
            student_user.save()

        # 2. Create Student Profile
        student_profile = Student.objects.create(
            user=student_user,
            id_no=id_no,
            community=community,
            alternative_email=data.get('alt_email'),
            has_vehicle=data.get('has_car')
        )
        
        # Save ID card picture
        if data.get('id_card_pic'):
            student_profile.id_picture = data_url_to_file(data.get('id_card_pic'), f"{username}_id_card")
            student_profile.save()

        # 3. Handle Vehicle if applicable
        vehicle = None
        if data.get('has_car'):
            car_info = data.get('car_info')
            vehicle = Vehicle.objects.create(
                vehicle_type=data.get('vehicle_type', 'car'),
                vehicle_model=car_info.get('model'),
                vehicle_plate_no=car_info.get('car_no'),
                capacity=car_info.get('total_seats')
            )
            
            if car_info.get('tax_token'):
                vehicle.tax_token_picture = data_url_to_file(car_info.get('tax_token'), f"{car_info.get('car_no')}_tax_token")
                vehicle.save()
            
            student_profile.vehicle = vehicle
            drive_type = car_info.get('drive_type')
            student_profile.driver_type = 'self_drive' if drive_type == 'self' else 'has_driver'
            student_profile.save()

            # 4. Create Rider Profile
            if drive_type == 'self':
                # Student is the rider - update phone if they are self-driving
                student_user.is_rider = True
                student_user.save()
                
                rider_profile = Rider.objects.create(
                    user=student_user,
                    employer_student=student_profile,
                    vehicle=vehicle,
                    license_no=data.get('student_license', {}).get('no')
                )
                
                if data.get('student_license', {}).get('pic'):
                    rider_profile.license_picture = data_url_to_file(data.get('student_license', {}).get('pic'), f"{username}_license")
                    rider_profile.save()
            
            elif drive_type == 'driver':
                # Create a new user for the rider
                rider_info = data.get('rider_info')
                # Generate a unique username for rider: student_username_rider
                rider_username = f"{username}_rider".lower()
                
                # Check if rider username exists
                if User.objects.filter(username=rider_username).exists():
                    email_prefix = rider_info.get('email').split('@')[0]
                    rider_username = f"{username}_{email_prefix}_rider".lower()

                rider_user = User.objects.create_user(
                    username=rider_username,
                    password="DefaultPassword123!", # Should probably be handled better
                    first_name=rider_info.get('first_name'),
                    last_name=rider_info.get('last_name'),
                    email=rider_info.get('email'),
                    phone_no=rider_info.get('phone_no'),
                    emergency_contact=rider_info.get('emergency_no'),
                    is_rider=True,
                    is_verified=student_user.is_verified,
                    is_active=student_user.is_active
                )
                
                if rider_info.get('profile_pic'):
                    rider_user.profile_picture = data_url_to_file(rider_info.get('profile_pic'), f"{rider_username}_profile")
                    rider_user.save()

                rider_profile = Rider.objects.create(
                    user=rider_user,
                    employer_student=student_profile,
                    vehicle=vehicle,
                    license_no=rider_info.get('license_no')
                )
                
                if rider_info.get('license_pic'):
                    rider_profile.license_picture = data_url_to_file(rider_info.get('license_pic'), f"{rider_username}_license")
                    rider_profile.save()

        return JsonResponse({
            'success': True, 
            'message': 'Account created! Please verify your email.',
            'username': username
        })
        
    except Community.DoesNotExist:
        return JsonResponse({'message': 'Invalid community selected'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def verify_otp_api(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        otp_code = data.get('otp')
        
        user = User.objects.get(username=username)
        latest_otp = user.otps.filter(is_used=False).order_by('-created_at').first()
        
        if latest_otp and latest_otp.code == otp_code:
            latest_otp.is_used = True
            latest_otp.save()
            
            user.is_active = True
            user.is_verified = True
            user.save()
            
            # If student is verified, their hired rider (if any) should also be verified
            if user.is_student and hasattr(user, 'student_profile'):
                hired_riders = Rider.objects.filter(employer_student=user.student_profile)
                for rider in hired_riders:
                    rider_user = rider.user
                    rider_user.is_verified = True
                    rider_user.is_active = True
                    rider_user.save()

            # Log the user in
            login(request, user)
            
            # Determine redirect based on role
            if user.is_student:
                redirect_url = reverse('accounts:home_student')
            else:
                redirect_url = reverse('accounts:home_rider')

            return JsonResponse({
                'success': True,
                'message': 'Email verified successfully!',
                'redirect_url': redirect_url
            })
        else:
            return JsonResponse({'success': False, 'message': 'Invalid verification code'}, status=400)
            
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@login_required
def home_rider(request):
    if not request.user.is_rider:
        return redirect('accounts:home_student')
    
    # Determine if we are viewing as a self-driving student or a hired rider
    from rides.services import get_active_ride_for_user, format_ride, get_ride_map_data
    
     # This finds the ride where the user is involved
    
    # Identifty the rider profile
    rider_profile = Rider.objects.filter(user=request.user).first()
    
    # Debug info for the terminal
    print(f"DEBUG: Logged-in User: {request.user.username} ({request.user.get_full_name()})")
    print(f"DEBUG: Found Rider Profile: {rider_profile}")
    
    active_ride = get_active_ride_for_user(request.user)
    active_ride_data = None
    map_data = None
    if active_ride:
        active_ride_data = format_ride(active_ride, current_user=request.user)
        map_data = get_ride_map_data(active_ride)
        
    map_data_json = json.dumps(map_data) if map_data else "null"
    
    latest_location = request.user.locations.order_by('-updated_at').first()
    location_data = {'lat': latest_location.latitude, 'lng': latest_location.longitude} if latest_location else None
    
    # Priority: 
    # 1. If we found a Rider profile for this user account (hired or self), use this user.
    # 2. Fallback to request.user
    display_user = request.user
    if rider_profile and rider_profile.user:
        display_user = rider_profile.user

    print(f"DEBUG: Displaying as: {display_user.get_full_name()}")
    
    from reviews.models import StudentReview, PlatformReview
    pending_review = None
    review_type = None
    review_target = ""

    pending_student = StudentReview.objects.filter(reviewer=rider_profile, status='pending').first() if rider_profile else None
    if pending_student:
        pending_review = pending_student
        review_type = 'student'
        review_target = pending_student.student_booking.student.user.get_full_name() or pending_student.student_booking.student.user.username
    else:
        pending_platform = PlatformReview.objects.filter(user=request.user, status='pending').first()
        if pending_platform:
            pending_review = pending_platform
            review_type = 'platform'
            review_target = "RideBuddy Platform"

    context = {
        'active_ride': active_ride_data,
        'map_data': map_data_json,
        'rider_location': location_data,
        'display_user': display_user
    }
    
    if pending_review:
        context['pending_review'] = {
            'id': pending_review.id,
            'type': review_type,
            'target_name': review_target
        }

    return render(request, 'home_rider.html', context)

@login_required
def home_student(request):
    if not request.user.is_student:
        if request.user.is_rider:
            return redirect('accounts:home_rider')
        # If neither student nor rider, send to login
        return redirect('accounts:login')
        
    from reviews.models import RiderReview, VehicleReview, PassengerReview, PlatformReview
    
    pending_review = None
    review_type = None
    review_target = ""

    # Priority 1: Rider Review
    if hasattr(request.user, 'student_profile'):
        pending_rider = RiderReview.objects.filter(reviewer__student=request.user.student_profile, status='pending').first()
        if pending_rider:
            pending_review = pending_rider
            review_type = 'rider'
            review_target = pending_rider.rider.user.get_full_name() or pending_rider.rider.user.username
        else:
            # Priority 2: Vehicle Review
            pending_vehicle = VehicleReview.objects.filter(reviewer__student=request.user.student_profile, status='pending').first()
            if pending_vehicle:
                pending_review = pending_vehicle
                review_type = 'vehicle'
                review_target = pending_vehicle.vehicle.vehicle_plate_no
            else:
                # Priority 3: Passenger Review
                pending_passenger = PassengerReview.objects.filter(reviewer__student=request.user.student_profile, status='pending').first()
                if pending_passenger:
                    pending_review = pending_passenger
                    review_type = 'passenger'
                    review_target = pending_passenger.whom_reviewed.student.user.get_full_name() or pending_passenger.whom_reviewed.student.user.username
                else:
                    # Priority 4: Platform Review
                    pending_platform = PlatformReview.objects.filter(user=request.user, status='pending').first()
                    if pending_platform:
                        pending_review = pending_platform
                        review_type = 'platform'
                        review_target = "RideBuddy Platform"

    context = {}
    if pending_review:
        context['pending_review'] = {
            'id': pending_review.id,
            'type': review_type,
            'target_name': review_target
        }

    return render(request, 'home_student.html', context)

@login_required
def account_view(request):
    return render(request, 'account.html')

def settings_view(request):
    return render(request, 'settings.html')

def wallet_view(request):
    return render(request, 'wallet.html')

@login_required
def about_view(request):
    return render(request, 'about.html')

@login_required
def edit_profile_view(request):
    communities = Community.objects.all()
    return render(request, 'edit_profile.html', {'communities': communities})
@csrf_exempt
@login_required
@transaction.atomic
def update_student_api(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update Basic User Fields
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone_no = data.get('phone_no', user.phone_no)
        user.emergency_contact = data.get('emergency_phone', user.emergency_contact)
        
        if data.get('profile_pic'):
            user.profile_picture = data_url_to_file(data.get('profile_pic'), f"{user.username}_profile")
        
        user.save()

        # Update Student Specific Fields
        if user.is_student:
            student_profile = user.student_profile
            student_profile.alternative_email = data.get('alt_email', student_profile.alternative_email)
            
            if data.get('id_card_pic'):
                student_profile.id_picture = data_url_to_file(data.get('id_card_pic'), f"{user.username}_id_card")
            
            if data.get('community'):
                student_profile.community = Community.objects.get(id=data.get('community'))
            
            has_vehicle = data.get('has_vehicle', False)
            student_profile.has_vehicle = has_vehicle
            student_profile.save()
        
        if has_vehicle:
            vehicle_data = data.get('vehicle_info', {})
            drive_type = vehicle_data.get('drive_type') # 'self' or 'driver'
            student_profile.driver_type = 'self_drive' if drive_type == 'self' else 'has_driver'
            
            # Update or Create Vehicle
            vehicle = student_profile.vehicle
            if not vehicle:
                vehicle = Vehicle.objects.create(
                    vehicle_type=vehicle_data.get('vehicle_type', 'car'),
                )
                student_profile.vehicle = vehicle
            
            vehicle.vehicle_model = vehicle_data.get('model')
            vehicle.vehicle_plate_no = vehicle_data.get('plate_no')
            vehicle.capacity = vehicle_data.get('capacity')
            
            if vehicle_data.get('tax_token_pic'):
                vehicle.tax_token_picture = data_url_to_file(vehicle_data.get('tax_token_pic'), f"{vehicle.vehicle_plate_no}_tax_token")
            
            vehicle.save()
            student_profile.save()
            
            # Handle Rider Profiles
            if drive_type == 'self':
                # Student is the rider
                request.user.is_rider = True
                request.user.save()
                
                rider_profile = Rider.objects.filter(user=request.user).first()
                if not rider_profile:
                    rider_profile = Rider.objects.create(
                        user=request.user,
                        employer_student=student_profile,
                        vehicle=vehicle
                    )
                else:
                    rider_profile.employer_student = student_profile
                    rider_profile.vehicle = vehicle
                
                rider_profile.license_no = vehicle_data.get('license_no')
                if vehicle_data.get('license_pic'):
                    rider_profile.license_picture = data_url_to_file(vehicle_data.get('license_pic'), f"{request.user.username}_license")
                rider_profile.save()
            
            elif drive_type == 'driver':
                # Hired driver
                rider_info = data.get('rider_info', {})
                # Find existing hired rider or create new one
                rider_profile = student_profile.hired_riders.first()
                
                if not rider_profile:
                    # Create a new user for the rider: student_username_rider
                    rider_email = rider_info.get('email')
                    rider_username = f"{student_profile.user.username}_rider".lower()
                    
                    if User.objects.filter(username=rider_username).exists():
                        email_prefix = rider_email.split('@')[0]
                        rider_username = f"{student_profile.user.username}_{email_prefix}_rider".lower()
                    
                    rider_user = User.objects.create_user(
                        username=rider_username,
                        password="DefaultPassword123!",
                        first_name=rider_info.get('first_name'),
                        last_name=rider_info.get('last_name'),
                        email=rider_email,
                        phone_no=rider_info.get('phone_no'),
                        emergency_contact=rider_info.get('emergency_no'),
                        is_rider=True,
                        is_verified=request.user.is_verified,
                        is_active=request.user.is_active
                    )
                    rider_profile = Rider.objects.create(
                        user=rider_user,
                        employer_student=student_profile,
                        vehicle=vehicle
                    )
                else:
                    rider_user = rider_profile.user
                    rider_user.first_name = rider_info.get('first_name')
                    rider_user.last_name = rider_info.get('last_name')
                    rider_user.email = rider_info.get('email')
                    rider_user.phone_no = rider_info.get('phone_no')
                    rider_user.emergency_contact = rider_info.get('emergency_no')
                    rider_user.save()
                    
                    rider_profile.vehicle = vehicle
                
                if rider_info.get('profile_pic'):
                    rider_user.profile_picture = data_url_to_file(rider_info.get('profile_pic'), f"{rider_user.username}_profile")
                    rider_user.save()
                
                rider_profile.save()

        # Independent Rider Field Updates (for hired riders or direct rider edits)
        if user.is_rider:
            rider_profile = getattr(user, 'rider_profile', None)
            if rider_profile:
                if 'license_no' in data:
                    rider_profile.license_no = data.get('license_no')
                if data.get('license_pic'):
                    rider_profile.license_picture = data_url_to_file(data.get('license_pic'), f"{user.username}_license")
                rider_profile.save()
                
        else:
            student_profile.save()
            
        return JsonResponse({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
@login_required
def change_password_api(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        form = PasswordChangeForm(user=request.user, data=data)
        
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            return JsonResponse({'success': True, 'message': 'Password changed successfully'})
        else:
            # Extract form errors
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(error)
            return JsonResponse({'success': False, 'message': errors[0] if errors else 'Invalid data'}, status=400)
            
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

from rides.models import OwnerCommission
from django.utils import timezone

@login_required
def payments_view(request):
    if not request.user.is_student:
        return redirect('accounts:account')
        
    student_profile = request.user.student_profile
    due_payments = OwnerCommission.objects.filter(owner=student_profile, payment_status='due').order_by('-invoice_date')
    history_payments = OwnerCommission.objects.filter(owner=student_profile).exclude(payment_status='due').order_by('-invoice_date')
    
    return render(request, 'payment.html', {
        'due_payments': due_payments,
        'history_payments': history_payments,
    })

@login_required
def invoice_view(request, commission_id):
    try:
        commission = OwnerCommission.objects.get(id=commission_id, owner=request.user.student_profile)
    except OwnerCommission.DoesNotExist:
        return redirect('accounts:payments')
        
    return render(request, 'invoice.html', {'commission': commission})

@login_required
def make_payment_view(request, commission_id):
    try:
        commission = OwnerCommission.objects.get(id=commission_id, owner=request.user.student_profile)
    except OwnerCommission.DoesNotExist:
        return redirect('accounts:payments')
        
    if commission.payment_status == 'paid':
        return redirect('accounts:invoice', commission_id=commission.id)
        
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        payment_id = request.POST.get('payment_id')
        if payment_method and payment_id:
            commission.payment_method = payment_method
            commission.payment_id = payment_id
            commission.payment_status = 'paid'
            commission.payment_date = timezone.now().date()
            commission.save()
            return redirect('accounts:invoice', commission_id=commission.id)
            
    methods = OwnerCommission.PAYMENT_METHOD_CHOICES
    instructions = OwnerCommission.PAYMENT_INSTRUCTION_DICT
    
    return render(request, 'make_payment.html', {
        'commission': commission,
        'methods': methods,
        'instructions': instructions,
        'instructions_json': json.dumps(instructions)
    })
