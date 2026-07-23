# Tier 5 — Vision & Perception (Eyes)

> **Goal:** JARVIS can see and understand the world through a camera.
> **Est. time:** 6-8 hours · **Depends on:** Tier 2

## ✅ Checklist
- [ ] `core/vision.py` — Camera access via OpenCV
- [ ] Support USB webcam, Pi Camera, IP camera
- [ ] Face detection (MediaPipe)
- [ ] Face tracking (pupils follow detected face)
- [ ] Object detection (YOLOv8/11)
- [ ] Gesture recognition (MediaPipe hands)
- [ ] Scene understanding via Vision LLM (GPT-4o, Qwen3-VL, Gemini)
- [ ] Text reading in images (OCR via VLM)
- [ ] Configurable resolution, frame rate, camera source
- [ ] On-demand capture vs. continuous monitoring
- [ ] Test: "JARVIS, what do you see?"

---

## 📄 core/vision.py — Camera & Perception

```python
"""
Vision Module — Camera capture, object/face detection, VLM understanding.
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectedFace:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    landmarks: Optional[List[Tuple[int, int]]] = None


@dataclass
class DetectedObject:
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h


class Vision:
    """Computer vision system for JARVIS."""
    
    def __init__(self, settings):
        self.camera_id = settings.get("camera_id", 0)
        self.resolution = settings.get("camera_resolution", (640, 480))
        self.fps = settings.get("camera_fps", 30)
        self.enabled = settings.get("vision_enabled", True)
        
        self._camera = None
        self._frame = None
        self._running = False
        self._face_detector = None
        self._object_detector = None
        self._hands_detector = None
        self._frame_lock = threading.Lock()
        
        if self.enabled:
            self._setup()
    
    def _setup(self):
        """Initialize camera and detectors."""
        try:
            self._camera = cv2.VideoCapture(self.camera_id)
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self._camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Initialize MediaPipe face detector
            import mediapipe as mp
            self._mp_face = mp.solutions.face_detection
            self._face_detector = self._mp_face.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )
            
            # Initialize MediaPipe hands
            self._mp_hands = mp.solutions.hands
            self._hands_detector = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5,
            )
            
            print("👁️ Vision system initialized")
        except Exception as e:
            print(f"⚠️ Vision setup failed: {e}")
            self.enabled = False
    
    def start(self):
        """Start background camera capture."""
        if not self.enabled or self._running:
            return
        
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
    
    def stop(self):
        """Stop camera capture."""
        self._running = False
        if self._camera:
            self._camera.release()
    
    def capture(self) -> Optional[np.ndarray]:
        """Capture a single frame on demand."""
        if self._camera:
            ret, frame = self._camera.read()
            if ret:
                return frame
        return None
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame from continuous capture."""
        with self._frame_lock:
            if self._frame is not None:
                return self._frame.copy()
        return None
    
    def detect_faces(self, frame: np.ndarray = None) -> List[DetectedFace]:
        """Detect faces in a frame."""
        if frame is None:
            frame = self.get_latest_frame()
        if frame is None or self._face_detector is None:
            return []
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_detector.process(rgb)
        
        faces = []
        if results.detections:
            h, w, _ = frame.shape
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                faces.append(DetectedFace(
                    x=int(bbox.xmin * w),
                    y=int(bbox.ymin * h),
                    width=int(bbox.width * w),
                    height=int(bbox.height * h),
                    confidence=detection.score[0],
                ))
        
        return faces
    
    def detect_objects(self, frame: np.ndarray = None) -> List[DetectedObject]:
        """Detect objects using YOLO."""
        if not hasattr(self, '_yolo_model'):
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n.pt")  # Nano model for speed
            except Exception as e:
                print(f"⚠️ YOLO not available: {e}")
                return []
        
        if frame is None:
            frame = self.get_latest_frame()
        if frame is None:
            return []
        
        results = self._yolo_model(frame, verbose=False)[0]
        objects = []
        for box in results.boxes:
            objects.append(DetectedObject(
                label=results.names[int(box.cls[0])],
                confidence=float(box.conf[0]),
                bbox=tuple(int(x) for x in box.xyxy[0].tolist()),
            ))
        
        return objects
    
    def describe_scene(self, frame: np.ndarray = None) -> str:
        """Use Vision LLM to describe what's visible."""
        if frame is None:
            frame = self.get_latest_frame()
        if frame is None:
            return "I can't see anything — camera not available."
        
        # Save frame to temp file for the VLM
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            cv2.imwrite(f.name, frame)
            image_path = f.name
        
        try:
            # Use the brain's VLM provider
            from core.brain import Brain
            brain = Brain()  # Uses vision_provider config
            description = brain.describe_image(image_path)
            return description
        finally:
            Path(image_path).unlink(missing_ok=True)
    
    def read_text(self, frame: np.ndarray = None) -> str:
        """Read text visible in frame using VLM."""
        return self.describe_scene(frame)  # VLM handles OCR naturally
    
    def find_face_position(self) -> Optional[Tuple[int, int]]:
        """Find the center of the nearest face (for eye tracking)."""
        faces = self.detect_faces()
        if not faces:
            return None
        face = faces[0]  # Nearest face
        return (face.x + face.width // 2, face.y + face.height // 2)
    
    def _capture_loop(self):
        """Continuous capture loop (background thread)."""
        while self._running and self._camera:
            ret, frame = self._camera.read()
            if ret:
                with self._frame_lock:
                    self._frame = frame
            time.sleep(1.0 / self.fps)
```

## 🔧 Settings Keys

```yaml
vision:
  enabled: true
  camera_id: 0                    # 0=USB, or IP camera URL
  camera_resolution: [640, 480]
  camera_fps: 30
  enable_face_detection: true
  enable_object_detection: false  # YOLO is heavy
  enable_gesture_recognition: false
  face_tracking: true             # Eyes follow detected face
  capture_mode: on_demand         # on_demand or continuous
```

## 🔗 Next Agent

When complete → move to `.agent/tier6-integration.agent.md`
