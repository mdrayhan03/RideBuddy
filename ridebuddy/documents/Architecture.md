# System Architecture and Methodology

This document outlines the descriptive architecture of the RideBuddy platform. It is structured to be directly integrated into the Methodology section of a research paper, providing a comprehensive breakdown of the system's components, layers, and data flow.

## 1. High-Level System Architecture

The proposed system follows a **Client-Server Architecture** utilizing a Monolithic framework with service-oriented business logic. The architecture is primarily divided into three main layers: the Presentation Layer (Frontend), the Application Logic Layer (Backend Services), and the Data Persistence Layer (Database). 

The system relies heavily on asynchronous communication (AJAX/Fetch API) to provide a dynamic, Single-Page Application (SPA)-like experience while maintaining the robust security and structured routing of a traditional server-side rendered application.

## 2. Presentation Layer (Client-Side)

The client-side interface is designed to be highly responsive and mobile-first, ensuring accessibility for students and riders on the go.

*   **Core Technologies:** HTML5, CSS3 (with utility frameworks like Bootstrap), and Vanilla JavaScript.
*   **State Management:** The frontend utilizes local browser storage (`localStorage`) to maintain user state (`appState`), current geographical coordinates, and active booking IDs across page reloads, ensuring a seamless user experience.
*   **Dynamic UI Updates:** Instead of full page reloads, the interface uses JavaScript to manipulate the Document Object Model (DOM) dynamically. For instance, the activity dashboard relies on periodic polling (`setInterval`) to fetch real-time ride statuses from the server and updates the UI components accordingly.
*   **Mapping and Geolocation:** The frontend heavily integrates `Leaflet.js` for rendering interactive maps. It uses the browser's native Geolocation API to track user coordinates and plots routes on the map using geographic data returned from routing services.

## 3. Application Logic Layer (Server-Side)

The backend is built using the **Django Web Framework (Python)**, adhering to the Model-View-Template (MVT) architectural pattern. It serves as the central brain of the application, securely processing requests, enforcing business rules, and serving data to the frontend.

*   **API Controllers (Views):** Django views act as API endpoints (e.g., `create_booking_api`, `get_student_activity_api`). These controllers receive JSON payloads from the frontend, validate the data, and route it to the appropriate internal services.
*   **Service Layer Abstraction:** To prevent "fat models" and "fat views", complex business logic is decoupled into a dedicated `services/` directory. This includes:
    *   `RideMatcher` & `BookingMatcher`: Handles the mathematical and logical operations required to match passengers with drivers based on route similarity, time windows, and user preferences (e.g., gender, AC).
    *   `Fare Calculation Service`: Dynamically computes ride costs based on geodetic distance and predefined base fares.
    *   `Review and Commission Services`: Automatically handles post-ride operations like generating pending reviews and calculating platform commissions.
*   **Authentication and Authorization:** Leverages Django's robust authentication middleware to secure endpoints. Custom decorators ensure that only verified students or authorized riders can access specific features.

## 4. Data Persistence Layer (Database)

The system utilizes a relational database management system (RDBMS) configured through the Django Object-Relational Mapper (ORM).

*   **Entity Relationships:** The database is highly normalized, featuring core models such as `Student`, `Rider`, `Vehicle`, `Booking` (representing a passenger's request), and `Ride` (representing the actual trip containing multiple bookings).
*   **Spatial Data Handling:** Geographic locations are stored as serialized JSON structures containing latitude and longitude coordinates, allowing for efficient distance computations via the Haversine formula on the application layer.

## 5. External APIs and Integrations

To facilitate real-world geographical mapping and routing without maintaining an expensive proprietary map server, the architecture integrates several third-party Application Programming Interfaces (APIs):

*   **OSRM (Open Source Routing Machine):** Used to calculate optimal driving routes between pickup and drop-off coordinates. It returns exact route distances and detailed GeoJSON waypoints, which are crucial for the route vectorization in the matching algorithm.
*   **Nominatim / Photon (OpenStreetMap):** Utilized for geocoding and reverse geocoding. This allows the system to convert raw GPS coordinates into human-readable street addresses (e.g., translating a user's location into "Main Street, City") and provides location autocomplete suggestions when users are typing their destinations.

## 6. Algorithmic Workflow (The Matching Engine)

The core scientific contribution of the architecture lies in its Matching Engine (`ride_match.py`). When a `Booking` request is initiated:
1.  **Vectorization:** The OSRM waypoints of the request are converted into a mathematical route vector.
2.  **Filtering:** The engine queries the database for active `Ride` objects, applying hard constraints (time compatibility, vehicle type, and strict passenger preferences).
3.  **Similarity Scoring:** For rides passing the hard constraints, the engine calculates the **Cosine Similarity** between the new request's route vector and the existing ride's reference vector.
4.  **Geofencing:** If the request involves a host offering a vehicle, a strict Haversine distance geofence (e.g., 500 meters) is applied to ensure pickup/drop-off proximity.
5.  **Assignment:** The matches are sorted by their similarity score, and the most optimal rides are returned to the client for final confirmation.

### 6.1 Ridematching Pseudo Algorithm

```text
Algorithm 1: Ride Matching Algorithm
Input: 
    TargetBooking B_t (The incoming ride request)
    ActiveRides R_active (List of currently active rides)
    SimilarityThreshold θ (e.g., 0.8)
    MaxResults N (Number of top matches to return)
Output: 
    Top N Matched Rides sorted by route similarity

1.  v_t ← EXTRACT_ROUTE_VECTOR(B_t)
2.  if IS_ZERO_VECTOR(v_t) then
3.      return []
4.  end if
5.
6.  MatchedRides ← []
7.
8.  for each Ride r in R_active do
9.      // Filter 1: Check Vehicle Type Compatibility
10.     if r.VehicleType ≠ B_t.RideType then
11.         continue
12.     end if
13.
14.     // Filter 2: Check Time Window Compatibility
15.     TimeDiff ← ABS(r.ScheduledStart - B_t.ScheduledStart)
16.     MaxAllowedDiff ← (r.WaitingThreshold + B_t.WaitingThreshold) / 2
17.     if TimeDiff > MaxAllowedDiff then
18.         continue
19.     end if
20.
21.     // Filter 3: Check Passenger Preferences (Gender, AC, etc.)
22.     if not CHECK_PREFERENCES_COMPATIBILITY(r.Bookings, B_t.Preferences) then
23.         continue
24.     end if
25.
26.     // Determine Reference Route for the existing ride
27.     B_ref ← GET_REFERENCE_BOOKING(r.Bookings) // Selected by max waypoints & distance
28.     v_ref ← EXTRACT_ROUTE_VECTOR(B_ref)
29.
30.     // Calculate Route Similarity
31.     SimScore ← COSINE_SIMILARITY(v_t, v_ref)
32.
33.     // Filter 4: Strict Geofence for Vehicle Providers (Carpool Hosts)
34.     if B_t.IsVehicleProvider == TRUE then
35.         DistStart ← HAVERSINE_DISTANCE(B_t.StartLocation, B_ref.StartLocation)
36.         DistEnd ← HAVERSINE_DISTANCE(B_t.EndLocation, B_ref.EndLocation)
37.         
38.         if DistStart > 500 meters OR DistEnd > 500 meters then
39.             continue
40.         end if
41.     end if
42.
43.     // Add to matches if it meets the similarity threshold
44.     if SimScore ≥ θ then
45.         MatchedRides.APPEND({Ride: r, Score: SimScore})
46.     end if
47. end for
48.
49. // Sort and Return Top N Results
50. SORT MatchedRides by Score in DESCENDING order
51. return MatchedRides[1 to N]
```
