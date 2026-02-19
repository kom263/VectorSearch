"""
Final comprehensive test for the Property Search API.
Tests all assignment requirements end-to-end.
"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label} -- {detail}")


print("=" * 70)
print("  PROPERTY SEARCH API - FINAL VERIFICATION")
print("=" * 70)

# =====================================================================
# 1. HEALTH CHECK
# =====================================================================
print("\n[1] Health Check")
r = requests.get(f"{BASE}/")
h = r.json()
check("Status is healthy", h["status"] == "healthy")
check("32 properties indexed", h["total_properties"] == 32)
check("Index is ready", h["index_ready"] is True)

# =====================================================================
# 2. PROPERTY LISTING
# =====================================================================
print("\n[2] Property Listing")
r = requests.get(f"{BASE}/properties")
props = r.json()
check("Returns 32 properties", len(props) == 32)
check("First property has id", "id" in props[0])
check("First property has nearby_places", "nearby_places" in props[0])
check("nearby_places are structured objects", isinstance(props[0]["nearby_places"][0], dict))

# =====================================================================
# 3. SINGLE PROPERTY
# =====================================================================
print("\n[3] Single Property Lookup")
r = requests.get(f"{BASE}/properties/prop_001")
p = r.json()
check("Returns prop_001", p["id"] == "prop_001")
check("Has title", p["title"] == "3BHK Apartment on Pine Street")

# =====================================================================
# 4. SEARCH - Pine Street + School (Assignment Example)
# =====================================================================
print("\n[4] Search: Pine Street + nearby school (Assignment Example)")
r = requests.post(f"{BASE}/search", json={
    "query": "I recently shifted to Pine Street and am looking for a property, and a nearby school is preferable.",
    "top_k": 5
})
data = r.json()
pq = data["parsed_query"]
check("Extracts location 'pine street'", "pine street" in pq.get("locations", []))
check("Extracts school preference", any("school" in p for p in pq.get("preferences", [])))
check("Returns results", data["total_results"] > 0)

top = data["results"][0]
check("Has property_id", "property_id" in top)
check("Has relevance_score", "relevance_score" in top)
check("Has vector_score", "vector_score" in top)
check("Has explanation", "explanation" in top)
check("Has metadata", "metadata" in top)
check("Has parsed_query in response", "parsed_query" in data)
check("Explanation mentions location", "Location match" in top["explanation"] or "pine street" in top["explanation"].lower())
check("Explanation mentions school with distance", "school" in top["explanation"].lower() and "m)" in top["explanation"])
check("Explanation shows base similarity", "base similarity=" in top["explanation"])

print(f"\n  Top result: {top['title']}")
print(f"  Score: {top['relevance_score']}")
print(f"  Explanation: {top['explanation']}")

# =====================================================================
# 5. SEARCH - Budget + Bedrooms + Amenity
# =====================================================================
print("\n[5] Search: 2 bedroom flat under 40k with parking")
r = requests.post(f"{BASE}/search", json={
    "query": "2 bedroom flat under 40k near the city centre with parking",
    "top_k": 3
})
data = r.json()
pq = data["parsed_query"]
check("Extracts bedrooms=2", pq.get("bedrooms") == 2)
check("Extracts budget_max=40000", pq.get("budget_max") == 40000.0)
check("Extracts amenity parking", "parking" in pq.get("amenities", []))
check("Returns results", data["total_results"] > 0)

# Verify strict filtering
for res in data["results"]:
    price = res["metadata"].get("price", 0)
    beds = res["metadata"].get("bedrooms", 0)
    check(f"  {res['title']}: price {price} <= 40000", price <= 40000)
    check(f"  {res['title']}: bedrooms={beds} == 2", beds == 2)

# =====================================================================
# 6. SEARCH - Cheap studio close to metro
# =====================================================================
print("\n[6] Search: Cheap studio close to metro")
r = requests.post(f"{BASE}/search", json={
    "query": "Cheap studio close to metro",
    "top_k": 3
})
data = r.json()
pq = data["parsed_query"]
check("Extracts bedrooms=1 (studio)", pq.get("bedrooms") == 1)
check("Extracts close to metro preference", any("metro" in p for p in pq.get("preferences", [])))
check("Returns results", data["total_results"] > 0)
print(f"  Top: {data['results'][0]['title']} (Rs.{data['results'][0]['metadata']['price']:,.0f})")

# =====================================================================
# 7. SEARCH - Pet-friendly house with balcony
# =====================================================================
print("\n[7] Search: Pet-friendly house with balcony")
r = requests.post(f"{BASE}/search", json={
    "query": "Pet-friendly house with balcony",
    "top_k": 3
})
data = r.json()
pq = data["parsed_query"]
check("Extracts pet friendly amenity/pref", 
      "pet friendly" in pq.get("amenities", []) or "pet_friendly" in pq.get("amenities", [])
      or any("pet" in p for p in pq.get("preferences", [])))
check("Extracts balcony amenity", "balcony" in pq.get("amenities", []))
check("Returns results", data["total_results"] > 0)
print(f"  Top: {data['results'][0]['title']}")

# =====================================================================
# 8. SEARCH - Near hospitals
# =====================================================================
print("\n[8] Search: Any property near hospitals?")
r = requests.post(f"{BASE}/search", json={
    "query": "Any property near hospitals?",
    "top_k": 3
})
data = r.json()
check("Returns results", data["total_results"] > 0)
print(f"  Top: {data['results'][0]['title']}")

# =====================================================================
# 9. SEARCH - Calm neighbourhood with good schools
# =====================================================================
print("\n[9] Search: Calm neighbourhood with good schools")
r = requests.post(f"{BASE}/search", json={
    "query": "Looking for a calm neighbourhood with good schools",
    "top_k": 3
})
data = r.json()
pq = data["parsed_query"]
check("Extracts calm preference", "calm" in pq.get("preferences", []))
check("Extracts school preference", any("school" in p for p in pq.get("preferences", [])))
check("Returns results", data["total_results"] > 0)
print(f"  Top: {data['results'][0]['title']}")

# =====================================================================
# 10. PURE SEMANTIC (no structured signals)
# =====================================================================
print("\n[10] Search: Pure semantic query (no structured signals)")
r = requests.post(f"{BASE}/search", json={
    "query": "a nice place to live with my family",
    "top_k": 3
})
data = r.json()
check("Returns results even with no structure", data["total_results"] > 0)
print(f"  Top: {data['results'][0]['title']} (score={data['results'][0]['relevance_score']:.4f})")

# =====================================================================
# SUMMARY
# =====================================================================
print("\n" + "=" * 70)
print(f"  RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
print("=" * 70)

if FAIL == 0:
    print("\n  ALL CHECKS PASSED!")
else:
    print(f"\n  {FAIL} CHECK(S) FAILED!")
    sys.exit(1)
