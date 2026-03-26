import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import timedelta
from django.utils import timezone
from ..models import Booking

class BookingMatcher:
    """
    A service class to match a given booking with other pending bookings 
    based on time, preference, and waypoint similarity using built-in cosine similarity.
    """

    def __init__(self, target_booking, threshold=0.8, top_n=10):
        self.target_booking = target_booking
        self.threshold = threshold
        self.top_n = top_n
        self.resample_size = 50  # Increased for better accuracy with many points

    def get_route_vector(self, booking):
        """
        Converts waypoints into a fixed-size vector for built-in cosine similarity.
        """
        waypoints_data = booking.waypoints
        points = []
        if waypoints_data and isinstance(waypoints_data, dict):
            points = waypoints_data.get('points', [])
        elif isinstance(waypoints_data, list):
            points = waypoints_data

        if not points or len(points) < 2:
            # Fallback to start/end points if waypoints are missing
            if booking.start_latlon and booking.end_latlon:
                points = [
                    [booking.start_latlon.get('lng'), booking.start_latlon.get('lat')],
                    [booking.end_latlon.get('lng'), booking.end_latlon.get('lat')]
                ]
            else:
                return np.zeros((1, self.resample_size * 2))

        # points are expected as [[lng, lat], ...]
        data = np.array(points)
        
        if data.ndim != 2 or data.shape[1] < 2:
            return np.zeros((1, self.resample_size * 2))

        # Separate coordinates
        lngs = data[:, 0]
        lats = data[:, 1]

        # Resample to common size for fixed-length vector comparison
        x_new = np.linspace(0, 1, self.resample_size)
        x_old = np.linspace(0, 1, len(data))
        
        resampled_lngs = np.interp(x_new, x_old, lngs)
        resampled_lats = np.interp(x_new, x_old, lats)
        
        # Flatten to a single vector [lng1, lng2... lat1, lat2...]
        vector = np.concatenate([resampled_lngs, resampled_lats]).reshape(1, -1)
        
        return vector

    def calculate_similarity(self, vec1, vec2):
        """
        Uses sklearn's built-in cosine_similarity.
        """
        if np.all(vec1 == 0) or np.all(vec2 == 0):
            return 0.0
        
        return float(cosine_similarity(vec1, vec2)[0][0])

    def is_time_compatible(self, b1, b2):
        """
        Checks if the timing of two bookings overlaps within their waiting windows.
        """
        t1 = b1.scheduled_start or timezone.now()
        t2 = b2.scheduled_start or timezone.now()
        
        # Buffer window is the average of their thresholds or a default of 15 mins
        threshold1 = timedelta(minutes=getattr(b1, 'waiting_threshold', 15))
        threshold2 = timedelta(minutes=getattr(b2, 'waiting_threshold', 15))
        
        diff = abs(t1 - t2)
        # Compatible if the difference is within the combined window
        return diff <= (threshold1 + threshold2) / 2

    def check_preference(self, b1, b2):
        """
        Ensures gender and AC preferences are respected.
        """
        pref1 = b1.preference.get('gender', 'any') if b1.preference else 'any'
        pref2 = b2.preference.get('gender', 'any') if b2.preference else 'any'
        
        ac1 = b1.preference.get('ac', 'any') if b1.preference else 'any'
        ac2 = b2.preference.get('ac', 'any') if b2.preference else 'any'
        
        if pref1 != 'any' and pref2 != 'any':
            if pref1 != pref2:
                return False
                
        if ac1 != 'any' and ac2 != 'any':
            if str(ac1).lower() != str(ac2).lower():
                return False
                
        return True

    def match(self):
        """
        Finds matching pending bookings.
        """
        # 1. Fetch pending bookings excluding current one
        pending_bookings = Booking.objects.filter(status='pending').exclude(id=self.target_booking.id)
        
        results = []
        target_vector = self.get_route_vector(self.target_booking)
        
        for booking in pending_bookings:
            # 2. Check basic filters: Ride Type, Time, and Preference
            if booking.ride_type != self.target_booking.ride_type:
                continue
                
            if not self.is_time_compatible(self.target_booking, booking):
                continue
            
            if not self.check_preference(self.target_booking, booking):
                continue
            
            # 3. Calculate waypoint similarity
            other_vector = self.get_route_vector(booking)
            similarity = self.calculate_similarity(target_vector, other_vector)
            
            if similarity >= self.threshold:
                results.append({
                    'booking': booking,
                    'similarity': float(similarity)
                })
        
        # 4. Sort by similarity and return top N
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:self.top_n]
