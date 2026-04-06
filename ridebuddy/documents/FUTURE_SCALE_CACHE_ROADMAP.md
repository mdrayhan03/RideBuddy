# RideBuddy: Future Scaling & Caching Roadmap

As RideBuddy's user base grows, the current architecture will experience higher database loads specifically from users actively polling for ride coordinates and searching for active rides. This document serves as a blueprint for implementing **Redis**, which is the industry standard for solving these scaling bottlenecks.

## 1. What is Redis?
Redis is a highly performant, in-memory data store. While PostgreSQL writes data permanently to the hard drive, Redis stores provisional data in RAM (Random Access Memory). This allows data to be read and written in microseconds, bypassing expensive database disk queries.

## 2. Immediate Upgrades (Caching)

### View Caching: `active_rides_json`
Currently, every time a student requests the dashboard map, Django queries PostgreSQL to filter active rides and calculate distances. 

**Future Solution:** 
Implement Django's `cache` framework with `django-redis`. Cache the `active_rides_json` output for 5 to 10 seconds.
- **Result:** If 50 students wait for a ride in a 10-second window, the database is queried exactly **once**. The other 49 requests are served instantly from the Redis RAM cache.

### Session Caching
Instead of verifying the user's session against PostgreSQL on every single authenticated page load, store Django Sessions inside Redis. This provides a massive, global speedup across the entire platform.

## 3. High-Velocity Location Tracking (Future WebSockets)

Currently, map location syncing relies on clients rapidly "polling" the server via standard HTTP requests with updated coordinates.

**Future Solution:** Implement **Django Channels**.
1. Swap standard HTTP endpoints for bidirectional **WebSockets**.
2. **Redis as a Channel Layer:** Redis acts as the message broker taking rapid GPS coordinate updates from the Rider and instantly broadcasting them to all Students connected to that specific ride.
- **Result:** The GPS map feels completely smooth and "live" (like the Uber app), while removing millions of short HTTP requests from your server load.

## 4. Background Processing (Celery)
Some tasks shouldn't block the user from seeing their next screen.
- E.g., Sending email receipts via SMTP when a Ride concludes.
- E.g., Generating complex analytics.

**Future Solution:** Implement **Celery**, using Redis as the message broker. 
When a ride completes, Django hands the "send email" task to Redis. The user's screen loads instantly, while a background Celery worker quietly pulls the task out of Redis and sends the SMTP email out of sync.

## 5. Docker Implementation Plan
When you are ready to implement this, your architecture is already primed for it. You will only need to update your existing Docker Compose setup:

1. Add to `docker-compose.yml`:

    redis:
      image: redis:7-alpine
      container_name: ridebuddy_redis
      ports:
        - "6379:6379"
      volumes:
        - redis_data:/data
      restart: unless-stopped

2. Add to `requirements.txt`:

    django-redis==5.4.0

3. Add to `settings.py`:

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
