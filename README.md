# Elderly Human Fall Detection Using Video Monitoring

## Overview

The Elderly Human Fall Detection System is an AI-powered safety monitoring application designed to detect human falls in real time using video surveillance and deep learning techniques. The system helps monitor elderly individuals and supports caregivers by providing timely fall detection during emergency situations.

This project uses Computer Vision, YOLOv8, Flask, and OpenCV to analyze video streams and identify fall events efficiently.

---

## Features

- Real-time human fall detection
- Video upload monitoring
- Live video stream monitoring
- Caregiver monitoring portal
- User authentication system
- AI-powered human detection using YOLOv8
- Emergency monitoring support
- User-friendly web interface

---

## Technologies Used

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask

### AI & Computer Vision
- OpenCV
- YOLOv8
- Deep Learning

### Database
- SQLite

---

## Project Modules

### 1. Authentication System
- User Registration
- User Login
- Secure access management

### 2. Fall Detection Portal
- Detects falls from uploaded videos
- Processes video frames using AI models

### 3. Live Stream Monitoring
- Real-time camera monitoring
- Continuous fall detection

### 4. Caregiver Portal
- Allows caregivers to monitor elderly safety
- Displays monitoring information

### 5. Theory Module
- Provides project explanation and working flow

---

## Folder Structure

```text
human_fall_detection/
│
├── templates/
│   ├── caregiver_portal.html
│   ├── detection_portal.html
│   ├── fall_detection.html
│   ├── home.html
│   ├── live_stream.html
│   ├── login.html
│   ├── portals.html
│   ├── register.html
│   ├── theory.html
│   └── upload_video.html
│
├── static/
│
├── auth_db.py
├── env_loader.py
├── final1.py
├── newapp.py
├── schema.sql
├── requirements.txt
├── README.md
└── PROJECT_FLOW_AND_RUN_GUIDE.md
```

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/PadmalathaKasireddy/elderly-fall-detection-system.git
```

### Navigate to Project Folder

```bash
cd elderly-fall-detection-system
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

---

## Running the Project

Run the Flask application:

```bash
python newapp.py
```

After running the server, open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## Working Process

1. User logs into the system
2. User uploads video or starts live monitoring
3. Frames are processed using OpenCV
4. YOLOv8 detects human posture and fall conditions
5. System identifies possible falls
6. Monitoring information is displayed to caregivers

---

## Applications

- Elderly healthcare monitoring
- Smart home safety systems
- Hospital patient monitoring
- Assisted living environments
- Real-time surveillance systems

---

## Future Enhancements

- SMS alert system
- Mobile application integration
- Cloud deployment
- Real-time emergency notifications
- IoT device integration
- AI-based health analytics

---

## Screenshots
<img width="1600" height="741" alt="image" src="https://github.com/user-attachments/assets/48d5fb2a-071b-4aa6-b3bd-548326ff4e2e" />

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/afee8291-6e40-441a-85cc-6830be587f2e" />

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/ed9b728d-b000-47d5-b220-9e84b1df3ff4" />

<img width="1600" height="735" alt="image" src="https://github.com/user-attachments/assets/e4b4a4a9-10fc-4e0a-af8d-41c1b88a1dbd" />

<img width="1600" height="727" alt="image" src="https://github.com/user-attachments/assets/bc5f97f7-0183-4dc4-8477-cf2799bec23e" />

<img width="1600" height="736" alt="image" src="https://github.com/user-attachments/assets/ab3936e2-44ac-4102-87c1-c18a95f5776a" />



---

## Advantages

- Improves elderly safety
- Supports continuous monitoring
- Reduces emergency response time
- Provides automated fall detection
- User-friendly interface
