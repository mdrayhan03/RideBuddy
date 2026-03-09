def calculate_fare(booking):
    """
    Calculates the total ride fare based on distance and ride type.
    Formula: TotalCost = B + (D * Cf)
    
    Bangladesh (BD) Context Values (Refined for community sharing):
    Car: 
      B (Base Cost) = 50 BDT (Covers starting overhead/service)
      Cf (Cost per Km) = 35 BDT (Reflects fuel + engine wear)
    Bike:
      B (Base Cost) = 20 BDT
      Cf (Cost per Km) = 15 BDT
    """
    
    # Configuration for Bangladesh (BD) Context (Values for 2025)
    CONFIG = {
        'car_ac': {
            'B': 60.0,  # Base Fare for AC
            'Cf': 45.0  # Cost per km for AC
        },
        'car': {
            'B': 40.0,  # Base Fare for Non-AC
            'Cf': 30.0  # Cost per km for Non-AC
        },
        'bike': {
            'B': 20.0,
            'Cf': 15.0
        }
    }

    # Use 'ac' preference if provided in the booking
    is_ac = False
    if booking.preference and isinstance(booking.preference, dict):
        is_ac = booking.preference.get('ac_available', False) or booking.preference.get('ac', False)
    
    # Construct the lookup key, e.g., 'car_ac' or 'car'
    ride_type = booking.ride_type.lower()
    lookup_key = f"{ride_type}_ac" if (is_ac and ride_type == 'car') else ride_type
    
    # Get parameters, fallback to basic 'car' if anything goes wrong
    params = CONFIG.get(lookup_key, CONFIG['car'])
    
    # Calculate total using booking distance
    distance_km = float(booking.distance or 0.0)
    total_fare = params['B'] + (distance_km * params['Cf'])

    total_fare /= 2
    
    # Round to nearest 5 for cash convenience in BD
    return int(round(total_fare / 5) * 5)