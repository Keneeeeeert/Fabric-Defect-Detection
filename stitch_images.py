import cv2
import os
import glob

def stitch(src_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for folder in os.listdir(src_dir):
        folder_path = os.path.join(src_dir, folder)
        if os.path.isdir(folder_path):
            left_path = os.path.join(folder_path, 'left.*')
            right_path = os.path.join(folder_path, 'right.*')
            
            left_files = glob.glob(left_path)
            right_files = glob.glob(right_path)
            
            if left_files and right_files:
                left = cv2.imread(left_files[0])
                right = cv2.imread(right_files[0])
                if left is not None and right is not None:
                    # ensure same height
                    if left.shape[0] != right.shape[0]:
                        right = cv2.resize(right, (right.shape[1], left.shape[0]))
                    concat = cv2.hconcat([left, right])
                    ext = os.path.splitext(left_files[0])[1]
                    out_path = os.path.join(dest_dir, f"{folder}_concat{ext}")
                    cv2.imwrite(out_path, concat)
                    print(f"Saved {out_path}")

if __name__ == '__main__':
    stitch(r'gzz-20260710\gzz\color', r'gzz-20260710\gzz\code\color_tests')
    stitch(r'gzz-20260710\gzz\label', r'gzz-20260710\gzz\code\label_tests')
