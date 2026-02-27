#!/usr/bin/env bash
set -euo pipefail

VER="${1:-1.24.2}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THIRD_PARTY_DIR="${ROOT_DIR}/third_party"
ARCHIVE="onnxruntime-linux-x64-${VER}.tgz"
URL="https://github.com/microsoft/onnxruntime/releases/download/v${VER}/${ARCHIVE}"

mkdir -p "${THIRD_PARTY_DIR}"
cd "${THIRD_PARTY_DIR}"

echo "Downloading ${URL}"
curl -L --fail -o "${ARCHIVE}" "${URL}"

tar -xzf "${ARCHIVE}"
ln -sfn "onnxruntime-linux-x64-${VER}" onnxruntime

echo "ONNX Runtime installed at: ${THIRD_PARTY_DIR}/onnxruntime"
echo "Headers: ${THIRD_PARTY_DIR}/onnxruntime/include"
echo "Library: ${THIRD_PARTY_DIR}/onnxruntime/lib"
