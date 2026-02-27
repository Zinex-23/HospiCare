# drowsiness_ONNX

C++ webcam detection su dung ONNX Runtime (khong dung OpenCV DNN parser).

## 1) Export `best.pt` -> `best.onnx`

Tu thu muc goc project:

```bash
./venv/bin/python drowsiness_ONNX/scripts/export_onnx.py \
  --pt drowsiness_detection/best.pt \
  --out drowsiness_ONNX/models/best.onnx \
  --opset 11
```

Se tao:
- `drowsiness_ONNX/models/best.onnx`
- `drowsiness_ONNX/models/classes.txt`

## 2) Cai ONNX Runtime C++ SDK local (khong can apt)

```bash
cd drowsiness_ONNX
./scripts/setup_onnxruntime.sh
```

Mac dinh script tai version `1.24.2` vao `third_party/onnxruntime`.

## 3) Build

```bash
cd drowsiness_ONNX
cmake -S . -B build -DONNXRUNTIME_ROOT=$PWD/third_party/onnxruntime
cmake --build build -j
```

## 4) Run webcam detection

```bash
cd drowsiness_ONNX
./build/drowsiness_cam models/best.onnx models/classes.txt
```

Nhan `q` de thoat.

## 5) Test nhanh khong can webcam

```bash
cd drowsiness_ONNX
TEST_NO_CAM=1 ./build/drowsiness_cam models/best.onnx models/classes.txt
```

Neu thay dong `ORT forward OK` la ONNX Runtime chay tot.
