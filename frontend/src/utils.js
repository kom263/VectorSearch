export const PROPERTY_IMAGES = [
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=600&h=400&fit=crop",
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&h=400&fit=crop",
];

export function getPropertyImage(index) {
    return PROPERTY_IMAGES[index % PROPERTY_IMAGES.length];
}

export function capitalize(str) {
    return str.split(" ").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

export function extractSchoolDistance(nearbyPlaces) {
    if (!nearbyPlaces) return null;
    const school = nearbyPlaces.find(
        (p) => typeof p === "string" && p.toLowerCase().includes("school")
    );
    if (!school) return null;
    const match = school.match(/\((\d+)m\)/);
    if (!match) return null;
    const meters = parseInt(match[1]);
    return meters >= 1000 ? `${(meters / 1000).toFixed(1)}km` : `${meters}m`;
}

export function formatPrice(price) {
    return `₹${Number(price).toLocaleString("en-IN")}`;
}
