import os

import cv2
from ultralytics import YOLO

MODEL_PATH = os.path.join(os.path.dirname(__file__), "best.pt")
CONF_THRESHOLD = 0.5


def main():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Khong tim thay model: {MODEL_PATH}")

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Khong mo duoc webcam.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Khong doc duoc frame tu webcam.")
            break

        result = model(frame, verbose=False)[0]
        display = result.plot()

        status_text = "NO DETECTION"
        status_color = (0, 255, 255)

        if result.boxes is not None and len(result.boxes) > 0:
            best_idx = int(result.boxes.conf.argmax().item())
            conf = float(result.boxes.conf[best_idx].item())
            cls_id = int(result.boxes.cls[best_idx].item())
            label = str(result.names[cls_id]).lower()

            if conf >= CONF_THRESHOLD:
                if label == "drowsy":
                    status_text = f"DROWSY {conf:.2f}"
                    status_color = (0, 0, 255)
                elif label == "awake":
                    status_text = f"AWAKE {conf:.2f}"
                    status_color = (0, 255, 0)
                else:
                    status_text = f"{label.upper()} {conf:.2f}"
                    status_color = (255, 255, 0)
            else:
                status_text = f"LOW CONF {conf:.2f}"
                status_color = (0, 255, 255)

        cv2.putText(
            display,
            status_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            status_color,
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Drowsiness Detection", display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
