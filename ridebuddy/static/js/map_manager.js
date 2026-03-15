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
        this._lastWaypointsHash = null;
        this.mainRoute = null; // Single main route if needed
        this.tileLayer = null;
        this.config = {
            mapHeight: '350px',
            defaultCenter: [23.8103, 90.4125], // Dhaka
            defaultZoom: 14,
            tileUrl: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            routingStyles: {
                main: { color: '#202124', weight: 8, opacity: 0.9 },
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
        const tileUrl = options.tileUrl || this.config.tileUrl;

        this.map = L.map(elementId, {
            zoomControl: true,
            attributionControl: false,
            ...options
        }).setView(center, zoom);

        this.tileLayer = L.tileLayer(tileUrl).addTo(this.map);

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

        let icon = null;
        const isRider = options.type === 'rider' || (options.icon && options.icon.includes('vehiclemarker'));

        if (isRider) {
            icon = L.icon({
                iconUrl: options.icon || '/static/assets/media/vehiclemarker.png',
                iconSize: [28, 28],
                iconAnchor: [14, 14],
                popupAnchor: [0, -14]
            });
        } else if (options.icon) {
            icon = L.icon({
                iconUrl: options.icon,
                iconSize: [28, 28],
                iconAnchor: [14, 14],
                popupAnchor: [0, -14]
            });
        } else if (options.small) {
            // Minimalist dot marker for cleaner maps
            icon = L.divIcon({
                className: 'custom-div-dot',
                html: `<div style="background-color: ${options.color || '#3b82f6'}; width: 12px; height: 12px; border: 2px solid white; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"></div>`,
                iconSize: [12, 12],
                iconAnchor: [6, 6],
                popupAnchor: [0, -6]
            });
        }

        if (this.markers[markerId]) {
            const m = this.markers[markerId];
            m.setLatLng(pos);
            if (icon) m.setIcon(icon);
            if (options.popup) {
                if (m.getPopup()) {
                    m.setPopupContent(options.popup);
                } else {
                    m.bindPopup(options.popup);
                }
            }
            return m;
        }

        // Only define icon if it's not null to allow the default Leaflet pin.
        const markerOptions = {
            zIndexOffset: options.zIndexOffset || 0
        };
        if (icon) markerOptions.icon = icon;

        const marker = L.marker(pos, markerOptions).addTo(this.map);
        if (options.popup) marker.bindPopup(options.popup);
        this.markers[markerId] = marker;

        return marker;
    }

    /**
     * Efficiently updates the coordinates of existing markers.
     * Use this for smooth live tracking without triggering full redraws or icon logic.
     * @param {Array|Object} data - List of {id, lat, lng} or individual object.
     */
    updatePositions(data) {
        if (!this.map || !data) return;
        const list = Array.isArray(data) ? data : [data];

        list.forEach(item => {
            const marker = this.markers[item.id];
            if (marker && item.lat != null && item.lng != null) {
                marker.setLatLng([item.lat, item.lng]);
                if (item.zIndexOffset) {
                    marker.setZIndexOffset(item.zIndexOffset);
                }
            }
        });
    }

    /**
     * Renders all data from the Backend Map Data service
     * @param {Object} data - Processed map data from ride_service.py
     * @param {Object} mainStyle - Optional style override for the main route
     */
    renderRideData(mapData, mainStyle = null) {
        if (!this.map || !mapData) return;

        // 1. Handle Routing (Road Path)
        // We only redraw the routing line if the PICKUP/DROP waypoints have changed.
        const waypoints = mapData.waypoints || [];
        const wpHash = JSON.stringify(waypoints);

        if (this._lastWaypointsHash !== wpHash) {
            this.clearRouting();
            const activeStyle = mainStyle || this.config.routingStyles.main;

            if (waypoints.length >= 2) {
                this.setMainRoute(waypoints, activeStyle);
            } else if (mapData.main_route_geometry && mapData.main_route_geometry.points) {
                this.drawGeometryRoute(mapData.main_route_geometry.points, activeStyle);
            }
            this._lastWaypointsHash = wpHash;

            // Auto-fit only when the route changes to avoid disruptive zooming during live movement
            this.autoFit();
        }

        // 2. Handle Markers (Live Tracking)
        const currentMarkerIds = new Set();
        if (mapData.markers) {
            mapData.markers.forEach(m => {
                const markerId = m.id || `${m.lat}-${m.lng}`;
                currentMarkerIds.add(markerId);

                const isUserMarker = m.is_user || markerId === 'rider_user' || markerId.includes('live_user_');
                const zIndex = isUserMarker ? 1000 : 0;

                if (this.markers[markerId]) {
                    // Optimized: Only move the marker without touching routing or icons
                    this.updatePositions({
                        id: markerId,
                        lat: m.lat,
                        lng: m.lng,
                        zIndexOffset: zIndex
                    });
                } else {
                    // Create marker if it doesn't exist yet
                    this.updateRideMarker(markerId, m.lat, m.lng, {
                        type: m.type,
                        icon: m.icon,
                        popup: m.popup,
                        zIndexOffset: zIndex
                    });
                }
            });
        }

        // Remove markers that are no longer in mapData
        Object.keys(this.markers).forEach(id => {
            if (!currentMarkerIds.has(id) && !id.startsWith('user_')) {
                this.map.removeLayer(this.markers[id]);
                delete this.markers[id];
            }
        });
    }

    _compareWaypoints(wp1, wp2) {
        if (wp1.length !== wp2.length) return false;
        return wp1.every((p, i) => p[0] === wp2[i][0] && p[1] === wp2[i][1]);
    }

    /**
     * Draws an exact polyline from a list of points. 
     * Corrects OSRM/GeoJSON [lng, lat] format to Leaflet [lat, lng]
     */
    drawGeometryRoute(points, style = null) {
        if (!this.map || !points || points.length === 0) return;

        // Auto-fix: GeoJSON (OSRM) provides [lng, lat]. Leaflet expects [lat, lng].
        // Dhaka is ~23N, 90E. If the first coordinate is > 60, it's definitely Longitude.
        const processedPoints = points.map(p => {
            if (Array.isArray(p) && p.length >= 2) {
                if (p[0] > 60) return [p[1], p[0]]; // Flip [lng, lat] -> [lat, lng]
                return p;
            }
            return p;
        });

        const polyline = L.polyline(processedPoints, {
            ...(style || this.config.routingStyles.main),
            interactive: false
        }).addTo(this.map);

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
        if (!this.map) {
            this.routingControls = [];
            return;
        }

        this.routingControls.forEach(ctrl => {
            try {
                if (!ctrl) return;

                // Leaflet Routing Machine Controls are specialized
                if (ctrl instanceof L.Control || (ctrl.getPlan && ctrl.onRemove)) {
                    this.map.removeControl(ctrl);
                } else if (ctrl.remove) {
                    ctrl.remove();
                } else {
                    this.map.removeLayer(ctrl);
                }
            } catch (e) {
                console.warn("Map: Routing cleanup suppressed:", e);
            }
        });

        this.routingControls = [];
        this._lastWaypoints = null;
    }

    /**
     * Set a single main route (e.g., for a rider's path)
     * @param {Array} waypoints - Array of [lat, lng] or L.latLng
     * @param {Object} style - Optional style override
     */
    setMainRoute(waypoints, style = null) {
        if (!this.map) return;

        const control = L.Routing.control({
            waypoints: waypoints.map(w => L.latLng(w.lat, w.lng)),
            lineOptions: {
                styles: [style || this.config.routingStyles.main],
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

        const featureGroup = new L.FeatureGroup();

        // Add markers
        Object.values(this.markers).forEach(m => featureGroup.addLayer(m));

        // Add polyline routes
        this.routingControls.forEach(ctrl => {
            if (ctrl instanceof L.Polyline) {
                featureGroup.addLayer(ctrl);
            } else if (ctrl._line) {
                // LRM control has a _line property which is the polyline
                featureGroup.addLayer(ctrl._line);
            }
        });

        if (featureGroup.getLayers().length > 0) {
            this.map.fitBounds(featureGroup.getBounds().pad(0.1));
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
