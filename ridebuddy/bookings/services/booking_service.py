from django.utils import timezone
from ..models import Booking
from rides.models import Ride

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
        
        # Check if all bookings in the associated ride are completed
        ride = booking.rides.first() # ride_host_rider context
        if ride:
            all_completed = ride.bookings.exclude(status='completed').count() == 0
            if all_completed:
                ride.status = 'completed'
                ride.dropped_time = timezone.now()
                ride.save()
        
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
        booking.preference.update(preferences)
        booking.save()
        
        return True, "Preferences updated"
    except Booking.DoesNotExist:
        return False, "Booking not found"
    except Exception as e:
        return False, str(e)
