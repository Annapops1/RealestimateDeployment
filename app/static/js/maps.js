let map;
let marker;
let autocomplete;

function initMap() {
    const latInput = document.getElementById("latitude");
    const lngInput = document.getElementById("longitude");
    const locationInput = document.getElementById("locationSearch");
    const preferredLocationInput = document.getElementById("preferred_location");
    
    let initialLocation;
    if (latInput.value && lngInput.value) {
        initialLocation = { 
            lat: parseFloat(latInput.value), 
            lng: parseFloat(lngInput.value) 
        };
    } else {
        // Default to India's center
        initialLocation = { lat: 20.5937, lng: 78.9629 };
    }
    
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: latInput.value ? 15 : 5,
        center: initialLocation,
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: [
            {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    });

    // If we have existing coordinates, place a marker
    if (latInput.value && lngInput.value) {
        marker = new google.maps.Marker({
            map,
            position: initialLocation,
            animation: google.maps.Animation.DROP,
            draggable: true
        });
        
        // Update coordinates when marker is dragged
        marker.addListener('dragend', function(e) {
            updateLocation(e.latLng);
        });
    }

    // Initialize the autocomplete with existing value
    autocomplete = new google.maps.places.Autocomplete(locationInput, { 
        componentRestrictions: { country: "in" },
        fields: ["formatted_address", "geometry"]
    });

    // Add marker when location is selected
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry) return;

        updateLocation(place.geometry.location, place.formatted_address);
        map.setCenter(place.geometry.location);
        map.setZoom(15);
    });

    // Allow clicking on map to set location
    map.addListener("click", (e) => {
        updateLocation(e.latLng);
    });
}

function updateLocation(latLng, address = null) {
    if (marker) marker.setMap(null);
    
    marker = new google.maps.Marker({
        position: latLng,
        map: map,
        animation: google.maps.Animation.DROP,
        draggable: true
    });

    marker.addListener('dragend', function(e) {
        updateLocation(e.latLng);
    });

    // Reverse geocode if address not provided
    if (!address) {
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ location: latLng }, (results, status) => {
            if (status === "OK" && results[0]) {
                document.getElementById("locationSearch").value = results[0].formatted_address;
                document.getElementById("preferred_location").value = results[0].formatted_address;
            }
        });
    } else {
        document.getElementById("locationSearch").value = address;
        document.getElementById("preferred_location").value = address;
    }

    document.getElementById("latitude").value = latLng.lat();
    document.getElementById("longitude").value = latLng.lng();
}

// Initialize map when page loads
document.addEventListener("DOMContentLoaded", initMap); 