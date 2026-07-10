import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

CLASSES_DETECT = ["hole", "dirt", "thread"]
CLASSES_OBB = ["thread"]
COLORS = {
    "hole": (0, 0, 255),
    "dirt": (0, 255, 0),
    "thread": (255, 0, 0),
}


def draw_detect(img, results):
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_name = r.names[int(box.cls.item())]
            if cls_name == "thread":
                continue
            conf = float(box.conf.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            c = COLORS[cls_name]
            cv2.rectangle(img, (x1, y1), (x2, y2), c, 2)
            cv2.putText(img, f"{cls_name} {conf:.2f}",
                        (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)


def draw_obb(img, results):
    for r in results:
        if r.obb is None:
            continue
        for obb in r.obb:
            cls_name = r.names[int(obb.cls.item())]
            conf = float(obb.conf.item())
            pts = obb.xyxyxyxy[0].cpu().numpy().astype(np.int32).reshape(4, 2)
            c = COLORS[cls_name]
            cv2.polylines(img, [pts], True, c, 2)
            cv2.putText(img, f"{cls_name} {conf:.2f}",
                        (pts[0][0], pts[0][1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)


def main():
    parser = argparse.ArgumentParser(description="ONNX Deployment Inference")
    parser.add_argument("--source", required=True)
    parser.add_argument("--det-onnx", default="detectbest.onnx")
    parser.add_argument("--obb-onnx", default="obbbest.onnx")
    parser.add_argument("--output", default="runs/onnx_output")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    print("Loading ONNX models (onnxruntime backend)...")
    det = YOLO(args.det_onnx, task="detect")
    obb = YOLO(args.obb_onnx, task="obb")
    print(f"  Detect classes: {det.names}")
    print(f"  OBB classes:    {obb.names}")
    print("OK")

    source = Path(args.source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

    if source.is_dir():
        files = [f for f in source.iterdir() if f.suffix.lower() in IMG_EXTS]
        print(f"\nProcessing {len(files)} images...")
        for f in files:
            img = cv2.imread(str(f))
            if img is None:
                continue
            display = img.copy()

            det_results = det(img, conf=args.conf, verbose=False)
            draw_detect(display, det_results)

            obb_results = obb(img, conf=args.conf, verbose=False)
            draw_obb(display, obb_results)

            hole_dirt = sum(1 for r in det_results if r.boxes for b in r.boxes
                            if r.names[int(b.cls.item())] != "thread")
            thread_count = sum(1 for r in obb_results if r.obb for _ in r.obb)
            print(f"  [{f.name}] hole/dirt: {hole_dirt}, thread: {thread_count}")

            cv2.imwrite(str(output / f"onnx_{f.name}"), display)
        print(f"Saved to {output}")
    else:
        img = cv2.imread(str(source))
        display = img.copy()

        det_results = det(img, conf=args.conf, verbose=False)
        draw_detect(display, det_results)

        obb_results = obb(img, conf=args.conf, verbose=False)
        draw_obb(display, obb_results)

        hole_dirt = sum(1 for r in det_results if r.boxes for b in r.boxes
                        if r.names[int(b.cls.item())] != "thread")
        thread_count = sum(1 for r in obb_results if r.obb for _ in r.obb)
        print(f"  [{source.name}] hole/dirt: {hole_dirt}, thread: {thread_count}")

        save_path = output / f"onnx_{source.name}"
        cv2.imwrite(str(save_path), display)
        print(f"Saved: {save_path}")
        cv2.imshow("ONNX Result", display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
