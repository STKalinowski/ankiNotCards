import cv2
import numpy as np
import os
from PIL import Image
import pytesseract
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import requests

#Input and OPENCV Stuff
INPUT_DIR = "./inputNotes"
UP_YELLOW = np.array([48, 255, 255])
LOW_YELLOW = np.array([20, 100, 100])

#Notion stuff
#Detect contours with opensv2 I think
DBID= "84606ef9e44449899f1ab8c68571648a"
#!!!Set notion environment Vairable!!!
NOTIONKEY = os.environ.get('NOTION')

def main():
    #Filter image and get main contours
    imgFileList = os.listdir(INPUT_DIR)
    for i in imgFileList:
        img = cv2.imread(INPUT_DIR + '/' + i)
        title = i[0:-4]

        #We use color for markers!!!
        imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(imgHSV, LOW_YELLOW, UP_YELLOW)
        res = cv2.bitwise_and(img, img, mask=mask)
        resGrey = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        contours,_ =  cv2.findContours(resGrey, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        #Filter out unintended marks by low contour complexity!
        left,mid,right = []
        count = 0
        for cont in contours:
            #First check if contour is intended! Should have high complexity
            if len(cont) > 10:
                match count%3:
                    case 0:
                        left.append(cont)
                        break
                    case 1:
                        mid.append(cont)
                        break
                    case 2:
                        right.append(cont)
                        break
                count += 1

    #Loop through, check proper left and double right
    #If next 2 right are below the next left, then fail and move on to next left!
    #If success make the two crop

    #Now make page and upload to notion
    #With Q: A: crops


def contours():
    imgFileList = os.listdir(INPUT_DIR)
    img = cv2.imread(INPUT_DIR + '/' + imgFileList[0])
    print("TITLE " + imgFileList[0][0:-4])
    imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(imgHSV, LOW_YELLOW, UP_YELLOW)
    result = cv2.bitwise_and(img, img, mask=mask)

    '''
    cv2.imshow('Initial', img)
    cv2.imshow('Mask', mask)
    cv2.imshow('Result', result)
    cv2.waitKey(0)
    '''

    resGray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    ret, resGrayThr = cv2.threshold(resGray, 127,255,0)

    cv2.imshow('Results as Grey', resGray)

    contoursSimple, hierarchy = cv2.findContours(resGrayThr, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contoursNone, hierarchy = cv2.findContours(resGrayThr, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    print(len(contoursSimple))
    print(type(contoursSimple))
    contoursSimple =  map((lambda x : x.reshape(-1,2) ), contoursSimple)
    contoursNone = map((lambda x : x.reshape(-1,2) if len(x) > 4 else [] ), contoursNone)

    im1 = result.copy()
    im2 = result.copy()
    for i in contoursSimple:
        print(len(i))
        for (x, y) in i:
            cv2.circle(im1, (x, y), 1, (255, 0, 0), 3)
    print("End1")
    for i in contoursNone:
        print(len(i))
        for (x, y) in i:
            cv2.circle(im2, (x, y), 1, (255, 0, 0), 3)
    
    out = np.hstack([im1, im2])
    cv2.imshow('Output', out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    for i in contoursSimple:
        print(len(i))
    print("Hello")

    a = [1,2,3,4,5,6,7,8,9]
    for l,mid,r in a:
        print(l)
        print(mid)
        print(r)

def getQA():
    imgFileList = os.listdir(INPUT_DIR)
    img = cv2.imread(INPUT_DIR + '/' + imgFileList[0])

    imgTxtData = [ x.split('\t') for x in pytesseract.image_to_data(img).splitlines()]  
    #['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
    # 0         1           2           3           4           5           6       7       8       9       10          11
    fig, ax = plt.subplots()
    ax.imshow(img)
    for row in imgTxtData[1:]:
        if int(row[3]) == 0:
            width = int(row[8])
            height = int(row[9])
            left = int(row[6])
            bot = int(row[7])
            rect = patches.Rectangle((left,bot),width, height, linewidth=2, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
    plt.show()
def notionTest():
    print("Notion test!")

#main()
#getQA()
#contours()
notionTest()