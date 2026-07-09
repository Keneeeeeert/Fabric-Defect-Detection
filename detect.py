import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


def detect_image(model, image_path, output_dir, conf=0.25):
    results = model(image_path, conf=conf)
    result = results[0]

    save_path = Path(output_dir) / f"det_{Path(image_path).name}"
    annotated = result.plot()
    cv2.imwrite(str(save_path), annotated)
    print(f"Saved: {save_path}")

    if result.boxes is not None:
        for box in result.boxes:
            cls_id = int(box.cls.item())
            cls_name = model.names[cls_id]
            conf_val = float(box.conf.item())
            xyxy = box.xyxy[0].tolist()
            print(f"  [{cls_name}] conf={conf_val:.3f} | bbox={xyxy}")

    return result


def detect_video(model, video_path, output_path, conf=0.25):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Failed to open: {video_path}")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        results = model(frame, conf=conf, verbose=False)
        annotated = results[0].plot()
        out.write(annotated)

        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()
    out.release()
    print(f"Done. {frame_count} frames saved to {output_path}")


def detect_folder(model, input_dir, output_dir, conf=0.25, exts=(".jpg", ".jpeg", ".png", ".bmp")):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_files = [f for f in input_path.iterdir() if f.suffix.lower() in exts]
    print(f"Found {len(image_files)} images")

    counts = {}
    for img_file in image_files:
        results = model(img_file, conf=conf, verbose=False)
        result = results[0]

        save_path = output_path / f"det_{img_file.name}"
        annotated = result.plot()
        cv2.imwrite(str(save_path), annotated)

        if result.boxes is not None:
            for box in result.boxes:
                cls_name = model.names[int(box.cls.item())]
                counts[cls_name] = counts.get(cls_name, 0) + 1

    print(f"\nDetection summary:")
    for cls_name, cnt in sorted(counts.items()):
        print(f"  {cls_name}: {cnt}")
    print(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fabric Defect Detection")
    parser.add_argument("--model", default="runs/fabric_defect/weights/best.pt", help="Model path")
    parser.add_argument("--source", required=True, help="Image, video, or folder path")
    parser.add_argument("--output", default="runs/detect_output", help="Output directory/file")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--device", default="0", help="Device (0 for GPU, cpu for CPU)")
    parser.add_argument("--show", action="store_true", help="Show result in window")
    args = parser.parse_args()

    model = YOLO(args.model)
    if args.device:
        model.to(args.device)

    source = Path(args.source)
    output = Path(args.output)

    if source.is_dir():
        detect_folder(model, source, output, args.conf)
    elif source.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv"):
        detect_video(model, str(source), str(output), args.conf)
    else:
        output.mkdir(parents=True, exist_ok=True)
        detect_image(model, str(source), str(output), args.conf)

    if args.show and source.is_file():
        img = cv2.imread(str(output / f"det_{source.name}") if output.is_dir() else str(output))
        if img is not None:
            cv2.imshow("Detection Result", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
