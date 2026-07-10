import sys
import cv2
import numpy as np
from colordiff import colordet

def run_color_test(concat_image_path):
    print(f"Processing color concatenated image: {concat_image_path}")
    # colordet processes the concatenated image directly.
    # It returns Grade, Score, Score1 (where Score is the primary color diff)
    try:
        cvalue = colordet(concat_image_path)
        dgree = [14.44297,11.0153785,8.7874580 ,5.5373490 ,3.85586591 ,2.5609145 ,2.04274592 ,0.8240221,0.25000]
        grade=1
        if cvalue>(dgree[0]+dgree[1])*0.5:
            grade=1
        elif cvalue>(dgree[1]+dgree[2])*0.5:
            grade = 1.5
        elif cvalue>(dgree[2]+dgree[3])*0.5:
            grade = 2
        elif cvalue>(dgree[3]+dgree[4])*0.5:
            grade = 2.5
        elif cvalue>(dgree[4]+dgree[5])*0.5:
            grade = 3
        elif cvalue>(dgree[5]+dgree[6])*0.5:
            grade = 3.5   
        elif cvalue>(dgree[6]+dgree[7])*0.5:
            grade = 4
        elif cvalue>(dgree[7]+dgree[8])*0.5:
            grade = 4.5 
        else:
            grade = 5   
            
        res_text = f"色差等级 (Grade): {grade}\n色差评分 (Score): {cvalue:.4f}"
        
        # Color test doesn't output a modified image, just return the original input image path
        return concat_image_path, res_text
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

if __name__ == '__main__':
    path, res = run_color_test('color_concat_test.bmp')
    print(res)
