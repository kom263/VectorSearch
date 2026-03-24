#!/bin/bash
# AI Hiring Pipeline — curl examples
# ═══════════════════════════════════════════════════════════════
# Make sure the backend is running: uvicorn app.main:app --reload --port 8000

BASE="http://localhost:8000"

echo "=== 1. List available roles ==="
curl -s "$BASE/api/roles" | python -m json.tool

echo ""
echo "=== 2. Get role config ==="
curl -s "$BASE/api/roles/senior_electromechanical_engineer" | python -m json.tool

echo ""
echo "=== 3. Apply candidate — Strong fit (should ADVANCE) ==="
curl -s -X POST "$BASE/api/candidates/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rajesh Kumar",
    "phone": "+91-9876543210",
    "skills": ["SolidWorks", "PLC Programming", "Circuit Design", "MATLAB", "AutoCAD"],
    "years_experience": 8,
    "location": "Pune",
    "pitch": "I have 8 years of experience designing automated electromechanical systems for manufacturing. I led a team that built PLC-controlled assembly lines using SolidWorks and MATLAB simulations, reducing production downtime by 30%. I am passionate about bridging hardware and software to build smarter machines.",
    "role_id": "senior_electromechanical_engineer"
  }' | python -m json.tool

echo ""
echo "=== 4. Apply candidate — Moderate fit (should HOLD) ==="
curl -s -X POST "$BASE/api/candidates/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Priya Sharma",
    "phone": "+91-9876543211",
    "skills": ["SolidWorks", "CAD", "Python"],
    "years_experience": 5,
    "location": "Bangalore",
    "pitch": "I am a mechanical engineer with SolidWorks expertise and some exposure to control systems. I am eager to transition into electromechanical design and learn PLC programming on the job.",
    "role_id": "senior_electromechanical_engineer"
  }' | python -m json.tool

echo ""
echo "=== 5. Apply candidate — Weak fit (should REJECT) ==="
curl -s -X POST "$BASE/api/candidates/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amit Patel",
    "phone": "+91-9876543212",
    "skills": ["JavaScript", "React", "Node.js"],
    "years_experience": 3,
    "location": "Chennai",
    "pitch": "I am a web developer looking to explore new opportunities. I have built several React applications and I think I could learn engineering quickly.",
    "role_id": "senior_electromechanical_engineer"
  }' | python -m json.tool

echo ""
echo "=== 6. Apply same candidate to a different role ==="
curl -s -X POST "$BASE/api/candidates/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rajesh Kumar",
    "phone": "+91-9876543210",
    "skills": ["Cost Estimation", "BOQ Preparation", "Contract Management", "AutoCAD"],
    "years_experience": 8,
    "location": "Mumbai",
    "pitch": "I have extensive experience in cost estimation and quantity surveying for large infrastructure projects. I have managed BOQ preparation and contract administration for projects exceeding 100 Cr.",
    "role_id": "senior_quantity_surveyor"
  }' | python -m json.tool

echo ""
echo "=== 7. Get candidate status across all roles ==="
curl -s "$BASE/api/candidates/+91-9876543210/status" | python -m json.tool

echo ""
echo "=== 8. Recruiter dashboard — role view ==="
curl -s "$BASE/dashboard/role/senior_electromechanical_engineer" | python -m json.tool

echo ""
echo "=== 9. Recruiter dashboard — candidate history ==="
curl -s "$BASE/dashboard/candidate/+91-9876543210" | python -m json.tool

echo ""
echo "=== 10. Override a bucket (change application_id as needed) ==="
curl -s -X POST "$BASE/dashboard/override" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 2,
    "new_bucket": "advance",
    "reason": "Candidate showed strong potential in phone screen, promoting from Hold to Advance",
    "overridden_by": "Recruiter_Neha"
  }' | python -m json.tool

echo ""
echo "=== 11. Verify override in candidate history ==="
curl -s "$BASE/dashboard/candidate/+91-9876543211" | python -m json.tool

echo ""
echo "=== 12. Try duplicate application (should fail) ==="
curl -s -X POST "$BASE/api/candidates/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rajesh Kumar",
    "phone": "+91-9876543210",
    "skills": ["SolidWorks"],
    "years_experience": 8,
    "location": "Pune",
    "pitch": "Trying to apply again for the same role.",
    "role_id": "senior_electromechanical_engineer"
  }' | python -m json.tool
