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
from ultralytics import YOLO
import mediapipe as mp
import time
import winsound

# =========================
# Flask Setup
# =========================
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# =========================
# Models
# =========================
yolo = YOLO("yolov8n.pt")

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)

# =========================
# Alert Settings
# =========================
BUZZER_FREQ = 1000
BUZZER_DURATION = 800
ALERT_DURATION = 2

# =========================
# Global State
# =========================
fall_detected = False
fall_start_time = None
prev_heights = []
buzzer_played = False
stop_stream_flag = False

NAV_ITEMS = [
    {"label": "Home", "endpoint": "home"},
    {"label": "Theory", "endpoint": "theory"},
    {"label": "Detection", "endpoint": "fall_detection"},
    {"label": "Portals", "endpoint": "portals"},
    {"label": "Login", "endpoint": "login"},
]


def render_page(template_name, **page_context):
    return render_template(template_name, nav_items=NAV_ITEMS, **page_context)

# =========================
# FALL DETECTION
# =========================
def detect_fall(frame):
    global fall_detected, fall_start_time, prev_heights, buzzer_played

    results = yolo(frame, verbose=False)

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            if yolo.names[cls] != "person":
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            box_h = y2 - y1
            box_w = x2 - x1

            # Aspect ratio (lying detection)
            is_horizontal = box_w > box_h * 1.2

            # Height drop detection
            prev_heights.append(box_h)
            if len(prev_heights) > 5:
                prev_heights.pop(0)

            height_drop = False
            if len(prev_heights) >= 2:
                drop = (prev_heights[0] - box_h) / prev_heights[0]
                height_drop = drop > 0.35

            # FALL CONFIRMATION
            if is_horizontal and height_drop:
                if fall_start_time is None:
                    fall_start_time = time.time()

                if time.time() - fall_start_time > ALERT_DURATION:
                    fall_detected = True
                    if not buzzer_played:
                        winsound.Beep(BUZZER_FREQ, BUZZER_DURATION)
                        buzzer_played = True
            else:
                fall_start_time = None
                fall_detected = False
                buzzer_played = False

            # Draw
            color = (0, 0, 255) if fall_detected else (0, 255, 0)
            label = "FALL DETECTED!" if fall_detected else "Normal"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    return frame

# =========================
# STREAMING
# =========================
def generate_frames(src):
    global stop_stream_flag
    cap = cv2.VideoCapture(src)

    while cap.isOpened() and not stop_stream_flag:
        ret, frame = cap.read()
        if not ret:
            break

        frame = detect_fall(frame)
        ret, buffer = cv2.imencode('.jpg', frame)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')

    cap.release()

# =========================
# ROUTES
# =========================
@app.route('/')
def home():
    return render_page(
        'home.html',
        page_title='Intelligent Fall Surveillance',
        hero={
            "eyebrow": "AI-powered elderly safety",
            "title": "Monitor falls with a calmer, clearer command center.",
            "subtitle": (
                "A modern interface for live monitoring, recorded video analysis, "
                "and future caregiver workflows."
            ),
            "primary": {"label": "Open Detection Hub", "endpoint": "fall_detection"},
            "secondary": {"label": "View System Theory", "endpoint": "theory"},
            "stats": [
                {"value": "2", "label": "Monitoring modes"},
                {"value": "YOLO", "label": "Person detection"},
                {"value": "Real-time", "label": "Alert pipeline"},
            ],
        },
        feature_cards=[
            {
                "title": "Live camera monitoring",
                "description": "Launch a webcam session and watch fall events appear in the live feed.",
                "badge": "Live",
            },
            {
                "title": "Recorded video review",
                "description": "Upload a stored clip and inspect the processed stream inside the browser.",
                "badge": "Upload",
            },
            {
                "title": "Future-ready dashboard",
                "description": "Structured to later support alert history, caregiver actions, and analytics.",
                "badge": "Scalable",
            },
            {
                "title": "Dual portal access",
                "description": "Separate UI journeys for monitoring staff and the detection-side operator.",
                "badge": "Role-based",
            },
        ],
        overview_panels=[
            {
                "title": "System focus",
                "items": [
                    "Elderly safety monitoring",
                    "Fall event visibility",
                    "Low-friction browser workflow",
                ],
            },
            {
                "title": "Dynamic UI areas",
                "items": [
                    "Session status chips",
                    "Feature cards from route data",
                    "Detection summaries and event panels",
                ],
            },
            {
                "title": "Notification workflow vision",
                "items": [
                    "Caregiver login and register screens",
                    "Medical staff review portal",
                    "Detector-side monitoring portal",
                ],
            },
        ],
    )


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
    return render_page(
        'portals.html',
        page_title='Role Portals',
        portal_intro={
            "title": "Two portals for a safer response loop",
            "subtitle": (
                "One experience is for caregivers or medical personnel who receive alerts, "
                "and the other is for the operator who runs the detection system."
            ),
        },
        portal_cards=[
            {
                "title": "Caregiver / medical portal",
                "description": "Designed for alert visibility, patient overview, response actions, and future notifications.",
                "endpoint": "caregiver_portal",
                "cta": "Open Care Portal",
                "tag": "Alert receiver",
            },
            {
                "title": "Detection operator portal",
                "description": "Designed for monitoring sessions, live streams, video uploads, and future system health controls.",
                "endpoint": "detection_portal",
                "cta": "Open Detection Portal",
                "tag": "Detection owner",
            },
        ],
    )


@app.route('/login')
def login():
    return render_page(
        'login.html',
        page_title='Login',
        auth_mode='login',
        auth_info={
            "title": "Sign in to continue",
            "subtitle": "Choose the right role experience and continue into the appropriate portal.",
            "roles": ["Caregiver", "Medical personnel", "Detection operator"],
        },
    )


@app.route('/register')
def register():
    return render_page(
        'register.html',
        page_title='Register',
        auth_mode='register',
        auth_info={
            "title": "Create an access profile",
            "subtitle": "A polished onboarding screen now exists for future account-based notifications and portal access.",
            "roles": ["Caregiver", "Medical personnel", "Detection operator"],
        },
    )


@app.route('/caregiver_portal')
def caregiver_portal():
    return render_page(
        'caregiver_portal.html',
        page_title='Caregiver Portal',
        caregiver_info={
            "title": "Caregiver and medical response portal",
            "subtitle": "Structured for future fall alerts, patient visibility, and emergency response workflows.",
            "stats": [
                {"label": "Alert queue", "value": "Live-ready"},
                {"label": "Patients", "value": "Dynamic"},
                {"label": "Response flow", "value": "Planned"},
            ],
        },
        caregiver_panels=[
            {
                "title": "Upcoming notification surface",
                "items": [
                    "Fall detected banners",
                    "Priority alert cards",
                    "Escalation to medical personnel",
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
    global stop_stream_flag
    stop_stream_flag = False
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return Response(generate_frames(path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/live_stream')
def live_stream():
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
    global stop_stream_flag
    stop_stream_flag = False
    return Response(generate_frames(0),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_stream')
def stop_stream():
    global stop_stream_flag
    stop_stream_flag = True
    return redirect(url_for('fall_detection'))

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)
