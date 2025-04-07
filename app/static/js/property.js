function deleteProperty(propertyId) {
    if (confirm('Are you sure you want to delete this property?')) {
        window.location.href = `/property/delete/${propertyId}`;
    }
} 