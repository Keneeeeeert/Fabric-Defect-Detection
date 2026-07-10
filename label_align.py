import glob
import os
import sys

import cv2
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt

from data_loader import RescaleT
from data_loader import ToTensor
from data_loader import ToTensorLab
from data_loader import Rotate
from data_loader import GetImage,SetImage

from u2net_model import U2NET # full size version 173.6 MB
from u2net_model import U2NETP # small version u2net 4.7 MB

import torch
from torch.autograd import Variable
from torchvision import transforms#, utils

from skimage import io
from skimage.data import stereo_motorcycle
from skimage.color import rgb2gray
from skimage.transform import warp
from skimage.registration import optical_flow_tvl1,optical_flow_ilk

import json

MAX_MATCHES = 2000
GOOD_MATCH_PERCENT = 0.15

def normPRED(d):
    ma = torch.max(d)
    mi = torch.min(d)

    dn = (d-mi)/(ma-mi)

    return dn
def u2net_output(image,pred):

    predict = pred
    predict = predict.squeeze()
    predict_np = predict.cpu().data.numpy()

    im = Image.fromarray(predict_np*255).convert('RGB')
    
    imo = im.resize((image.shape[1],image.shape[0]),resample=Image.BILINEAR)

    return np.array(imo)

def save_output(image_name,mask_name,pred,needRotate=0):

    predict = pred
    predict = predict.squeeze()
    predict_np = predict.cpu().data.numpy()

    im = Image.fromarray(predict_np*255).convert('RGB')
    
    if needRotate!=0:
        im=im.rotate(needRotate)
    img_name = image_name.split(os.sep)[-1]
    image = io.imread(image_name)
    imo = im.resize((image.shape[1],image.shape[0]),resample=Image.BILINEAR)
    imo.save(mask_name)
def u2net_loadnet(model_name='u2net'):
    # --------- 1. get image path and name ---------    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(current_dir, 'u2net_model/saved_models', model_name, model_name + '.pth')   

    # --------- 3. model define ---------
    if(model_name=='u2net'):
        print("...load U2NET---173.6 MB")
        net = U2NET(3,1)
    elif(model_name=='u2netp'):
        print("...load U2NEP---4.7 MB")
        net = U2NETP(3,1)

    if torch.cuda.is_available():
        net.load_state_dict(torch.load(model_dir))
        net.cuda()
    else:
        net.load_state_dict(torch.load(model_dir, map_location='cpu'))
    net.eval()
    return net
def u2net_image(image,net):

    data_test = SetImage(image,transform=transforms.Compose([RescaleT(320),ToTensorLab(flag=0)]))
    
    inputs_test = data_test['image'].unsqueeze(0)
    inputs_test = inputs_test.type(torch.FloatTensor)

    if torch.cuda.is_available():
        inputs_test = Variable(inputs_test.cuda())
    else:
        inputs_test = Variable(inputs_test)

    d1,d2,d3,d4,d5,d6,d7= net(inputs_test)

    # normalization
    pred = d1[:,0,:,:]
    pred = normPRED(pred)

    # save results to test_results folder
    mask=u2net_output(image,pred)

    del d1,d2,d3,d4,d5,d6,d7   

    return mask
def u2net_main(filename,maskname,model_name='u2net',needRoate = 0):

    # --------- 1. get image path and name ---------    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(current_dir, 'saved_models', model_name, model_name + '.pth')
   

    # --------- 3. model define ---------
    if(model_name=='u2net'):
        print("...load U2NET---173.6 MB")
        net = U2NET(3,1)
    elif(model_name=='u2netp'):
        print("...load U2NEP---4.7 MB")
        net = U2NETP(3,1)

    if torch.cuda.is_available():
        net.load_state_dict(torch.load(model_dir))
        net.cuda()
    else:
        net.load_state_dict(torch.load(model_dir, map_location='cpu'))
    net.eval()

    # --------- 4. inference for each image ---------
    if needRoate!=0:
        data_test = GetImage(filename,transform=transforms.Compose([RescaleT(320),Rotate(needRoate),ToTensorLab(flag=0)]))
    else:
        data_test = GetImage(filename,transform=transforms.Compose([RescaleT(320),ToTensorLab(flag=0)]))

    inputs_test = data_test['image'].unsqueeze(0)
    inputs_test = inputs_test.type(torch.FloatTensor)

    if torch.cuda.is_available():
        inputs_test = Variable(inputs_test.cuda())
    else:
        inputs_test = Variable(inputs_test)

    d1,d2,d3,d4,d5,d6,d7= net(inputs_test)

    # normalization
    pred = d1[:,0,:,:]
    pred = normPRED(pred)

    # save results to test_results folder
    save_output(filename,maskname,pred,needRotate=-needRoate)

    del d1,d2,d3,d4,d5,d6,d7
def u2net_main_dir4(filename,maskname,model_name='u2net'):

    # --------- 1. get image path and name ---------    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(current_dir, 'saved_models', model_name, model_name + '.pth')
   

    # --------- 3. model define ---------
    if(model_name=='u2net'):
        print("...load U2NET---173.6 MB")
        net = U2NET(3,1)
    elif(model_name=='u2netp'):
        print("...load U2NEP---4.7 MB")
        net = U2NETP(3,1)

    if torch.cuda.is_available():
        net.load_state_dict(torch.load(model_dir))
        net.cuda()
    else:
        net.load_state_dict(torch.load(model_dir, map_location='cpu'))
    net.eval()

    opt_out=[]
    opl_max = 0
    opl_roate = 0
    for needRoate in range(0,270,90):
        # --------- 4. inference for each image ---------
        if needRoate!=0:
            data_test = GetImage(filename,transform=transforms.Compose([RescaleT(320),Rotate(needRoate),ToTensorLab(flag=0)]))
        else:
            data_test = GetImage(filename,transform=transforms.Compose([RescaleT(320),ToTensorLab(flag=0)]))

        inputs_test = data_test['image'].unsqueeze(0)
        inputs_test = inputs_test.type(torch.FloatTensor)

        if torch.cuda.is_available():
            inputs_test = Variable(inputs_test.cuda())
        else:
            inputs_test = Variable(inputs_test)

        d1,d2,d3,d4,d5,d6,d7= net(inputs_test)

        # normalization
        pred = d1[:,0,:,:]
        pred = normPRED(pred)
        
        predict = pred.squeeze().cpu().data.numpy()*255
        predict = predict.astype(np.uint8)
        _,predict = cv2.threshold(predict,128,255,cv2.THRESH_BINARY)
        opl = cv2.findNonZero(predict)
        if len(opl)>opl_max:
            opl_max = len(opl)
            opl_out=pred
            opl_roate = needRoate
        

    # save results to test_results folder
    save_output(filename,maskname,opl_out,needRotate=-opl_roate)

    del d1,d2,d3,d4,d5,d6,d7


def  alignImages(im1, im2,itern=1):

    # Convert images to grayscale

    im2Gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

    # Detect ORB features and compute descriptors.
    orb = cv2.ORB_create(MAX_MATCHES)

    keypoints2, descriptors2 = orb.detectAndCompute(im2Gray, None)

    matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)

    for k in range(0,itern):
        im1Gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        keypoints1, descriptors1 = orb.detectAndCompute(im1Gray, None)

        # Match features.    
        matches = matcher.match(descriptors1, descriptors2, None)
        matches = list(matches)
        # Sort matches by score
        matches.sort(key=lambda x: x.distance, reverse=False)

        # Remove not so good matches
        numGoodMatches = int(len(matches) * GOOD_MATCH_PERCENT)
        matches = matches[:numGoodMatches]

        # Draw top matches
        imMatches = cv2.drawMatches(im1, keypoints1, im2, keypoints2, matches, None)
        cv2.imwrite("matches_{}.jpg".format(k), imMatches)

        # Extract location of good matches
        points1 = np.zeros((len(matches), 2), dtype=np.float32)
        points2 = np.zeros((len(matches), 2), dtype=np.float32)

        for i, match in enumerate(matches):
            points1[i, :] = keypoints1[match.queryIdx].pt
            points2[i, :] = keypoints2[match.trainIdx].pt

        # Find homography
        h, mask = cv2.findHomography(points1, points2, cv2.RANSAC)

        # Use homography
        height, width, channels = im2.shape
        im1 = cv2.warpPerspective(im1, h, (width, height))

    #mix_aligned = cv2.addWeighted(im2,alpha=0.5,src2=im1,beta=0.5,gamma=1)

    return im1

def tv_align(image0,image1,isShow=False):

    #im0 = cv2.cvtColor(image0,cv2.COLOR_RGB2GRAY)
    #im1 = cv2.cvtColor(image1,cv2.COLOR_RGB2GRAY)
    
    #im_aligned_step1 = cv2.addWeighted(image0,alpha=0.5,src2=image1,beta=0.5,gamma=1)

    im0 = rgb2gray(image0)
    im1 = rgb2gray(image1)

    #isShow = False   
    if isShow:
      fig, (ax0, ax1,ax2) = plt.subplots(1, 3, figsize=(5, 10))

      ax0.imshow(im0)
      ax0.set_title("reference")
      ax0.set_axis_off()

      ax1.imshow(im1)
      ax1.set_title("moved")
      ax1.set_axis_off()

      fig.tight_layout()
      #plt.show()

    # --- Compute the optical flow
    v, u = optical_flow_tvl1(im0, im1)

    # --- Use the estimated optical flow for registration

    nr, nc = im0.shape

    row_coords, col_coords = np.meshgrid(np.arange(nr), np.arange(nc),
                                        indexing='ij')

    
    image_warp = warp(im1, np.array([row_coords + v, col_coords + u]),
                    mode='edge')
    
    image1_warp = np.zeros((nr, nc, 3))
    image1_warp[:,:,0] = warp(image1[:,:,0], np.array([row_coords + v, col_coords + u]),
                    mode='edge')
    image1_warp[:,:,1] = warp(image1[:,:,1], np.array([row_coords + v, col_coords + u]),
                    mode='edge')
    image1_warp[:,:,2] = warp(image1[:,:,2], np.array([row_coords + v, col_coords + u]),
                    mode='edge')  
    # build an RGB image with the unregistered sequence
    seq_im = np.zeros((nr, nc, 3))
    seq_im[..., 0] = im1
    seq_im[..., 1] = im0
    seq_im[..., 2] = im0

    # build an RGB image with the registered sequence
    reg_im = np.zeros((nr, nc, 3))
    reg_im[..., 0] = image_warp
    reg_im[..., 1] = im0
    reg_im[..., 2] = im0 
    if isShow:
      ax0.imshow(seq_im)
      ax0.set_title("orig diff")
      ax0.set_axis_off()

      ax1.imshow(reg_im)
      ax1.set_title("moved diff")
      ax1.set_axis_off()

      ax2.imshow(image1_warp)
      ax2.set_title("warped")
      ax2.set_axis_off()

      fig.tight_layout()
      #plt.show()

    #im_aligned_step2 = cv2.addWeighted(image0,alpha=0.5,src2=(image1_warp*255).astype(np.uint8),beta=0.5,gamma=1)

    norm = np.sqrt(u ** 2 + v ** 2)
    if isShow:
      fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(8, 4))

      # --- Sequence image sample

      ax0.imshow(image0, cmap='gray')
      ax0.set_title("Sequence image sample")
      ax0.set_axis_off()

      nvec = 64#256  # Number of vectors to be displayed along each image dimension
      nl, nc = im0.shape
      step = max(nl//nvec, nc//nvec)

      y, x = np.mgrid[:nl:step, :nc:step]
      u_ = u[::step, ::step]
      v_ = v[::step, ::step]

      ax1.imshow(norm)
      ax1.quiver(x, y, u_, v_, color='r', units='dots',
                angles='xy', scale_units='xy', lw=3)
      ax1.set_title("Optical flow magnitude and vector field")
      ax1.set_axis_off()
      fig.tight_layout()

      plt.show()

    return (image1_warp*255).astype(np.uint8),(seq_im*255).astype(np.uint8),(reg_im*255).astype(np.uint8)

def fine_diff(im1,im2,im1mask,blockg=61,blocks=21,mstep=4,grad_thr=76):
  
    h,w=im1.shape[:2]
    out = np.ones((h,w),np.uint8)*255
    h1,w1=im2.shape[:2]
    if h != h1 or w !=w1:
        return out
    
    im1 = cv2.cvtColor(im1,cv2.COLOR_RGB2GRAY)   
    im2 = cv2.cvtColor(im2,cv2.COLOR_RGB2GRAY)  

    dx=cv2.Sobel(im2,cv2.CV_64F,1,0)#计算x方向梯度
    dy=cv2.Sobel(im2,cv2.CV_64F,0,1)
    img_x=cv2.convertScaleAbs(dx)#取绝对值
    img_y=cv2.convertScaleAbs(dy)
    image_template_gradient=cv2.addWeighted(img_x,0.5,img_y,0.5,0)#按权相加
    
    
    #for y in range(blockg+1,h-blockg-1,mstep):
    #    for x in range(blockg+1,w-blockg-1,mstep):
    for y in range(blocks,h-blocks,mstep):
        for x in range(blocks,w-blocks,mstep):
            if im1mask[y,x]==0:
                continue
            if image_template_gradient[y,x]>grad_thr:
                starty1 = y-blockg
                startx1 = x-blockg
                endy1 = y+blockg
                endx1 = x+blockg
                starty2 = y-blocks
                startx2 = x-blocks
                endy2 = y+blocks
                endx2 = x+blocks
                if starty1<0:
                    starty1=0
                    endy1 = starty1+blockg*2
                if endy1>=h:
                    endy1=h-1
                    starty1=endy1-blockg*2
                if startx1<0:
                    startx1=0
                    endx1 = startx1+blockg*2
                if endx1>=w:
                    endx1=w-1
                    startx1=endx1-blockg*2

                if starty2<0:
                    starty2=0
                    endy2 = starty2+blocks*2
                if endy2>=h:
                    endy2=h-1
                    starty2=endy2-blocks*2
                if startx2<0:
                    startx2=0
                    endx2 = startx2+blocks*2
                if endx2>=w:
                    endx2=w-1
                    startx2=endx2-blocks*2

                tmat2 = im1[starty1:endy1,startx1:endx1]
                tmat1 = im2[starty2:endy2,startx2:endx2]
                result = cv2.matchTemplate(tmat2, tmat1, cv2.TM_CCOEFF_NORMED)
                minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
                out[y:y+mstep,x:x+mstep] = int(maxVal*255)
    
    return out
def compare_labels_simple(reffile,movedfile,net,dscale=0.5):
    blockg =61
    ref_img = cv2.imread(reffile,flags=cv2.IMREAD_UNCHANGED)
    move_img = cv2.imread(movedfile, flags=cv2.IMREAD_UNCHANGED)
    if False:
        if max(ref_img.shape[:2])>1024:
            ref_img = cv2.resize(ref_img,None,fx=dscale,fy=dscale,interpolation=cv2.INTER_AREA)
        if max(move_img.shape[:2])>1024:
            move_img = cv2.resize(move_img,None,fx=dscale,fy=dscale,interpolation=cv2.INTER_AREA)
    #ref_img1 = np.zeros((ref_img.shape[0]+2*blockg+1,ref_img.shape[1]+2*blockg+1,ref_img.shape[2]),np.uint8)    
    #ref_img1[blockg:ref_img.shape[0]+blockg,blockg:ref_img.shape[1]+blockg,:] = ref_img
    #move_img1 = np.zeros((move_img.shape[0]+2*blockg+1,move_img.shape[1]+2*blockg+1,move_img.shape[2]),np.uint8)    
    #move_img1[blockg:move_img.shape[0]+blockg,blockg:move_img.shape[1]+blockg,:] = move_img

    #ref_img = ref_img1
    #move_img = move_img1

    if ref_img.shape[2]>3:
        ref_mask = np.zeros((ref_img.shape[0],ref_img.shape[1],3),np.uint8)
        ref_mask[:,:,0] = ref_img[:,:,3]
        ref_mask[:,:,1] = ref_img[:,:,3]
        ref_mask[:,:,2] = ref_img[:,:,3]
        ref_img = ref_img[:,:,:3]
    else:
        ref_mask = u2net_image(ref_img,net)
    
    if move_img.shape[2]>3:
        move_mask = np.zeros((move_img.shape[0],move_img.shape[1],3),np.uint8)
        move_mask[:,:,0] = move_img[:,:,3]
        move_mask[:,:,1] = move_img[:,:,3]
        move_mask[:,:,2] = move_img[:,:,3]
        move_img = move_img[:,:,:3]
    else:
         move_mask = u2net_image(move_img,net)

    ref_img = ref_img*(ref_mask>128)
    move_img = move_img*(move_mask>128)

    imReg = alignImages(move_img, ref_img)  

    im0=cv2.cvtColor(ref_img,cv2.COLOR_BGR2GRAY)
    im1=cv2.cvtColor(imReg,cv2.COLOR_BGR2GRAY)  

    seq_im = np.zeros((ref_img.shape[0], ref_img.shape[1], 3))
    seq_im[..., 0] = im1
    seq_im[..., 1] = im0
    seq_im[..., 2] = im0

    ref_mask = cv2.cvtColor(ref_mask,cv2.COLOR_BGR2GRAY)

    _,binarymask = cv2.threshold(ref_mask,128,255,cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(binarymask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)   
    tarea=0
    for contour in contours:
        tarea += cv2.contourArea(contour)# 求轮廓面积

    ref_mask = ref_mask>128
    out = fine_diff(ref_img,imReg,ref_mask)
    return out,imReg,seq_im,tarea

def compare_labels(reffile,movedfile,dscale=0.5):
    net = u2net_loadnet()
    if net is None:
        return

    ref_img = cv2.imread(reffile, cv2.IMREAD_COLOR)
    move_img = cv2.imread(movedfile, cv2.IMREAD_COLOR)

    if max(ref_img.shape[:2])>1024:
        ref_img = cv2.resize(ref_img,None,fx=dscale,fy=dscale,interpolation=cv2.INTER_AREA)
    if max(move_img.shape[:2])>1024:
        move_img = cv2.resize(move_img,None,fx=dscale,fy=dscale,interpolation=cv2.INTER_AREA)

    ref_mask = u2net_image(ref_img,net)
    move_mask = u2net_image(move_img,net)


    ref_img = ref_img*(ref_mask>128)
    move_img = move_img*(move_mask>128)


    imReg = alignImages(move_img, ref_img)

    imReg1,u,v = tv_align(ref_img,imReg)
    

    ref_mask = cv2.cvtColor(ref_mask,cv2.COLOR_BGR2GRAY)
    '''
    cv2.imshow("tt1",imReg)
    cv2.imshow("tt2",imReg1)
    cv2.imshow("tt3",ref_mask)
    cv2.waitKey()
    cv2.destroyAllWindows()
    '''

    ref_mask = ref_mask>128
    out1 = fine_diff(ref_img,imReg,ref_mask)
    out2 = fine_diff(ref_img,imReg1,ref_mask)

    return out1,out2,imReg,imReg1,u,v
def get_report(out,jsonfile,varea,vthr = 210,athr=100,ker=9):
    _,out1 = cv2.threshold(out,vthr,255,cv2.THRESH_BINARY_INV)
    kernel = np.ones((ker,ker),np.uint8)
    out1=cv2.dilate(out1,kernel)
    contours, hierarchy = cv2.findContours(out1,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    out=cv2.cvtColor(out,cv2.COLOR_GRAY2BGR)
    
    
    vrect=[]
    tarea=0
    for contour in contours:
        area = cv2.contourArea(contour)# 求轮廓面积
        x, y, w, h = cv2.boundingRect(contour)# 求轮廓外接矩形
        if area<athr:
            continue
        tarea += area
        cv2.rectangle(out, (x, y), (x+w, y+h), (0, 0, 255), 2)
        vrect.append([x,y,x+w,y+h])
    
    f = open(jsonfile,'w')
    f.write("{")
    f.write("\"area\": {},".format(tarea))
    f.write("\"percent\": {},".format(100*(tarea/varea)))
    f.write("\"number\": {}".format(len(vrect)))
    if len(vrect):
        for i,kl in enumerate(vrect):
            f.write(",\"no{}\":[{},{},{},{}]".format(i,kl[0],kl[1],kl[2],kl[3]))
    f.write("}")
    f.close()
    return out        


if __name__ == '__main__':
    if True:
        sys.argv=['',
                '../label/1/left.png',
                '../label/1/right.png',
                'res.json',
                'testout1.jpg',              
                'testout3.jpg',
                'testout4.jpg'
                ]
        move_img = cv2.imread(sys.argv[1])
        ref_img = cv2.imread(sys.argv[2])

        imReg = alignImages(move_img, ref_img)

        imReg1,u,v = tv_align(ref_img,imReg,isShow=False)
        exit(0)
    sys.argv=['',
                #'G:/pr/FashionAI_PC/python/data/label/fail/142a1402546efb48575db914bd63b4d7.png',
                #'G:/pr/FashionAI_PC/python/data/label/fail/b5d651c1f010601e3f3ee95419ace72d.png',
                'G:/pr/FashionAI_PC/python/data/label/fail/169e0976f94c03a381acbebc66306e8c.png',
                'G:/pr/FashionAI_PC/python/data/label/fail/e7d28521fe27d3e37fcf2bbb3b320a9d.png',
                'res.json',
                'testout1.jpg',              
                'testout3.jpg',
                'testout4.jpg'
                ]
    net = u2net_loadnet()
    out,img1,img2,varea= compare_labels_simple(sys.argv[1],sys.argv[2],net)
    
    
    if len(sys.argv)>3:
        out = get_report(out,sys.argv[3],varea)
    if len(sys.argv)>4:
        cv2.imwrite(sys.argv[4],out)
    if len(sys.argv)>5:
        cv2.imwrite(sys.argv[5],img1)
    if len(sys.argv)>6:
        cv2.imwrite(sys.argv[6],img2)