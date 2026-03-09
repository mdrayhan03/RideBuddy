/**
 * RideBuddy Map Manager v1.0
 * A robust, centralized handler for OpenStreetMap (Leaflet) operations.
 * Handles persistent map instances, smooth marker movements, and dynamic routing updates.
 */

class MapManager {
    constructor() {
        this.map = null;
        this.markers = {}; // { userId: L.marker }
        this.routingControls = []; // Array of L.Routing.control
        this._lastWaypointCount = 0;
        this._lastStart = null;
        this.mainRoute = null; // Single main route if needed
        this.tileLayer = null;
        this.config = {
            mapHeight: '350px',
            defaultCenter: [23.8103, 90.4125], // Dhaka
            defaultZoom: 14,
            tileUrl: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            routingStyles: {
                main: { color: '#1a73e8', weight: 6, opacity: 0.8 },
                passenger: { color: '#ea4335', weight: 4, opacity: 0.5 }
            }
        };
    }

    /**
     * Initializes the map and enforces a 350px height
     */
    init(elementId, options = {}) {
        const container = document.getElementById(elementId);
        if (container) {
            container.style.height = this.config.mapHeight;
            container.style.borderRadius = '16px';
            container.style.overflow = 'hidden';
            container.style.boxShadow = '0 10px 30px rgba(0,0,0,0.1)';
        }

        if (this.map) this.destroy();

        const center = options.center || this.config.defaultCenter;
        const zoom = options.zoom || this.config.defaultZoom;

        this.map = L.map(elementId, {
            zoomControl: true,
            attributionControl: false,
            ...options
        }).setView(center, zoom);

        this.tileLayer = L.tileLayer(this.config.tileUrl).addTo(this.map);

        return this.map;
    }

    /**
     * Specialized marker update for RideBuddy logic
     * Handles icons for Rider (Vehicle), Owner (Yellow), Host (Green), and Passenger (Blue/Red)
     */
    updateRideMarker(id, lat, lng, options = {}) {
        if (!this.map) return;

        const pos = [lat, lng];
        const markerId = id || `marker_${lat}_${lng}`;

        if (this.markers[markerId]) {
            this.markers[markerId].setLatLng(pos);
            if (options.popup) this.markers[markerId].setPopupContent(options.popup);
            return this.markers[markerId];
        }

        let icon;
        if (options.icon) {
            // Use custom icon from folder (memberyellow.png, membergreen.png, etc.)
            icon = L.icon({
                iconUrl: options.icon,
                iconSize: [32, 32],
                iconAnchor: [16, 32],
                popupAnchor: [0, -32]
            });
        } else if (options.type === 'rider') {
            // Priority Vehicle Marker
            icon = L.icon({
                iconUrl: '/static/assets/media/vehiclemarker.png',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            });
        }

        const marker = L.marker(pos, { icon: icon }).addTo(this.map);
        if (options.popup) marker.bindPopup(options.popup);
        this.markers[markerId] = marker;

        return marker;
    }

    /**
     * Renders all data from the Backend Map Data service
     * @param {Object} data - Processed map data from ride_service.py
     */
    renderRideData(mapData) {
        if (!this.map || !mapData) return;

        // 1. Update/Add Markers
        const currentMarkerIds = new Set();
        if (mapData.markers) {
            mapData.markers.forEach(m => {
                const markerId = m.id || `${m.lat}-${m.lng}`;
                currentMarkerIds.add(markerId);

                this.updateRideMarker(markerId, m.lat, m.lng, {
                    type: m.type,
                    icon: m.icon,
                    popup: m.popup
                });
            });
        }

        // Remove markers that are no longer in mapData
        Object.keys(this.markers).forEach(id => {
            if (!currentMarkerIds.has(id)) {
                this.map.removeLayer(this.markers[id]);
                delete this.markers[id];
            }
        });

        // 2. Handle Routing
        const hasGeometry = mapData.main_route_geometry && mapData.main_route_geometry.points && mapData.main_route_geometry.points.length > 0;

        if (hasGeometry) {
            this.clearRouting();
            this.drawGeometryRoute(mapData.main_route_geometry.points);
        } else {
            // Fallback to LRM if no explicit geometry
            const newWaypoints = mapData.waypoints || [];
            const shouldUpdateRouting = this.routingControls.length === 0 ||
                newWaypoints.length !== this._lastWaypointCount ||
                (newWaypoints.length > 0 &&
                    (newWaypoints[0].lat !== this._lastStart?.lat || newWaypoints[0].lng !== this._lastStart?.lng));

            if (shouldUpdateRouting && newWaypoints.length >= 2) {
                this.clearRouting();
                this.setMainRoute(newWaypoints);
                this._lastWaypointCount = newWaypoints.length;
                this._lastStart = newWaypoints[0];
            }
        }

        this.autoFit();
    }

    /**
     * Draws an exact polyline from a list of points [[lat, lon], ...]
     */
    drawGeometryRoute(points) {
        if (!this.map || !points) return;

        // Convert [lat, lon] to L.latLng if needed, though polyline handles it
        const polyline = L.polyline(points, {
            ...this.config.routingStyles.main,
            interactive: false
        }).addTo(this.map);

        // Treat it as a routing control for consistent clearing
        this.routingControls.push(polyline);
        return polyline;
    }

    clearMarkers() {
        Object.values(this.markers).forEach(m => this.map.removeLayer(m));
        this.markers = {};
    }

    /**
     * Clears specific routing controls or all of them
     */
    clearRouting() {
        this.routingControls.forEach(ctrl => {
            if (ctrl.remove) {
                ctrl.remove(); // Works for both layers and controls in Leaflet 1.0+
            } else if (this.map.removeControl && ctrl instanceof L.Control) {
                this.map.removeControl(ctrl);
            } else {
                this.map.removeLayer(ctrl);
            }
        });
        this.routingControls = [];
    }

    /**
     * Set a single main route (e.g., for a rider's path)
     * @param {Array} waypoints - Array of [lat, lng] or L.latLng
     */
    setMainRoute(waypoints) {
        if (!this.map) return;

        const control = L.Routing.control({
            waypoints: waypoints.map(w => L.latLng(w.lat, w.lng)),
            lineOptions: {
                styles: [this.config.routingStyles.main],
                addWaypoints: false
            },
            createMarker: () => null,
            addWaypoints: false,
            draggableWaypoints: false,
            routeWhileDragging: false,
            show: false
        }).addTo(this.map);

        this.routingControls.push(control);
        return control;
    }

    /**
     * Appends a waypoint to the main route without refreshing map
     * @param {Array|Object} waypoint - [lat, lng] or L.latLng
     */
    addWaypointToMain(waypoint) {
        if (this.routingControls.length === 0) return;
        const control = this.routingControls[0];
        const points = control.getWaypoints().map(wp => wp.latLng).filter(p => p !== null);
        points.push(L.latLng(waypoint));
        control.setWaypoints(points);
    }

    /**
     * Fits map bounds to show all markers and routes
     */
    autoFit() {
        if (!this.map) return;
        const layers = Object.values(this.markers);
        if (layers.length > 0) {
            const group = new L.featureGroup(layers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    /**
     * Destroys the map instance and clears storage
     */
    destroy() {
        if (this.map) {
            this.clearRouting();
            Object.values(this.markers).forEach(m => this.map.removeLayer(m));
            this.markers = {};
            this.map.remove();
            this.map = null;
        }
    }
}

// Global instance for the app to use
window.rideMapManager = new MapManager();
