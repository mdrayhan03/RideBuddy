from locust import HttpUser, task, between
import random
import json

class RideBuddyUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3) # Wait 1-3 seconds between tasks

    def on_start(self):
        """Simulate logging in and setting headers."""
        self.headers = {'Content-Type': 'application/json'}
        self.booking_id = None
        self.ride_id = None

        # 1. Fetch CSRF token
        self.client.get("/login/", name="/login/")
        csrf_token = self.client.cookies.get("csrftoken")
        if csrf_token:
            self.headers["X-CSRFToken"] = csrf_token

        # 2. Login as the seeded stress user
        login_payload = {
            "username": "stress_user",
            "password": "stresspass123"
        }
        self.client.post(
            "/login-api/",
            data=json.dumps(login_payload),
            headers=self.headers,
            name="/login-api/"
        )

    @task(3)
    def view_available_rides(self):
        """Heavy operation: querying matched rides using cosine similarity."""
        params = {}
        if self.booking_id:
            params['booking_id'] = self.booking_id
        
        self.client.get("/rides/active-rides-json/", params=params, name="/rides/active-rides-json/")

    @task(1)
    def create_and_cancel_booking(self):
        """Simulate the complete process of creating an instant ride request."""
        # Create booking request
        booking_data = {
            "pickup_name": "EWU Campus, Aftabnagar",
            "drop_name": "Rampura Bridge",
            "pickup_lat": 23.768, "pickup_lng": 90.425,
            "drop_lat": 23.761, "drop_lng": 90.420,
            "distance": 3.2,
            "ride_type": random.choice(["car", "bike"]),
            "booking_type": "instant",
            "preference": {"ac": "True", "gender": "any"}
        }
        
        response = self.client.post(
            "/create-booking-api/",
            data=json.dumps(booking_data),
            headers=self.headers,
            name="/create-booking-api/"
        )
        
        if response.status_code == 200:
            try:
                res_data = response.json()
                if res_data.get('success'):
                    self.booking_id = res_data.get('booking_id')
                    
                    # Instantly simulate wait threshold tracking
                    self.client.get("/student-activity-api/", name="/student-activity-api/")
                    
                    # Cleanup: Cancel booking to keep database clean during long runs
                    cancel_payload = {
                        "id": self.booking_id,
                        "type": "searching"
                    }
                    self.client.post(
                        "/cancel-activity-api/",
                        data=json.dumps(cancel_payload),
                        headers=self.headers,
                        name="/cancel-activity-api/"
                    )
                    self.booking_id = None
            except Exception:
                pass

    @task(2)
    def send_live_location_updates(self):
        """Simulate real-time map location updates."""
        loc_payload = {
            "latitude": 23.76 + random.uniform(-0.01, 0.01),
            "longitude": 90.42 + random.uniform(-0.01, 0.01)
        }
        # Simulate updating user's location
        self.client.post(
            "/update-location-api/",
            data=json.dumps(loc_payload),
            headers=self.headers,
            name="/update-location-api/",
            catch_response=True
        )
