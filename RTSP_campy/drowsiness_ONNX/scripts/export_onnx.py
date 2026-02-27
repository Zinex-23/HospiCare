import argparse
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Ultralytics .pt model to ONNX for C++")
    parser.add_argument("--pt", required=True, help="Path to .pt model")
    parser.add_argument("--out", default="drowsiness_ONNX/models/best.onnx", help="Output ONNX path")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--opset", type=int, default=11, help="ONNX opset (11 is safer for OpenCV 4.6)")
    parser.add_argument(
        "--no-simplify",
        action="store_true",
        help="Disable onnxslim graph simplification",
    )
    args = parser.parse_args()

    pt_path = Path(args.pt).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(pt_path))
    exported_path = model.export(
        format="onnx",
        imgsz=args.imgsz,
        opset=args.opset,
        simplify=not args.no_simplify,
        dynamic=False,
    )

    exported_path = Path(exported_path).resolve()
    if exported_path != out_path:
        out_path.write_bytes(exported_path.read_bytes())

    names = model.names if isinstance(model.names, dict) else {i: n for i, n in enumerate(model.names)}
    classes_path = out_path.with_name("classes.txt")
    with classes_path.open("w", encoding="utf-8") as f:
        for i in sorted(names):
            f.write(f"{names[i]}\n")

    print(f"ONNX saved: {out_path}")
    print(f"Classes saved: {classes_path}")


if __name__ == "__main__":
    main()
