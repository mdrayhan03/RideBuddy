from ..models import RiderReview, VehicleReview, PassengerReview, PlatformReview, StudentReview

def generate_pending_reviews(booking):
    """
    Creates pending review objects for a given completed booking.
    This effectively builds a 'To-Do list' of reviews for the student.
    """
    try:
        # A booking should be linked to a ride
        ride = booking.rides.first()
        if not ride:
            return False, "Booking is not associated with any ride."

        # 1. Create a pending review for the Rider
        if hasattr(ride, 'rider') and ride.rider:
            RiderReview.objects.get_or_create(
                reviewer=booking,
                rider=ride.rider,
                ride=ride,
                defaults={'status': 'pending'}
            )

        # 2. Create a pending review for the Vehicle
        if hasattr(ride, 'vehicle') and ride.vehicle:
            VehicleReview.objects.get_or_create(
                reviewer=booking,
                vehicle=ride.vehicle,
                ride=ride,
                defaults={'status': 'pending'}
            )

        # 3. Create a pending review for Co-Passengers (if any)
        # Identify the driver's user to handle 'self-drive' edge cases
        driver_user_id = ride.rider.user.id if (hasattr(ride, 'rider') and ride.rider) else None

        # Exclude the current booking
        other_bookings = ride.bookings.exclude(id=booking.id)
        
        for other_booking in other_bookings:
            # If the current booking is the self-driving rider, or the other booking is the self-driving rider,
            # we skip creating PassengerReviews between them (Driver vs Passenger is handled by RiderReview).
            if driver_user_id:
                if booking.student.user.id == driver_user_id or other_booking.student.user.id == driver_user_id:
                    continue

            # You (the current booking) review them
            PassengerReview.objects.get_or_create(
                reviewer=booking,
                whom_reviewed=other_booking,
                ride=ride,
                defaults={'status': 'pending'}
            )
            
            # They review you (so you appear in their 'to-do' list)
            PassengerReview.objects.get_or_create(
                reviewer=other_booking,
                whom_reviewed=booking,
                ride=ride,
                defaults={'status': 'pending'}
            )

        return True, "Pending reviews generated successfully."
    except Exception as e:
        return False, str(e)

def generate_pending_reviews_for_rider(ride):
    """
    Called when a ride is completed (all bookings finished).
    Generates StudentReviews (Rider reviewing Student) and PlatformReview for the Rider.
    """
    try:
        if not hasattr(ride, 'rider') or not ride.rider:
            return False, "No rider found for this ride."

        # 1. Create StudentReview for each completed passenger
        for booking in ride.bookings.filter(status='completed'):
            # Check if self-drive to avoid self-review
            if ride.rider.user != booking.student.user:
                StudentReview.objects.get_or_create(
                    reviewer=ride.rider,
                    student_booking=booking,
                    ride=ride,
                    defaults={'status': 'pending'}
                )

        # 2. Check if Rider needs a Platform Review (e.g. after 3 completed rides)
        from rides.models import Ride
        completed_rides_count = Ride.objects.filter(rider=ride.rider, status='completed').count()
        if completed_rides_count == 3:
            generate_pending_platform_review(ride.rider.user)
            
        return True, "Pending reviews for rider generated successfully."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


def generate_pending_platform_review(user):
    """
    Creates a pending platform review object for a given user.
    """
    try:
        PlatformReview.objects.get_or_create(
            user=user,
            defaults={'status': 'pending'}
        )
        return True, "Pending platform review generated successfully."
    except Exception as e:
        return False, str(e)

