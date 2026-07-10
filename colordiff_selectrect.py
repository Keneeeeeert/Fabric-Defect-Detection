from colordiff import getlab,CIEDE2000
import cv2
import numpy as np
from PIL import Image

import tkinter as tk
from tkinter import filedialog
def select_dir():
    root = tk.Tk()
    root.withdraw()

    FolderName = filedialog.askdirectory()  #获取文件夹

    if '/' in FolderName :

        # 用\替换/，注意'\\'的用法，
        # 如果直接使用'\'，会被系统识别成转义字符
        FolderName.replace('/', '\\') 
        print(FolderName)
    return FolderName
def select_filename():
    root = tk.Tk()
    root.withdraw()
   
    FileName = filedialog.askopenfilename()  #获取文件夹中的某文件

    if '/' in FileName :
        FileName.replace('/', '\\')
        print(FileName)
    return FileName

def select_roi_image(image):
    h,w=image.shape[:2]
    if h>400 or w>400:
        scale = 400/max(h,w)
        image = cv2.resize(image,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    r = cv2.selectROI('cv2.selectROI', image, True, False)

    roi = image[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
    cv2.imshow('roi', roi)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return roi

if __name__ == '__main__': 
    #import sys
    #sys.argv=['','data/color/ch1.bmp']
    filename = select_filename()
    #image = Image.open(filename)
    image = cv2.imread(filename)
    limg = select_roi_image(np.array(image))
    rimg = select_roi_image(np.array(image))
    l1,a1,b1 = getlab(limg)
    l2,a2,b2 = getlab(rimg)

    cdiff = CIEDE2000((l1,a1,b1),(l2,a2,b2))
    print(cdiff)

    cdiff = CIEDE2000((l1,0,0),(l2,0,0))
    print(cdiff)

