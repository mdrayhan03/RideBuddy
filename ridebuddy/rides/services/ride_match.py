import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import timedelta
from django.utils import timezone
from ..models import Ride
from bookings.services.booking_match import BookingMatcher

class RideMatcher:
    """
    A service class to match a given booking with existing active rides.
    """

    def __init__(self, target_booking, threshold=0.8, top_n=10):
        self.target_booking = target_booking
        self.threshold = threshold
        self.top_n = top_n
        self.matcher_util = BookingMatcher(target_booking) # Reuse route vector logic

    def check_ride_preferences(self, ride, target_booking):
        """
        Check if the target booking is compatible with ALL existing bookings in the ride.
        """
        target_pref = target_booking.preference.get('gender', 'any') if target_booking.preference else 'any'
        
        for existing_booking in ride.bookings.all():
            existing_pref = existing_booking.preference.get('gender', 'any') if existing_booking.preference else 'any'
            
            # If any booking (target or existing) restricts gender, they must match
            if target_pref != 'any' and existing_pref != 'any':
                if target_pref != existing_pref:
                    return False
            
            # Special case: If existing booking ONLY wants female, target must be female
            # Note: We need to know target user's gender, but assuming pref matches roles for now.
            # In a real app, you'd check request.user.gender vs existing_pref.
            
        return True

    def is_time_compatible(self, ride, booking):
        """
        Checks if the ride's scheduled start is within the booking's time window.
        """
        t_ride = ride.scheduled_start or timezone.now()
        t_book = booking.scheduled_start or timezone.now()
        
        threshold_ride = timedelta(minutes=getattr(ride, 'waiting_threshold', 15))
        threshold_book = timedelta(minutes=getattr(booking, 'waiting_threshold', 15))
        
        diff = abs(t_ride - t_book)
        return diff <= (threshold_ride + threshold_book) / 2

    def match(self):
        """
        Finds matching active rides for the target booking.
        """
        # 1. Fetch active rides with same ride_type (via vehicle)
        # We assume target_booking.ride_type matches ride.vehicle.vehicle_type
        active_rides = Ride.objects.filter(status='active').select_related('vehicle').prefetch_related('bookings')
        
        results = []
        target_vector = self.matcher_util.get_route_vector(self.target_booking)
        
        if np.all(target_vector == 0):
            return []

        for ride in active_rides:
            # Basic Filter: Ride Type
            if ride.vehicle and ride.vehicle.vehicle_type != self.target_booking.ride_type:
                continue

            # Basic Filter: Time
            if not self.is_time_compatible(ride, self.target_booking):
                continue
            
            # Check Preferences against all bookings in the ride
            if not self.check_ride_preferences(ride, self.target_booking):
                continue
            
            # Waypoint Matching: Find the "best" reference booking in the ride
            # Logic: Highest waypoint count or distance
            all_bookings = list(ride.bookings.all())
            if not all_bookings:
                # Ride started but no bookings? Highly unlikely but handle it.
                # Use ride's own metadata if available, otherwise skip.
                continue
                
            # Pick reference: booking with most points in 'waypoints' and largest distance
            reference_booking = max(all_bookings, key=lambda b: (
                len(b.waypoints.get('points', [])) if isinstance(b.waypoints, dict) else 0,
                float(b.distance or 0)
            ))
            
            ref_vector = self.matcher_util.get_route_vector(reference_booking)
            similarity = self.matcher_util.calculate_similarity(target_vector, ref_vector)
            
            if similarity >= self.threshold:
                results.append({
                    'ride': ride,
                    'similarity': float(similarity),
                    'reference_booking': reference_booking
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:self.top_n]
