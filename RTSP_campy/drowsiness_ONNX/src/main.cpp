#include <onnxruntime_cxx_api.h>
#include <opencv2/opencv.hpp>

#include <algorithm>
#include <array>
#include <cctype>
#include <chrono>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

struct LetterBoxInfo {
    float scale;
    int pad_x;
    int pad_y;
};

struct Detection {
    cv::Rect box;
    int class_id;
    float score;
};

static std::vector<std::string> load_classes(const std::string& path) {
    std::vector<std::string> classes;
    std::ifstream ifs(path);
    if (!ifs.is_open()) {
        return classes;
    }
    std::string line;
    while (std::getline(ifs, line)) {
        if (!line.empty()) {
            classes.push_back(line);
        }
    }
    return classes;
}

static cv::Mat letterbox(const cv::Mat& src, int input_w, int input_h, LetterBoxInfo& info) {
    const float r = std::min(static_cast<float>(input_w) / static_cast<float>(src.cols),
                             static_cast<float>(input_h) / static_cast<float>(src.rows));
    const int new_w = static_cast<int>(std::round(src.cols * r));
    const int new_h = static_cast<int>(std::round(src.rows * r));

    cv::Mat resized;
    cv::resize(src, resized, cv::Size(new_w, new_h));

    const int pad_w = input_w - new_w;
    const int pad_h = input_h - new_h;
    const int left = pad_w / 2;
    const int right = pad_w - left;
    const int top = pad_h / 2;
    const int bottom = pad_h - top;

    cv::Mat output;
    cv::copyMakeBorder(resized, output, top, bottom, left, right, cv::BORDER_CONSTANT,
                       cv::Scalar(114, 114, 114));

    info.scale = r;
    info.pad_x = left;
    info.pad_y = top;
    return output;
}

static float clip(float v, float lo, float hi) {
    return std::max(lo, std::min(v, hi));
}

static std::vector<Detection> decode_yolo(const float* data, const std::vector<int64_t>& shape,
                                          const LetterBoxInfo& lb, int img_w, int img_h,
                                          float conf_thres, float iou_thres) {
    std::vector<cv::Rect> boxes;
    std::vector<float> scores;
    std::vector<int> class_ids;

    if (!data || shape.size() != 3) {
        return {};
    }

    const int s1 = static_cast<int>(shape[1]);
    const int s2 = static_cast<int>(shape[2]);

    int num_pred = 0;
    int num_feat = 0;
    const bool channels_first = s1 < s2;  // [1, C, N] vs [1, N, C]
    if (channels_first) {
        num_feat = s1;
        num_pred = s2;
    } else {
        num_pred = s1;
        num_feat = s2;
    }

    if (num_feat < 5) {
        return {};
    }

    const int num_classes = num_feat - 4;

    for (int i = 0; i < num_pred; ++i) {
        float cx = 0.0f;
        float cy = 0.0f;
        float w = 0.0f;
        float h = 0.0f;

        if (channels_first) {
            cx = data[i + 0 * num_pred];
            cy = data[i + 1 * num_pred];
            w = data[i + 2 * num_pred];
            h = data[i + 3 * num_pred];
        } else {
            const float* row = data + i * num_feat;
            cx = row[0];
            cy = row[1];
            w = row[2];
            h = row[3];
        }

        float best_score = 0.0f;
        int best_class = -1;
        for (int c = 0; c < num_classes; ++c) {
            const float s = channels_first ? data[i + (4 + c) * num_pred] : data[i * num_feat + (4 + c)];
            if (s > best_score) {
                best_score = s;
                best_class = c;
            }
        }

        if (best_score < conf_thres || best_class < 0) {
            continue;
        }

        float x1 = (cx - 0.5f * w - static_cast<float>(lb.pad_x)) / lb.scale;
        float y1 = (cy - 0.5f * h - static_cast<float>(lb.pad_y)) / lb.scale;
        float x2 = (cx + 0.5f * w - static_cast<float>(lb.pad_x)) / lb.scale;
        float y2 = (cy + 0.5f * h - static_cast<float>(lb.pad_y)) / lb.scale;

        x1 = clip(x1, 0.0f, static_cast<float>(img_w - 1));
        y1 = clip(y1, 0.0f, static_cast<float>(img_h - 1));
        x2 = clip(x2, 0.0f, static_cast<float>(img_w - 1));
        y2 = clip(y2, 0.0f, static_cast<float>(img_h - 1));

        const int bw = std::max(1, static_cast<int>(x2 - x1));
        const int bh = std::max(1, static_cast<int>(y2 - y1));

        boxes.emplace_back(static_cast<int>(x1), static_cast<int>(y1), bw, bh);
        scores.push_back(best_score);
        class_ids.push_back(best_class);
    }

    std::vector<int> keep;
    cv::dnn::NMSBoxes(boxes, scores, conf_thres, iou_thres, keep);

    std::vector<Detection> detections;
    detections.reserve(keep.size());
    for (int idx : keep) {
        detections.push_back({boxes[idx], class_ids[idx], scores[idx]});
    }
    return detections;
}

int main(int argc, char** argv) {
    const std::string model_path = argc > 1 ? argv[1] : "models/best.onnx";
    const std::string classes_path = argc > 2 ? argv[2] : "models/classes.txt";

    const int input_size = 640;
    const float conf_thres = 0.5f;
    const float iou_thres = 0.45f;

    const bool test_no_cam = (std::getenv("TEST_NO_CAM") && std::string(std::getenv("TEST_NO_CAM")) == "1");

    std::vector<std::string> classes = load_classes(classes_path);

    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "drowsiness");
    Ort::SessionOptions sess_opts;
    sess_opts.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_EXTENDED);
    sess_opts.SetIntraOpNumThreads(1);

    Ort::Session session(env, model_path.c_str(), sess_opts);

    Ort::AllocatorWithDefaultOptions allocator;
    Ort::AllocatedStringPtr input_name_ptr = session.GetInputNameAllocated(0, allocator);
    Ort::AllocatedStringPtr output_name_ptr = session.GetOutputNameAllocated(0, allocator);
    const char* input_name = input_name_ptr.get();
    const char* output_name = output_name_ptr.get();

    std::array<int64_t, 4> input_shape = {1, 3, input_size, input_size};
    std::vector<float> input_tensor_values(static_cast<size_t>(1 * 3 * input_size * input_size));

    cv::VideoCapture cap;
    if (!test_no_cam) {
        cap.open(0);
        if (!cap.isOpened()) {
            std::cerr << "Khong mo duoc webcam\n";
            return 1;
        }
        std::cout << "Nhan q de thoat\n";
    } else {
        std::cout << "TEST_NO_CAM=1: chay 1 lan inference voi frame gia\n";
    }

    while (true) {
        const auto frame_t0 = std::chrono::steady_clock::now();
        cv::Mat frame;
        if (test_no_cam) {
            frame = cv::Mat::zeros(640, 640, CV_8UC3);
        } else {
            cap >> frame;
        }

        if (frame.empty()) {
            std::cerr << "Khong doc duoc frame\n";
            break;
        }

        LetterBoxInfo lb{};
        cv::Mat padded = letterbox(frame, input_size, input_size, lb);
        cv::Mat blob = cv::dnn::blobFromImage(padded, 1.0 / 255.0, cv::Size(input_size, input_size),
                                              cv::Scalar(), true, false, CV_32F);
        std::memcpy(input_tensor_values.data(), blob.ptr<float>(),
                    input_tensor_values.size() * sizeof(float));

        Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
        Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
            memory_info, input_tensor_values.data(), input_tensor_values.size(), input_shape.data(), input_shape.size());

        const char* input_names[] = {input_name};
        const char* output_names[] = {output_name};

        const auto infer_t0 = std::chrono::steady_clock::now();
        std::vector<Ort::Value> output_tensors = session.Run(
            Ort::RunOptions{nullptr}, input_names, &input_tensor, 1, output_names, 1);
        const auto infer_t1 = std::chrono::steady_clock::now();

        if (output_tensors.empty() || !output_tensors[0].IsTensor()) {
            std::cerr << "Output khong hop le\n";
            break;
        }

        float* out_data = output_tensors[0].GetTensorMutableData<float>();
        std::vector<int64_t> out_shape = output_tensors[0].GetTensorTypeAndShapeInfo().GetShape();

        std::vector<Detection> dets = decode_yolo(out_data, out_shape, lb, frame.cols, frame.rows, conf_thres, iou_thres);
        const auto frame_t1 = std::chrono::steady_clock::now();

        const double infer_ms =
            std::chrono::duration<double, std::milli>(infer_t1 - infer_t0).count();
        const double frame_ms =
            std::chrono::duration<double, std::milli>(frame_t1 - frame_t0).count();

        static int frame_count = 0;
        static double accum_ms = 0.0;
        frame_count++;
        accum_ms += frame_ms;
        if (frame_count >= 30) {
            const double avg_ms = accum_ms / static_cast<double>(frame_count);
            const double fps = avg_ms > 0.0 ? 1000.0 / avg_ms : 0.0;
            std::cout << "\rFPS: " << cv::format("%.2f", fps) << " | ms/frame: "
                      << cv::format("%.2f", avg_ms) << " | infer ms: "
                      << cv::format("%.2f", infer_ms) << "   " << std::flush;
            frame_count = 0;
            accum_ms = 0.0;
        }

        std::string status = "NO DETECTION";
        cv::Scalar status_color(0, 255, 255);
        float best_score = -1.0f;

        for (const auto& d : dets) {
            std::string name = d.class_id >= 0 && d.class_id < static_cast<int>(classes.size())
                                   ? classes[d.class_id]
                                   : ("cls_" + std::to_string(d.class_id));
            std::string lower = name;
            std::transform(lower.begin(), lower.end(), lower.begin(),
                           [](unsigned char c) { return static_cast<char>(std::tolower(c)); });

            cv::rectangle(frame, d.box, cv::Scalar(255, 0, 0), 2);
            cv::putText(frame, name + " " + cv::format("%.2f", d.score),
                        cv::Point(d.box.x, std::max(15, d.box.y - 6)), cv::FONT_HERSHEY_SIMPLEX, 0.6,
                        cv::Scalar(255, 255, 255), 2, cv::LINE_AA);

            if (d.score > best_score) {
                best_score = d.score;
                if (lower.find("drowsy") != std::string::npos) {
                    status = "DROWSY " + cv::format("%.2f", d.score);
                    status_color = cv::Scalar(0, 0, 255);
                } else if (lower.find("awake") != std::string::npos) {
                    status = "AWAKE " + cv::format("%.2f", d.score);
                    status_color = cv::Scalar(0, 255, 0);
                } else {
                    status = name + " " + cv::format("%.2f", d.score);
                    status_color = cv::Scalar(255, 255, 0);
                }
            }
        }

        if (test_no_cam) {
            const double fps = frame_ms > 0.0 ? 1000.0 / frame_ms : 0.0;
            std::cout << "ORT forward OK, so detection sau NMS: " << dets.size()
                      << " | FPS: " << cv::format("%.2f", fps)
                      << " | ms/frame: " << cv::format("%.2f", frame_ms)
                      << " | infer ms: " << cv::format("%.2f", infer_ms) << "\n";
            break;
        }

        cv::putText(frame, status, cv::Point(20, 40), cv::FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2,
                    cv::LINE_AA);
        cv::imshow("Drowsiness C++ ONNXRuntime", frame);

        if ((cv::waitKey(1) & 0xFF) == 'q') {
            break;
        }
    }

    if (cap.isOpened()) {
        cap.release();
    }
    cv::destroyAllWindows();
    return 0;
}
