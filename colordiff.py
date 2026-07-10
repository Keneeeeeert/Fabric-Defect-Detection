from ciede2000 import CIEDE2000
import cv2
import numpy as np
def getlab(image,mfsize=11):
    image = cv2.medianBlur(image,mfsize)
    w = image.shape[1]
    h = image.shape[0]
    image = np.float32(image)
    image *= 1./255
    Lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    L,a,b = cv2.split(Lab)
    return cv2.mean(L)[0],cv2.mean(a)[0],cv2.mean(b)[0]
def colordet(filename,rscale=0.5,mfsize=11):  #51  
    image = cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_COLOR)
    image = cv2.resize(image,None,fx=rscale,fy=rscale,interpolation=cv2.INTER_NEAREST)
    #image = cv2.blur(image,(51,51))
    image = cv2.medianBlur(image,mfsize)
    w = image.shape[1]
    h = image.shape[0]
    w1 = int(w*0.2)
    w2 = int(w*0.4)

    w3 = int(w*0.6)
    w4 = int(w*0.8)

    h1 = int(h*0.3)
    h2 = int(h*0.7)
    #cv2.imshow("test1",image)
    #cv2.imshow("test2",image[h1:h2,w1:w2])
    #cv2.imshow("test3",image[h1:h2,w3:w4])
    #cv2.waitKey()
    #cv2.destroyAllWindows()
    image = np.float32(image)
    image *= 1./255
    Lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    L,a,b = cv2.split(Lab)

    #blursize=51
    #L=cv2.blur(L,(blursize,blursize))

   

    #cv2.imshow("test1",L[h1:h2,w1:w2])
    #cv2.imshow("test2",L[h1:h2,w3:w4])
    #cv2.imshow("test3",L)
    #cv2.waitKey()
    #cv2.destroyAllWindows()

    L1 = L[h1:h2,w1:w2]
    a1 = a[h1:h2,w1:w2]
    b1 = b[h1:h2,w1:w2]

    L2 = L[h1:h2,w3:w4]
    a2 = a[h1:h2,w3:w4]
    b2 = b[h1:h2,w3:w4]

    if False:
        hl1 = cv2.calcHist([L1], [0], None, [256], [0, 256])
        hl2 = cv2.calcHist([L2], [0], None, [256], [0, 256])
        #ha1 = cv2.calcHist(a1)
        #ha2 = cv2.calcHist(a2)
        #hb1 = cv2.calcHist(b1)
        #hb2 = cv2.calcHist(b2)
        hl1 = np.divide(hl1,np.max(hl1))
        hl2 = np.divide(hl2,np.max(hl2))
        print(np.sum(np.abs(hl1-hl2)),end=" ")
    cdiff = CIEDE2000((cv2.mean(L1)[0],cv2.mean(a1)[0],cv2.mean(b1)[0]),(cv2.mean(L2)[0],cv2.mean(a2)[0],cv2.mean(b2)[0]))
    #print(cdiff,end=" ")
    if False:
        c1 = cv2.mean(L1)[0]
        c2 = cv2.mean(L2)[0]
        print(np.abs(c1-c2))
    return cdiff
if __name__ == '__main__': 
    import sys
    dgree = [14.44297,11.0153785,8.7874580 ,5.5373490 ,3.85586591 ,2.5609145 ,2.04274592 ,0.8240221,0.25000]
    cvalue = colordet(sys.argv[1],rscale=0.25,mfsize=11)
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
    print('{:.3f} {}'.format(cvalue,grade)) 
    #print(cdiff)
    if False:
        colordet("./c501b275b2c1a92c264e0dcba8572e09.jpeg",rscale=0.25,mfsize=11)
        print("1  ",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\1.jpeg")
        print("1-2",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\1-2.jpeg")
        print("2  ",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\2.jpeg")
        print("2-3",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\2-3.jpeg")
        print("3  ",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\3.jpeg")
        print("3-4",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\3-4.jpeg")
        print("4  ",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\4.jpeg")
        print("4-5",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\4-5.jpeg")
        print("5  ",end=" ")
        colordet("G:\\pr\\bodyCap\\bin\\x64\\fashion\\color-standard\\5.jpeg")
