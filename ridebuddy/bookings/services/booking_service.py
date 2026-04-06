from django.utils import timezone
from ..models import Booking
from rides.models import Ride
from reviews.services.review_service import generate_pending_reviews, generate_pending_platform_review, generate_pending_reviews_for_rider

def update_pickup_status(booking_id, rider_location, user_location):
    """
    Updates the pickup status of a booking.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        pickup_data = {
            'pickup': 'done',
            'time': timezone.now().isoformat(),
            'vehicle_location': rider_location, # [lat, lon]
            'location': user_location # [lat, lon]
        }
        
        booking.pickup = pickup_data
        booking.status = 'accepted' # Ensure it's accepted
        booking.save()
        
        return True, "Pickup recorded successfully"
    except Booking.DoesNotExist:
        return False, "Booking not found"
    except Exception as e:
        return False, str(e)

def update_drop_status(booking_id, rider_location, user_location):
    """
    Updates the drop status of a booking.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if the ride has started
        ride = booking.rides.first()
        if ride and ride.status == 'active':
            return False, "You cannot drop a passenger before starting the ride"

        # Structure defined by USER
        dropoff_data = {
            'drop': 'done',
            'time': timezone.now().isoformat(),
            'vehicle_location': rider_location, # [lat, lon]
            'location': user_location # [lat, lon]
        }
        
        booking.dropoff = dropoff_data
        booking.status = 'completed'
        booking.save()
        
        # Generate pending reviews for the student who was just dropped off
        generate_pending_reviews(booking)
        
        # If this is the student's 3rd completed booking, generate a platform review
        completed_bookings_count = Booking.objects.filter(student=booking.student, status='completed').count()
        if completed_bookings_count == 3:
            generate_pending_platform_review(booking.student.user)
        
        # Check if all bookings in the associated ride are completed
        ride = booking.rides.first()
        if ride:
            total_bookings = ride.bookings.count()
            completed_bookings = ride.bookings.filter(status='completed').count()
            
            if total_bookings > 0 and total_bookings == completed_bookings:
                ride.status = 'completed'
                ride.dropped_time = timezone.now()
                ride.save()
                
                # Generate reviews triggered specifically when a Ride completes (for the Rider)
                generate_pending_reviews_for_rider(ride)
                
        return True, "Drop-off recorded successfully"
    except Booking.DoesNotExist:
        return False, "Booking not found"
    except Exception as e:
        return False, str(e)

def update_booking_preferences(booking_id, student, preferences):
    """
    Updates the preferences of a booking.
    """
    try:
        booking = Booking.objects.get(id=booking_id, student=student)
        
        if not booking.preference:
            booking.preference = {}
        
        # Merge new preferences into existing ones
        # Special check for ride_type mapping
        if 'ride_type' in preferences:
            booking.ride_type = preferences['ride_type']
            del preferences['ride_type']
            
        booking.preference.update(preferences)
        booking.save()
        
        return True, "Preferences updated"
    except Booking.DoesNotExist:
        return False, "Booking not found"
    except Exception as e:
        return False, str(e)
