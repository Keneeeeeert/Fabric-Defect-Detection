import argparse
import json
from pathlib import Path

import cv2

CLASSES = ["hole", "dirt", "thread"]
COLORS = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

drawing = False
ix, iy = -1, -1
boxes = []
current_img = None
current_name = None
img_h, img_w = 0, 0


def draw_boxes(img, boxes):
    display = img.copy()
    for (x1, y1, x2, y2, cls_id) in boxes:
        c = COLORS[cls_id % len(COLORS)]
        cv2.rectangle(display, (x1, y1), (x2, y2), c, 2)
        cv2.putText(display, CLASSES[cls_id], (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 2)
    return display


def mouse_callback(event, x, y, flags, param):
    global drawing, ix, iy, boxes
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            tmp = current_img.copy()
            for (x1, y1, x2, y2, cls_id) in boxes:
                c = COLORS[cls_id % len(COLORS)]
                cv2.rectangle(tmp, (x1, y1), (x2, y2), c, 2)
            cv2.rectangle(tmp, (ix, iy), (x, y), (255, 255, 0), 1)
            cv2.imshow("Label", tmp)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = min(ix, x), min(iy, y)
        x2, y2 = max(ix, x), max(iy, y)
        if x2 - x1 > 5 and y2 - y1 > 5:
            print(f"\nBox: ({x1},{y1})-({x2},{y2}) | Class?")
            for j, name in enumerate(CLASSES):
                print(f"  [{j}] {name}")
            cls = input("> ").strip()
            if cls.isdigit() and 0 <= int(cls) < len(CLASSES):
                boxes.append((x1, y1, x2, y2, int(cls)))
                print(f"+ added [{CLASSES[int(cls)]}]")
        cv2.imshow("Label", draw_boxes(current_img, boxes))


def yolo_label(box, img_w, img_h):
    x1, y1, x2, y2, cls_id = box
    xc = ((x1 + x2) / 2) / img_w
    yc = ((y1 + y2) / 2) / img_h
    w = (x2 - x1) / img_w
    h = (y2 - y1) / img_h
    return f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}"


def main():
    global current_img, current_name, img_h, img_w, boxes

    parser = argparse.ArgumentParser()
    parser.add_argument("--cls", default="hole", help="Class dir name")
    parser.add_argument("--img", default="dataset/images/train",
                        help="Image root (train/val)")
    parser.add_argument("--label", default="dataset/labels/train",
                        help="Label root (train/val)")
    args = parser.parse_args()

    img_dir = Path(args.img) / args.cls
    label_dir = Path(args.label) / args.cls
    label_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([f for f in img_dir.iterdir() if f.suffix.lower() in IMG_EXTS])
    if not files:
        print(f"No images found in {img_dir}")
        return

    pbar_path = Path("annotate_progress.json")
    if pbar_path.exists():
        done = json.loads(pbar_path.read_text())
    else:
        done = []

    remaining = [f for f in files if f.name not in done]
    print(f"Total: {len(files)}, Done: {len(done)}, Remaining: {len(remaining)}")

    cv2.namedWindow("Label")
    cv2.setMouseCallback("Label", mouse_callback)

    print("\nControls: Draw box with mouse | [S] Save | [D] Next | [A] Prev")
    print("          [U] Undo last box | [F] Fullscreen | [Q] Quit\n")

    idx = 0
    while 0 <= idx < len(remaining):
        boxes = []
        current_name = remaining[idx].name
        current_img = cv2.imread(str(remaining[idx]))
        img_h, img_w = current_img.shape[:2]

        label_file = label_dir / (remaining[idx].stem + ".txt")
        if label_file.exists():
            for line in label_file.read_text().strip().split("\n"):
                if not line:
                    continue
                parts = line.strip().split()
                cls_id = int(parts[0])
                xc, yc, w, h = map(float, parts[1:])
                x1 = int((xc - w / 2) * img_w)
                y1 = int((yc - h / 2) * img_h)
                x2 = int((xc + w / 2) * img_w)
                y2 = int((yc + h / 2) * img_h)
                boxes.append((x1, y1, x2, y2, cls_id))

        cv2.imshow("Label", draw_boxes(current_img, boxes))
        print(f"--- [{idx+1}/{len(remaining)}] {current_name} ---")

        while True:
            key = cv2.waitKey(0) & 0xFF

            if key == ord("s"):
                lines = [yolo_label(b, img_w, img_h) for b in boxes]
                label_file.write_text("\n".join(lines) + "\n")
                done.append(current_name)
                pbar_path.write_text(json.dumps(done))
                print(f"Saved ({len(boxes)} boxes)")
                break

            elif key == ord("d"):
                if boxes:
                    lines = [yolo_label(b, img_w, img_h) for b in boxes]
                    label_file.write_text("\n".join(lines) + "\n")
                    done.append(current_name)
                    pbar_path.write_text(json.dumps(done))
                    print(f"Auto-saved ({len(boxes)} boxes)")
                idx += 1
                break

            elif key == ord("a"):
                if boxes:
                    lines = [yolo_label(b, img_w, img_h) for b in boxes]
                    label_file.write_text("\n".join(lines) + "\n")
                    done.append(current_name)
                    pbar_path.write_text(json.dumps(done))
                idx -= 1
                break

            elif key == ord("u"):
                if boxes:
                    removed = boxes.pop()
                    print(f"Undo: removed [{CLASSES[removed[4]]}]")
                    cv2.imshow("Label", draw_boxes(current_img, boxes))

            elif key == ord("f"):
                cv2.setWindowProperty("Label", cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)

            elif key == ord("q"):
                print("Bye.")
                cv2.destroyAllWindows()
                return

    cv2.destroyAllWindows()
    print("\nAll done!")


if __name__ == "__main__":
    main()
