# app.py
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# File to store courses
COURSES_FILE = "courses.json"

# Allowed status values
ALLOWED_STATUS = ["Not Started", "In Progress", "Completed"]

# Ensure courses.json exists
if not os.path.exists(COURSES_FILE):
    with open(COURSES_FILE, "w") as f:
        json.dump([], f)  # start with empty list

# Helper functions
def read_courses():
    """Read courses from the JSON file."""
    try:
        with open(COURSES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return jsonify({"error": "Failed to read courses file", "details": str(e)}), 500

def write_courses(courses):
    """Write courses list to the JSON file."""
    try:
        with open(COURSES_FILE, "w") as f:
            json.dump(courses, f, indent=4)
    except Exception as e:
        return jsonify({"error": "Failed to write courses file", "details": str(e)}), 500

def get_next_id(courses):
    """Get the next course ID."""
    if courses:
        return max(course["id"] for course in courses) + 1
    else:
        return 1

# ---------------------- ROUTES ----------------------

@app.route("/api/courses", methods=["POST"])
def add_course():
    """Add a new course."""
    data = request.get_json()

    # Validate required fields
    required_fields = ["name", "description", "target_date", "status"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    # Validate status
    if data["status"] not in ALLOWED_STATUS:
        return jsonify({"error": f"Invalid status. Allowed: {ALLOWED_STATUS}"}), 400

    # Validate date format
    try:
        datetime.strptime(data["target_date"], "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "target_date must be in YYYY-MM-DD format"}), 400

    courses = read_courses()
    if isinstance(courses, tuple):  # error reading file
        return courses

    new_course = {
        "id": get_next_id(courses),
        "name": data["name"],
        "description": data["description"],
        "target_date": data["target_date"],
        "status": data["status"],
        "created_at": datetime.now().isoformat()
    }

    courses.append(new_course)
    write_courses(courses)

    return jsonify(new_course), 201

@app.route("/api/courses", methods=["GET"])
def get_courses():
    """Get all courses."""
    courses = read_courses()
    if isinstance(courses, tuple):
        return courses
    return jsonify(courses)

@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    """Get a specific course by ID."""
    courses = read_courses()
    if isinstance(courses, tuple):
        return courses

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course)

@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    """Update a course by ID."""
    data = request.get_json()
    courses = read_courses()
    if isinstance(courses, tuple):
        return courses

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    # Update allowed fields
    if "name" in data:
        course["name"] = data["name"]
    if "description" in data:
        course["description"] = data["description"]
    if "target_date" in data:
        try:
            datetime.strptime(data["target_date"], "%Y-%m-%d")
            course["target_date"] = data["target_date"]
        except ValueError:
            return jsonify({"error": "target_date must be in YYYY-MM-DD format"}), 400
    if "status" in data:
        if data["status"] not in ALLOWED_STATUS:
            return jsonify({"error": f"Invalid status. Allowed: {ALLOWED_STATUS}"}), 400
        course["status"] = data["status"]

    write_courses(courses)
    return jsonify(course)

@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    """Delete a course by ID."""
    courses = read_courses()
    if isinstance(courses, tuple):
        return courses

    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    courses.remove(course)
    write_courses(courses)
    return jsonify({"message": f"Course {course_id} deleted successfully."})

@app.route("/api/courses/stats", methods=["GET"])
def get_course_stats():
    """Return statistics about courses."""
    courses = read_courses()
    if isinstance(courses, tuple):  # error reading file
        return courses

    # Initialize counts
    stats = {
        "total_courses": len(courses),
        "status_counts": {status: 0 for status in ALLOWED_STATUS}
    }

    # Count courses by status
    for course in courses:
        status = course.get("status")
        if status in stats["status_counts"]:
            stats["status_counts"][status] += 1

    return jsonify(stats)

# ---------------------- RUN APP ----------------------

if __name__ == "__main__":
    print("CodeCraftHub API is starting...")
    print(f"Data will be stored in: {os.path.abspath(COURSES_FILE)}")
    print("API will be available at: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)