import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
LOCAL_SITE_PACKAGES = PROJECT_ROOT / "venv" / "Lib" / "site-packages"

if LOCAL_SITE_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_SITE_PACKAGES))

from env_loader import load_env_file

load_env_file(PROJECT_ROOT / ".env")

from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
import mediapipe as mp
from ultralytics import YOLO
import time
import winsound
from flask import flash, session
from werkzeug.security import check_password_hash, generate_password_hash

from auth_db import (
    create_live_fall_notification,
    create_user,
    fetch_user_by_email,
    list_notification_feed,
    touch_last_login,
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fall-surveillance-dev-secret")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


yolo = YOLO("Yolov8n.pt")
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

BUZZER_FREQ = 1000
BUZZER_DURATION = 700

video_capture = None
video_frame = None
fall_detected = False
fall_start_time = None
ALERT_DURATION =1
stop_stream_flag = False
buzzer_played=None
active_live_operator = None
last_live_notification_at = None

NAV_ITEMS = [
    {"label": "Home", "endpoint": "home"},
    {"label": "Theory", "endpoint": "theory"},
    {"label": "Detection", "endpoint": "fall_detection"},
    {"label": "Portals", "endpoint": "portals"},
    {"label": "Login", "endpoint": "login"},
]

ROLE_OPTIONS = [
    {"value": "caregiver", "label": "Caregiver"},
    {"value": "detection_operator", "label": "Detection Operator"},
]


def render_page(template_name, **page_context):
    return render_template(
        template_name,
        nav_items=NAV_ITEMS,
        current_user=session.get("user"),
        current_portal_endpoint=portal_endpoint_for_role(session["user"]["role"]) if session.get("user") else None,
        **page_context,
    )


def portal_endpoint_for_role(role):
    if role == "caregiver":
        return "caregiver_portal"
    return "detection_portal"


def require_login():
    user = session.get("user")
    if user:
        return user

    flash("Please log in to access that portal.", "error")
    return None


def require_role(*allowed_roles):
    user = require_login()
    if not user:
        return None

    if user["role"] in allowed_roles:
        return user

    flash("You can access only your assigned portal.", "error")
    return "forbidden"


def detect_fall(frame):
    global fall_detected, fall_start_time
    global buzzer_played, horizontal_frames, fall_detected
    global active_live_operator, last_live_notification_at

    
    

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = yolo(frame, verbose=False)
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            if yolo.names[cls] == "person":
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                person_roi = frame_rgb[y1:y2, x1:x2]
                pose_results = pose.process(person_roi)
                if pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark
                    h, w, _ = person_roi.shape
                    sy = int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h)
                    ay = int(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y * h)
                    body_height = abs(ay - sy)
                    if body_height < h * 0.58:  # lying
                        if fall_start_time is None:
                            fall_start_time = time.time()
                        elapsed = time.time() - fall_start_time
                        if elapsed > ALERT_DURATION:
                            fall_detected = True

                        if not buzzer_played:
                         winsound.Beep(BUZZER_FREQ, BUZZER_DURATION)
                         if active_live_operator:
                             now = time.time()
                             if last_live_notification_at is None or (now - last_live_notification_at) > 15:
                                 try:
                                     create_live_fall_notification(
                                         active_live_operator["id"],
                                         source_label=f"Live stream by {active_live_operator['full_name']}",
                                     )
                                     last_live_notification_at = now
                                 except RuntimeError:
                                     pass
                         buzzer_played = True
                            
                    else:
                        fall_start_time = None
                        fall_detected = False
                        buzzer_played = False
                    color = (0,0,255) if fall_detected else (0,255,0)
                    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 3)
                    label = "FALL DETECTED!" if fall_detected else "Normal"
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    return frame


def generate_frames(video_source):
    global stop_stream_flag
    cap = cv2.VideoCapture(video_source)
    while cap.isOpened() and not stop_stream_flag:
        ret, frame = cap.read()
        if not ret:
            break
        frame = detect_fall(frame)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()


@app.route('/')
def home():
    if session.get("user"):
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))
    return redirect(url_for("login"))

@app.route('/theory')
def theory():
    return render_page(
        'theory.html',
        page_title='System Theory',
        theory_sections=[
            {
                "title": "Introduction",
                "body": (
                    "This system helps monitor elderly individuals with computer vision "
                    "so potential falls can be noticed quickly without wearables."
                ),
            },
            {
                "title": "Problem Statement",
                "body": (
                    "Manual supervision does not scale well, and delayed response after a fall "
                    "can increase medical risk for seniors living independently."
                ),
            },
            {
                "title": "Pipeline",
                "body": (
                    "YOLO detects people in each frame, the posture logic evaluates body orientation "
                    "and height change, and an alert state is raised after sustained fall evidence."
                ),
            },
        ],
        future_items=[
            "Caregiver notifications",
            "Event history and summaries",
            "Cloud evidence storage",
            "Multi-camera expansion",
        ],
    )


@app.route('/portals')
def portals():
    user = require_login()
    if not user:
        return redirect(url_for('login'))

    return redirect(url_for(portal_endpoint_for_role(user["role"])))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("user"):
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            user = fetch_user_by_email(email)
        except RuntimeError as exc:
            flash(str(exc), "error")
            user = None

        if not user or not user["is_active"] or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
        else:
            touch_last_login(user["id"])
            session["user"] = {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
            }
            flash("Login successful.", "success")
            return redirect(url_for(portal_endpoint_for_role(user["role"])))

    return render_page(
        'login.html',
        page_title='Login',
        auth_info={
            "title": "Sign in to continue",
            "subtitle": "Login is now backed by PostgreSQL user records and redirects each role into the correct portal.",
            "roles": ROLE_OPTIONS,
        },
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get("user"):
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone_number = request.form.get('phone_number', '').strip()
        role = request.form.get('role', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([full_name, email, role, password, confirm_password]):
            flash("Please fill in all required fields.", "error")
        elif role not in {item["value"] for item in ROLE_OPTIONS}:
            flash("Please choose a valid role.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            password_hash = generate_password_hash(password)
            try:
                user = create_user(full_name, email, phone_number, role, password_hash)
                if not user:
                    flash("An account with that email already exists.", "error")
                else:
                    flash("Registration successful. Please log in.", "success")
                    return redirect(url_for('login'))
            except RuntimeError as exc:
                flash(str(exc), "error")

    return render_page(
        'register.html',
        page_title='Register',
        auth_info={
            "title": "Create an access profile",
            "subtitle": "Registration writes user accounts into PostgreSQL so login and role-based portal access stay dynamic.",
            "roles": ROLE_OPTIONS,
        },
    )


@app.route('/logout')
def logout():
    global active_live_operator
    session.clear()
    active_live_operator = None
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route('/caregiver_portal')
def caregiver_portal():
    user = require_role("caregiver")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    try:
        notifications = list_notification_feed(user["id"])
    except RuntimeError as exc:
        notifications = []
        flash(str(exc), "error")

    return render_page(
        'caregiver_portal.html',
        page_title='Caregiver Portal',
        caregiver_info={
            "title": "Caregiver response portal",
            "subtitle": "This portal now receives live fall notifications triggered by the logged-in detection operator during monitoring.",
            "stats": [
                {"label": "Alert queue", "value": str(len(notifications))},
                {"label": "Patients", "value": "Dynamic"},
                {"label": "Response flow", "value": "Live-ready"},
            ],
        },
        portal_user=user,
        notifications=notifications,
        caregiver_panels=[
            {
                "title": "Upcoming notification surface",
                "items": [
                    "Fall detected banners",
                    "Priority alert cards",
                    "Escalation to caregiver response",
                ],
            },
            {
                "title": "Patient context area",
                "items": [
                    "Room or patient identifier",
                    "Recent event history",
                    "Emergency contact visibility",
                ],
            },
        ],
    )


@app.route('/detection_portal')
def detection_portal():
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    return render_page(
        'detection_portal.html',
        page_title='Detection Portal',
        detection_info={
            "title": "Detection operations portal",
            "subtitle": "Built for the operator who starts live monitoring, uploads footage, and reviews the active system state.",
            "stats": [
                {"label": "Live mode", "value": "Available"},
                {"label": "Upload mode", "value": "Available"},
                {"label": "Portal UX", "value": "Ready"},
            ],
        },
        portal_user=user,
        detection_actions=[
            {
                "title": "Start live stream",
                "description": "Open the live monitoring experience with the current detection pipeline.",
                "endpoint": "live_stream",
                "cta": "Go Live",
            },
            {
                "title": "Upload a recording",
                "description": "Review a saved clip using the same model pipeline and processing behavior.",
                "endpoint": "upload_video",
                "cta": "Open Upload",
            },
        ],
    )

@app.route('/fall_detection')
def fall_detection():
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    return render_page(
        'fall_detection.html',
        page_title='Detection Hub',
        hub_intro={
            "title": "Choose how you want to monitor",
            "subtitle": (
                "Keep the detection workflow simple now, while leaving room for richer "
                "status, alert, and reporting features later."
            ),
        },
        mode_cards=[
            {
                "title": "Upload video detection",
                "description": "Analyze a saved video file through the same fall detection pipeline.",
                "endpoint": "upload_video",
                "cta": "Open Upload Mode",
                "tag": "Recorded footage",
            },
            {
                "title": "Live stream detection",
                "description": "Start webcam monitoring and inspect live processed frames in real time.",
                "endpoint": "live_stream",
                "cta": "Open Live Mode",
                "tag": "Real-time monitoring",
            },
            {
                "title": "Role-based portal access",
                "description": "Open dedicated UI portals for caregivers, medical staff, and the detection-side operator.",
                "endpoint": "portals",
                "cta": "View Portals",
                "tag": "Workflow design",
            },
        ],
        support_panels=[
            {
                "title": "Dynamic next-step ideas",
                "items": [
                    "Alert history panel",
                    "Recent session summaries",
                    "Caregiver response shortcuts",
                ],
            },
            {
                "title": "Current experience",
                "items": [
                    "Upload flow available",
                    "Webcam stream available",
                    "Detection rendering available",
                ],
            },
        ],
    )

@app.route('/upload_video', methods=['GET', 'POST'])
def upload_video():
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    if request.method == 'POST':
        file = request.files['video']
        if file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            return redirect(url_for('video_detect', filename=file.filename))
    return render_page(
        'upload_video.html',
        page_title='Upload Video',
        upload_info={
            "title": "Upload a clip for detection",
            "subtitle": (
                "The processing behavior stays the same, but the interface now makes the "
                "workflow clearer and easier to extend."
            ),
        },
        upload_tips=[
            "Use a clear view of the person in frame",
            "Supported through the browser file picker",
            "Processed output will open immediately after submit",
        ],
    )

@app.route('/video_detect/<filename>')
def video_detect(filename):
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    global stop_stream_flag
    stop_stream_flag = False
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return Response(generate_frames(video_path), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/live_stream')
def live_stream():
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    return render_page(
        'live_stream.html',
        page_title='Live Stream Monitoring',
        live_info={
            "title": "Live stream monitoring",
            "subtitle": "Watch the processed camera feed and stop the session at any time.",
            "status": [
                {"label": "Camera", "value": "Ready"},
                {"label": "Mode", "value": "Real-time"},
                {"label": "Alert state", "value": "Auto-detect"},
            ],
        },
    )

@app.route('/start_stream')
def start_stream():
    global active_live_operator, last_live_notification_at
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    active_live_operator = user
    last_live_notification_at = None
    global stop_stream_flag
    stop_stream_flag = False
    return Response(generate_frames(0), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_stream')
def stop_stream():
    global active_live_operator
    user = require_role("detection_operator")
    if not user:
        return redirect(url_for('login'))
    if user == "forbidden":
        return redirect(url_for(portal_endpoint_for_role(session["user"]["role"])))

    global stop_stream_flag
    stop_stream_flag = True
    active_live_operator = None
    return redirect(url_for('fall_detection'))

if __name__ == '__main__':
    app.run()
