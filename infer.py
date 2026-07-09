import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


def draw_detect(img, results, color_map):
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_id = int(box.cls.item())
            cls_name = r.names[cls_id]
            conf = float(box.conf.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            c = color_map[cls_name]
            cv2.rectangle(img, (x1, y1), (x2, y2), c, 2)
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(img, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
    return img


def draw_obb(img, results, color_map):
    for r in results:
        if r.obb is None:
            continue
        for obb in r.obb:
            cls_id = int(obb.cls.item())
            cls_name = r.names[cls_id]
            conf = float(obb.conf.item())
            pts = obb.xyxyxyxy[0].cpu().numpy().astype(np.int32).reshape(4, 2)
            c = color_map[cls_name]
            cv2.polylines(img, [pts], True, c, 2)
            cv2.putText(img, f"{cls_name} {conf:.2f}",
                        (pts[0][0], pts[0][1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
    return img


def infer_image(detect_model, obb_model, image_path, conf=0.25):
    color_map = {
        "hole": (0, 0, 255),
        "dirt": (0, 255, 0),
        "thread": (255, 0, 0),
    }

    img = cv2.imread(str(image_path))
    if img is None:
        print(f"Cannot read: {image_path}")
        return None

    det_results = detect_model(img, conf=conf, verbose=False)
    det_results = [r for r in det_results if r.boxes is not None]
    hole_dirt = 0
    for r in det_results:
        for box in r.boxes:
            cls_name = r.names[int(box.cls.item())]
            if cls_name != "thread":
                hole_dirt += 1

    obb_results = obb_model(img, conf=conf, verbose=False)
    obb_results = [r for r in obb_results if r.obb is not None]
    thread_count = sum(1 for r in obb_results for _ in r.obb)

    draw_detect(img, det_results, color_map)
    draw_obb(img, obb_results, color_map)

    total = hole_dirt + thread_count
    print(f"[{Path(image_path).name}] hole/dirt: {hole_dirt}, thread: {thread_count}, total: {total}")
    return img


def main():
    parser = argparse.ArgumentParser(description="Fabric Defect Inference")
    parser.add_argument("--source", required=True, help="Image or folder path")
    parser.add_argument("--detect-model", default="detectbest.pt")
    parser.add_argument("--obb-model", default="obbbest.pt")
    parser.add_argument("--output", default="runs/infer_output")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    print("Loading models...")
    det = YOLO(args.detect_model)
    det.to(args.device)
    obb = YOLO(args.obb_model)
    obb.to(args.device)
    print("OK")

    source = Path(args.source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

    if source.is_dir():
        files = [f for f in source.iterdir() if f.suffix.lower() in IMG_EXTS]
        print(f"Processing {len(files)} images...")
        stats = {"hole": 0, "dirt": 0, "thread": 0}
        for f in files:
            result = infer_image(det, obb, f, args.conf)
            if result is not None:
                cv2.imwrite(str(output / f"infer_{f.name}"), result)
        print(f"\nSaved to {output}")
    else:
        result = infer_image(det, obb, source, args.conf)
        if result is not None:
            save_path = output / f"infer_{source.name}"
            cv2.imwrite(str(save_path), result)
            print(f"Saved: {save_path}")
            cv2.imshow("Result", result)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
