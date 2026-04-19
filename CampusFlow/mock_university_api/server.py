"""
Mock University API Server
--------------------------
Simulates a real university's SIS, Finance, and Housing systems.
Run with: uvicorn mock_university_api.server:app --port 8001 --reload

All endpoints require Bearer token auth (any non-empty token is accepted in mock mode).
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from mock_university_api.data import STUDENTS, COURSES, STUDENT_ENROLMENTS, ROOMS, FINANCES

app = FastAPI(
    title="Mock University API",
    description="Simulates UTM's SIS, Finance, and Housing systems for CampusFlow development",
    version="1.0.0",
)

security = HTTPBearer(auto_error=False)


def _auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Accept any Bearer token in mock mode. In production this would validate JWT."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return credentials.credentials


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "system": "Mock University API", "version": "1.0.0"}


# ─── SIS — Students ───────────────────────────────────────────────────────────

@app.get("/api/v2/students/{student_id}")
def get_student(student_id: str, token: str = Depends(_auth)):
    student = STUDENTS.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return student


@app.get("/api/v2/students")
def list_students(
    faculty: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    token: str = Depends(_auth),
):
    students = list(STUDENTS.values())
    if faculty:
        students = [s for s in students if s.get("faculty") == faculty]
    if status:
        students = [s for s in students if s.get("enrolStatus") == status]
    return {"count": len(students), "students": students}


# ─── SIS — Courses ────────────────────────────────────────────────────────────

@app.get("/api/v2/courses")
def list_courses(
    available_only: bool = Query(False),
    faculty: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    token: str = Depends(_auth),
):
    courses = list(COURSES)
    if available_only:
        courses = [c for c in courses if c.get("available_seats", 0) > 0]
    if faculty:
        courses = [c for c in courses if c.get("faculty") == faculty]
    if semester:
        courses = [c for c in courses if c.get("semester") == semester]
    return {"count": len(courses), "courses": courses}


@app.get("/api/v2/courses/{course_code}")
def get_course(course_code: str, token: str = Depends(_auth)):
    for course in COURSES:
        if course["course_code"].upper() == course_code.upper():
            return course
    raise HTTPException(status_code=404, detail=f"Course {course_code} not found")


@app.get("/api/v2/students/{student_id}/courses")
def get_student_courses(student_id: str, token: str = Depends(_auth)):
    if student_id not in STUDENTS:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    enrolled_codes = STUDENT_ENROLMENTS.get(student_id, [])
    enrolled_courses = [c for c in COURSES if c["course_code"] in enrolled_codes]
    return {"student_id": student_id, "count": len(enrolled_courses), "courses": enrolled_courses}


# ─── Finance ──────────────────────────────────────────────────────────────────

@app.get("/api/v2/students/{student_id}/finances")
def get_student_finances(student_id: str, token: str = Depends(_auth)):
    if student_id not in STUDENTS:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    finance = FINANCES.get(student_id)
    if not finance:
        return {
            "outstandingAmount": 0.0,
            "totalFeesSemester": 0.0,
            "paidAmount": 0.0,
            "aidCode": None,
            "aidName": None,
            "aidAmount": 0.0,
            "paymentHistory": [],
            "hasPaymentPlan": False,
        }
    return finance


@app.get("/api/v2/finances/outstanding")
def list_outstanding(
    min_amount: float = Query(0),
    token: str = Depends(_auth),
):
    result = []
    for student_id, finance in FINANCES.items():
        if finance["outstandingAmount"] >= min_amount:
            result.append({
                "student_id": student_id,
                "name": STUDENTS.get(student_id, {}).get("name"),
                "outstandingAmount": finance["outstandingAmount"],
            })
    return {"count": len(result), "students": result}


# ─── Housing ──────────────────────────────────────────────────────────────────

@app.get("/api/v2/rooms")
def list_rooms(
    status: Optional[str] = Query(None, description="available | occupied"),
    gender: Optional[str] = Query(None, description="male | female"),
    room_type: Optional[str] = Query(None, description="single | double"),
    block: Optional[str] = Query(None),
    token: str = Depends(_auth),
):
    rooms = list(ROOMS)
    if status:
        rooms = [r for r in rooms if r.get("status") == status]
    if gender:
        rooms = [r for r in rooms if r.get("gender") == gender]
    if room_type:
        rooms = [r for r in rooms if r.get("type") == room_type]
    if block:
        rooms = [r for r in rooms if block.lower() in r.get("block", "").lower()]
    return {
        "count": len(rooms),
        "rooms": rooms,
        "summary": {
            "total": len(ROOMS),
            "available": sum(1 for r in ROOMS if r["status"] == "available"),
            "occupied": sum(1 for r in ROOMS if r["status"] == "occupied"),
        },
    }


@app.get("/api/v2/rooms/{room_no}")
def get_room(room_no: str, token: str = Depends(_auth)):
    for room in ROOMS:
        if room["roomNo"].upper() == room_no.upper():
            return room
    raise HTTPException(status_code=404, detail=f"Room {room_no} not found")


@app.get("/api/v2/students/{student_id}/room")
def get_student_room(student_id: str, token: str = Depends(_auth)):
    if student_id not in STUDENTS:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    for room in ROOMS:
        if room.get("occupant_id") == student_id:
            return {"student_id": student_id, "room": room}
    return {"student_id": student_id, "room": None, "message": "Student is not assigned to any room"}
