import argparse
import json
from pathlib import Path

import cv2
import numpy as np

CLASSES = ["thread"]
COLORS = [(255, 0, 0)]
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

points = []
current_img = None
current_name = None
img_h, img_w = 0, 0
obbs = []


def draw_obbs(img, obbs):
    display = img.copy()
    for (corners, cls_id) in obbs:
        pts = np.array(corners, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(display, [pts], True, COLORS[cls_id % len(COLORS)], 2)
        cv2.putText(display, CLASSES[cls_id],
                    (pts[0][0][0], pts[0][0][1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[cls_id % len(COLORS)], 1)
    return display


def draw_polygon(img, points, obbs):
    display = draw_obbs(img, obbs)
    if len(points) > 1:
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(display, [pts], False, (0, 255, 255), 1)
    for p in points:
        cv2.circle(display, p, 3, (0, 255, 255), -1)
    return display


def points_to_obb(pts):
    rect = cv2.minAreaRect(np.array(pts, dtype=np.float32))
    corners = cv2.boxPoints(rect)
    corners_norm = [(x / img_w, y / img_h) for x, y in corners]
    return corners_norm


def mouse_callback(event, x, y, flags, param):
    global points, obbs
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        display = draw_polygon(current_img, points, obbs)
        cv2.imshow("OBB Label", display)
    elif event == cv2.EVENT_RBUTTONDOWN and len(points) >= 3:
        corners_norm = points_to_obb(points)
        obbs.append((corners_norm, 0))
        points = []
        print(f"+ OBB ({len(corners_norm)} corners) -> {len(obbs)} boxes total")
        display = draw_obbs(current_img, obbs)
        cv2.imshow("OBB Label", display)


def obb_label(obb, img_w, img_h):
    cls_id = obb[1]
    corners = obb[0]
    parts = [str(cls_id)]
    for (xn, yn) in corners:
        parts.append(f"{xn:.6f}")
        parts.append(f"{yn:.6f}")
    return " ".join(parts)


def main():
    global current_img, current_name, img_h, img_w, points, obbs

    parser = argparse.ArgumentParser()
    parser.add_argument("--img", default="dataset_obb/images/train",
                        help="Image root (train/val)")
    parser.add_argument("--label", default="dataset_obb/labels/train",
                        help="Label root (train/val)")
    args = parser.parse_args()

    img_dir = Path(args.img) / "thread"
    label_dir = Path(args.label) / "thread"
    label_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([f for f in img_dir.iterdir() if f.suffix.lower() in IMG_EXTS])
    if not files:
        print(f"No images found in {img_dir}")
        return

    pbar_path = Path("annotate_obb_progress.json")
    if pbar_path.exists():
        done = json.loads(pbar_path.read_text())
    else:
        done = []

    remaining = [f for f in files if f.name not in done]
    print(f"Total: {len(files)}, Done: {len(done)}, Remaining: {len(remaining)}")

    cv2.namedWindow("OBB Label")
    cv2.setMouseCallback("OBB Label", mouse_callback)

    print("\nControls:")
    print("  LEFT CLICK  - Add polygon point")
    print("  RIGHT CLICK - Close polygon -> create OBB")
    print("  S - Save   D - Next   A - Prev   U - Undo   Z - Delete last point")
    print("  F - Fullscreen   Q - Quit\n")

    idx = 0
    while 0 <= idx < len(remaining):
        points = []
        obbs = []
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
                coords = list(map(float, parts[1:]))
                corners = [(coords[i] * img_w, coords[i + 1] * img_h)
                           for i in range(0, len(coords), 2)]
                obbs.append(([(x / img_w, y / img_h) for x, y in corners], cls_id))

        cv2.imshow("OBB Label", draw_obbs(current_img, obbs))
        print(f"--- [{idx+1}/{len(remaining)}] {current_name} ---")

        while True:
            key = cv2.waitKey(0) & 0xFF

            if key == ord("s"):
                lines = [obb_label(b, img_w, img_h) for b in obbs]
                label_file.write_text("\n".join(lines) + "\n")
                done.append(current_name)
                pbar_path.write_text(json.dumps(done))
                print(f"Saved ({len(obbs)} OBBs)")
                break

            elif key == ord("d"):
                if obbs:
                    lines = [obb_label(b, img_w, img_h) for b in obbs]
                    label_file.write_text("\n".join(lines) + "\n")
                    done.append(current_name)
                    pbar_path.write_text(json.dumps(done))
                    print(f"Auto-saved ({len(obbs)} OBBs)")
                idx += 1
                break

            elif key == ord("a"):
                if obbs:
                    lines = [obb_label(b, img_w, img_h) for b in obbs]
                    label_file.write_text("\n".join(lines) + "\n")
                    done.append(current_name)
                    pbar_path.write_text(json.dumps(done))
                idx -= 1
                break

            elif key == ord("u"):
                if obbs:
                    removed = obbs.pop()
                    print("Undo last OBB")
                elif points:
                    removed = points.pop()
                    print("Undo last point")
                display = draw_polygon(current_img, points, obbs)
                cv2.imshow("OBB Label", display)

            elif key == ord("z"):
                if points:
                    points.pop()
                    print(f"Removed point, {len(points)} remaining")
                    display = draw_polygon(current_img, points, obbs)
                    cv2.imshow("OBB Label", display)

            elif key == ord("f"):
                cv2.setWindowProperty("OBB Label", cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)

            elif key == ord("q"):
                print("Bye.")
                cv2.destroyAllWindows()
                return

    cv2.destroyAllWindows()
    print("\nAll done!")


if __name__ == "__main__":
    main()
