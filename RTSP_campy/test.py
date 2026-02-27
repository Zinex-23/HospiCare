import os
import time
import json
import ast
import threading
import urllib.request
import urllib.error
import urllib.parse

# Reduce Qt/OpenCV runtime warnings and stabilize RTSP decode.
os.environ["QT_QPA_PLATFORM"] = "xcb"
if os.path.isdir("/usr/share/fonts/truetype/dejavu"):
    os.environ["QT_QPA_FONTDIR"] = "/usr/share/fonts/truetype/dejavu"
# Suppress noisy FFmpeg decoder logs printed by OpenCV backend.
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "8"  # fatal only
os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    (
        "rtsp_transport;tcp|rtsp_flags;prefer_tcp|fflags;discardcorrupt|"
        "flags;low_delay|reorder_queue_size;0|max_delay;500000|stimeout;5000000"
    ),
)

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as exc:
    raise SystemExit(
        "Chua cai ultralytics. Hay chay: pip install ultralytics"
    ) from exc

try:
    import paho.mqtt.client as mqtt
except ImportError as exc:
    raise SystemExit(
        "Chua cai paho-mqtt. Hay chay: pip install paho-mqtt"
    ) from exc

RTSP_URL = "rtsp://117.2.120.27:44445/art_tango_camera_111"  # doi sang webcam bang "0" neu can
MODEL_PATH = "yolo11n.pt"
CONF_THRES = 0.35
PERSON_CLASS_ID = 0  # COCO: person
WINDOW_NAME = "YOLO Person Overlay"
DISPLAY_SCALE = 0.7  # 1.0 = goc, <1 thu nho cua so hien thi
ROI_DRAW_COLOR = (54, 67, 244)  # BGR ~ #F44336
ROI_FILL_ALPHA = 0.18
ROI_POINT_RADIUS = 4
TB_HOST = "http://localhost:8080"
TB_ACCESS_TOKEN = "123123"
TB_ATTRIBUTE_KEY = "frame_base64"
FRAME_ENCODING = "hex"  # "hex" theo yeu cau; co the doi sang "base64" neu can.
TB_PUSH_EVERY_SEC = 1.0
ROI_POINTS_KEY = "roi_points"
ROI_CONFIG_KEY = "statistic_config"
DETECT_WITHOUT_ROI = False
VERBOSE_LOGS = False
TB_MQTT_PORT = 1883
TB_MQTT_KEEPALIVE = 60
TB_MQTT_REQ_ID = 1
TB_MQTT_RESYNC_SEC = 2.0
TB_HTTP_FALLBACK_SYNC_SEC = 1.0
READ_FAIL_RECONNECT_THRESHOLD = 6
CAPTURE_OPEN_RETRY = 3
CAPTURE_OPEN_RETRY_WAIT_SEC = 0.5
REOPEN_DELAY_SEC = 0.4

source = 0 if str(RTSP_URL).strip() == "0" else RTSP_URL

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Khong tim thay model: {MODEL_PATH}")

model = YOLO(MODEL_PATH)


def open_video_capture(src):
    last_err = None
    for _ in range(CAPTURE_OPEN_RETRY):
        cap_obj = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        if cap_obj.isOpened():
            try:
                cap_obj.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            return cap_obj
        last_err = "Khong mo duoc nguon video."
        cap_obj.release()
        time.sleep(CAPTURE_OPEN_RETRY_WAIT_SEC)
    raise RuntimeError(f"{last_err} Kiem tra RTSP URL/webcam/mang.")


cap = open_video_capture(source)


def encode_frame_payload(frame, encoding="hex"):
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        raise RuntimeError("Khong ma hoa duoc frame JPG.")
    if encoding == "hex":
        return buf.tobytes().hex()
    if encoding == "base64":
        import base64

        return base64.b64encode(buf.tobytes()).decode("ascii")
    raise ValueError(f"Encoding khong ho tro: {encoding}")


def send_frame_attribute_to_thingsboard(frame):
    payload_value = encode_frame_payload(frame, FRAME_ENCODING)
    payload = json.dumps({TB_ATTRIBUTE_KEY: payload_value}).encode("utf-8")
    url = f"{TB_HOST.rstrip('/')}/api/v1/{TB_ACCESS_TOKEN}/attributes"

    req = urllib.request.Request(
        url=url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        status = resp.getcode()
        if status < 200 or status >= 300:
            raise RuntimeError(f"ThingsBoard tra ve status khong hop le: {status}")
    if VERBOSE_LOGS:
        print(f"Da gui frame len ThingsBoard ({TB_ATTRIBUTE_KEY}, encoding={FRAME_ENCODING}).")


def _load_json_value(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            # ThingsBoard UI often stores JSON-like strings with single quotes.
            try:
                return ast.literal_eval(v)
            except (ValueError, SyntaxError):
                return v
    return v


def _extract_points_from_any(v):
    v = _load_json_value(v)
    if v is None:
        return None

    if isinstance(v, list):
        # statistic_config.points tablet: flat pixel list [x1,y1,x2,y2,...]
        if v and all(isinstance(n, (int, float)) for n in v):
            if len(v) >= 6 and len(v) % 2 == 0:
                points = []
                for i in range(0, len(v), 2):
                    points.append((float(v[i]), float(v[i + 1])))
                return points if len(points) >= 3 else None

        # statistic_config.points history: [[...flat], [...flat], ...], lay ban cuoi hop le
        if v and isinstance(v[0], list):
            for cand in reversed(v):
                if not isinstance(cand, list):
                    continue
                if not all(isinstance(n, (int, float)) for n in cand):
                    continue
                if len(cand) >= 6 and len(cand) % 2 == 0:
                    points = []
                    for i in range(0, len(cand), 2):
                        points.append((float(cand[i]), float(cand[i + 1])))
                    if len(points) >= 3:
                        return points

        points = []
        for item in v:
            if isinstance(item, dict):
                x = item.get("x")
                y = item.get("y")
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                x, y = item[0], item[1]
            else:
                continue
            if x is None or y is None:
                continue
            points.append((float(x), float(y)))
        return points if len(points) >= 3 else None

    if isinstance(v, dict):
        direct_keys = [
            ROI_POINTS_KEY,
            "roi",
            "roi_polygon",
            "polygon",
            "points",
            "area_points",
        ]
        for key in direct_keys:
            if key in v:
                points = _extract_points_from_any(v.get(key))
                if points:
                    return points

        for key in ("zones", "areas"):
            zones = v.get(key)
            if isinstance(zones, list):
                for zone in zones:
                    points = _extract_points_from_any(zone)
                    if points:
                        return points
    return None


def parse_roi_from_tb_payload(payload_obj):
    def _deep_scan(node):
        node = _load_json_value(node)

        if isinstance(node, dict):
            if ROI_CONFIG_KEY in node:
                return _extract_points_from_any(node.get(ROI_CONFIG_KEY)), True
            if ROI_POINTS_KEY in node:
                return _extract_points_from_any(node.get(ROI_POINTS_KEY)), True

            kv_key = node.get("key")
            if kv_key == ROI_CONFIG_KEY:
                return _extract_points_from_any(node.get("value")), True
            if kv_key == ROI_POINTS_KEY:
                return _extract_points_from_any(node.get("value")), True

            for _, child in node.items():
                points, has_key = _deep_scan(child)
                if has_key:
                    return points, True
            return None, False

        if isinstance(node, list):
            for item in reversed(node):
                points, has_key = _deep_scan(item)
                if has_key:
                    return points, True
            return None, False

        return None, False

    return _deep_scan(payload_obj)


def fetch_initial_roi_once():
    params = urllib.parse.urlencode({"sharedKeys": ROI_CONFIG_KEY})
    url = f"{TB_HOST.rstrip('/')}/api/v1/{TB_ACCESS_TOKEN}/attributes?{params}"
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        raw = resp.read()
    data = json.loads(raw.decode("utf-8") or "{}")
    points, has_roi_key = parse_roi_from_tb_payload(data)
    if has_roi_key:
        return points
    return None


def roi_http_fallback_worker(stop_event):
    last_signature = None
    while not stop_event.is_set():
        try:
            pts = fetch_initial_roi_once()
            sig = None
            if pts:
                sig = tuple((float(x), float(y)) for x, y in pts)
            if sig != last_signature:
                on_roi_update(pts)
                last_signature = sig
        except Exception:
            pass
        stop_event.wait(TB_HTTP_FALLBACK_SYNC_SEC)


def extract_mqtt_host(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname:
        return parsed.hostname
    return "localhost"


class TbRoiSubscriber:
    def __init__(self, on_roi_update):
        self.on_roi_update = on_roi_update
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except Exception:
            self.client = mqtt.Client()
        self.client.username_pw_set(TB_ACCESS_TOKEN)
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.connected = False
        self.req_id = TB_MQTT_REQ_ID
        self.req_lock = threading.Lock()

    def request_latest_roi(self):
        with self.req_lock:
            self.req_id += 1
            req_id = self.req_id
        req_payload = json.dumps(
            {
                "sharedKeys": ROI_CONFIG_KEY,
                "clientKeys": "",
            }
        )
        self.client.publish(
            f"v1/devices/me/attributes/request/{req_id}",
            req_payload,
            qos=1,
            retain=False,
        )

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        rc = int(reason_code) if reason_code is not None else -1
        self.connected = (rc == 0)
        if not self.connected:
            print(f"MQTT connect that bai, rc={rc}")
            return

        client.subscribe("v1/devices/me/attributes", qos=1)
        client.subscribe("v1/devices/me/attributes/response/+", qos=1)
        self.request_latest_roi()
        print("MQTT da ket noi, dang lang nghe ROI realtime...")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        rc = int(reason_code) if reason_code is not None else 0
        self.connected = False
        if rc != 0:
            print(f"MQTT mat ket noi, rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        points, has_roi_key = parse_roi_from_tb_payload(payload)
        if has_roi_key:
            self.on_roi_update(points)
            return

        # Neu message khong chua ROI truc tiep, request full shared attrs de dong bo.
        if msg.topic == "v1/devices/me/attributes":
            self.request_latest_roi()

    def start(self):
        host = extract_mqtt_host(TB_HOST)
        self.client.connect_async(host, TB_MQTT_PORT, TB_MQTT_KEEPALIVE)
        self.client.loop_start()

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass


def normalize_roi_points(points, frame_w, frame_h):
    if not points or len(points) < 3:
        return None

    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)
    normalized = []

    for x, y in points:
        if max_x <= 1.0 and max_y <= 1.0:
            px = int(round(x * frame_w))
            py = int(round(y * frame_h))
        else:
            px = int(round(x))
            py = int(round(y))
        px = min(max(px, 0), frame_w - 1)
        py = min(max(py, 0), frame_h - 1)
        normalized.append((px, py))

    if len(normalized) < 3:
        return None
    return np.array(normalized, dtype=np.int32)


def build_roi_mask(frame_shape, roi_poly):
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    if roi_poly is not None:
        cv2.fillPoly(mask, [roi_poly], 255)
    return mask


prev_time = time.time()
last_tb_push = 0.0
last_mqtt_resync = 0.0
roi_poly = None
roi_mask = None
roi_ready = False
roi_status = "init"
roi_signature = None
roi_state_lock = threading.Lock()
roi_points_state = None
roi_version = 0
roi_force_reset = False
last_applied_roi_version = -1
consecutive_read_failures = 0


def on_roi_update(points):
    global roi_points_state, roi_version, roi_status, roi_signature, roi_force_reset

    new_signature = None
    if points:
        new_signature = tuple((float(x), float(y)) for x, y in points)

    with roi_state_lock:
        roi_points_state = points
        roi_version += 1
        if points:
            new_status = f"ready:{len(points)}"
        else:
            new_status = "missing"
        changed = (new_status != roi_status) or (new_signature != roi_signature)
        roi_status = new_status
        roi_signature = new_signature
        if changed:
            roi_force_reset = True

    if changed or VERBOSE_LOGS:
        if points:
            print(f"Da cap nhat ROI realtime: {len(points)} diem")
        else:
            print("ROI da bi xoa/khong ton tai tren ThingsBoard.")


subscriber = TbRoiSubscriber(on_roi_update)
subscriber.start()
fallback_stop_event = threading.Event()
fallback_thread = threading.Thread(
    target=roi_http_fallback_worker, args=(fallback_stop_event,), daemon=True
)
fallback_thread.start()
try:
    initial_points = fetch_initial_roi_once()
    if initial_points:
        on_roi_update(initial_points)
        print(f"Khoi tao ROI tu attribute hien tai: {len(initial_points)} diem")
except (urllib.error.URLError, RuntimeError, ValueError, json.JSONDecodeError):
    pass

try:
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            consecutive_read_failures += 1
            if consecutive_read_failures >= READ_FAIL_RECONNECT_THRESHOLD:
                print("Stream loi lien tiep, dang reconnect RTSP...")
                try:
                    cap.release()
                except Exception:
                    pass
                time.sleep(REOPEN_DELAY_SEC)
                try:
                    cap = open_video_capture(source)
                    consecutive_read_failures = 0
                    print("Reconnect RTSP thanh cong.")
                except RuntimeError as exc:
                    print(f"Reconnect that bai: {exc}")
                    time.sleep(1.0)
            else:
                time.sleep(0.03)
            continue
        consecutive_read_failures = 0

        now = time.time()
        if now - last_tb_push >= TB_PUSH_EVERY_SEC:
            try:
                send_frame_attribute_to_thingsboard(frame)
                last_tb_push = now
            except (urllib.error.URLError, RuntimeError, ValueError) as exc:
                print(f"Khong gui duoc frame len ThingsBoard: {exc}")

        if subscriber.connected and (now - last_mqtt_resync >= TB_MQTT_RESYNC_SEC):
            subscriber.request_latest_roi()
            last_mqtt_resync = now

        with roi_state_lock:
            points_snapshot = roi_points_state
            version_snapshot = roi_version
            force_reset_snapshot = roi_force_reset
            if roi_force_reset:
                roi_force_reset = False

        if force_reset_snapshot:
            # Hard reset ROI cache so new points are applied immediately.
            roi_poly = None
            roi_mask = None
            roi_ready = False
            last_applied_roi_version = -1

        if version_snapshot != last_applied_roi_version:
            if points_snapshot:
                h, w = frame.shape[:2]
                roi_poly = normalize_roi_points(points_snapshot, w, h)
                roi_mask = build_roi_mask(frame.shape, roi_poly) if roi_poly is not None else None
                roi_ready = roi_poly is not None
                if not roi_ready:
                    print("ROI khong hop le, tam dung detect.")
            else:
                roi_ready = False
                roi_poly = None
                roi_mask = None
            last_applied_roi_version = version_snapshot

        infer_frame = frame
        if roi_ready and roi_mask is not None:
            infer_frame = cv2.bitwise_and(frame, frame, mask=roi_mask)
        elif not DETECT_WITHOUT_ROI:
            infer_frame = None

        overlay = frame.copy()
        if roi_poly is not None:
            # Draw ROI in same style as ThingsBoard widget: fill + outline + points.
            roi_layer = overlay.copy()
            cv2.fillPoly(roi_layer, [roi_poly], ROI_DRAW_COLOR)
            cv2.addWeighted(roi_layer, ROI_FILL_ALPHA, overlay, 1.0 - ROI_FILL_ALPHA, 0, overlay)
            cv2.polylines(overlay, [roi_poly], True, ROI_DRAW_COLOR, 2, cv2.LINE_AA)
            for px, py in roi_poly:
                cv2.circle(
                    overlay,
                    (int(px), int(py)),
                    ROI_POINT_RADIUS,
                    ROI_DRAW_COLOR,
                    -1,
                    cv2.LINE_AA,
                )

        if infer_frame is None:
            cv2.putText(
                overlay,
                "Waiting ROI from ThingsBoard...",
                (12, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 180, 255),
                2,
                cv2.LINE_AA,
            )
            result_boxes = []
        else:
            result = model.predict(
                source=infer_frame,
                conf=CONF_THRES,
                classes=[PERSON_CLASS_ID],
                verbose=False,
            )[0]
            result_boxes = result.boxes

        for box in result_boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])

            if roi_poly is not None:
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                if cv2.pointPolygonTest(roi_poly, (float(cx), float(cy)), False) < 0:
                    continue

            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 220, 0), 2)
            cv2.putText(
                overlay,
                f"person {conf:.2f}",
                (x1, max(y1 - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 220, 0),
                2,
                cv2.LINE_AA,
            )

        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now
        cv2.putText(
            overlay,
            f"FPS: {fps:.1f}",
            (12, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        if DISPLAY_SCALE != 1.0:
            show_frame = cv2.resize(
                overlay,
                None,
                fx=DISPLAY_SCALE,
                fy=DISPLAY_SCALE,
                interpolation=cv2.INTER_AREA,
            )
        else:
            show_frame = overlay

        cv2.imshow(WINDOW_NAME, show_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    fallback_stop_event.set()
    fallback_thread.join(timeout=1.0)
    subscriber.stop()
    cap.release()
    cv2.destroyAllWindows()
