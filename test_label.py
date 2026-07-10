import cv2
import numpy as np
from label_align import u2net_loadnet, compare_labels_simple
import os

def run_label_test(concat_image_path):
    print(f"Processing label concatenated image: {concat_image_path}")
    img = cv2.imdecode(np.fromfile(concat_image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None, "Error: Could not load image."
    
    # 1. Split image into left and right
    h, w = img.shape[:2]
    mid = w // 2
    left_img = img[:, :mid]
    right_img = img[:, mid:]
    
    # Save to temp files so we can pass them to compare_labels_simple
    cv2.imencode('.png', left_img)[1].tofile('temp_left.png')
    cv2.imencode('.png', right_img)[1].tofile('temp_right.png')
    
    # 2. Run the detection
    net = u2net_loadnet()
    out, imReg, seq_im, varea = compare_labels_simple('temp_left.png', 'temp_right.png', net)
    
    # 3. Find differences and draw on a proper Red/Cyan overlay
    vthr = 210
    athr = 100
    ker = 9
    
    # Threshold the difference map
    _, out1 = cv2.threshold(out, vthr, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((ker, ker), np.uint8)
    out1 = cv2.dilate(out1, kernel)
    contours, hierarchy = cv2.findContours(out1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Generate proper Red/Cyan overlay
    proper_overlay = np.zeros_like(seq_im, dtype=np.uint8)
    proper_overlay[..., 0] = np.clip(seq_im[..., 1], 0, 255) # Blue = ref
    proper_overlay[..., 1] = np.clip(seq_im[..., 1], 0, 255) # Green = ref
    proper_overlay[..., 2] = np.clip(seq_im[..., 0], 0, 255) # Red = moved
    
    # Draw bounding boxes on proper_overlay
    vrect = []
    tarea = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, bw, bh = cv2.boundingRect(contour)
        if area < athr:
            continue
        tarea += area
        # Draw green box
        cv2.rectangle(proper_overlay, (x, y), (x+bw, y+bh), (0, 255, 0), 2)
        vrect.append([x, y, x+bw, y+bh])
        
    out_path = 'output_label.jpg'
    cv2.imencode('.jpg', proper_overlay)[1].tofile(out_path)
    
    # Clean up temp files
    if os.path.exists('temp_left.png'):
        os.remove('temp_left.png')
    if os.path.exists('temp_right.png'):
        os.remove('temp_right.png')

    res_text = f"成功检测到 {len(vrect)} 处不一致区域\n总瑕疵面积: {tarea:.1f}"
    return out_path, res_text

if __name__ == '__main__':
    path, res = run_label_test('test_label_concat.png')
    print(res)
