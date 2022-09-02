import cv2
import numpy as np
import os
from PIL import Image
import pytesseract
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import requests
import json
import genanki
import random

from rauth import OAuth2Service
import webbrowser
from imgurpython import ImgurClient

#HARD CODED STUFF!!!!
#Input and OPENCV Stuff
INPUT_DIR = "./inputNotes"
UP_YELLOW = np.array([48, 255, 255])
LOW_YELLOW = np.array([20, 70, 70])

#Notion stuff
#Detect contours with opensv2 I think
DBID= "72f8d794702d4de4bf6e19c84c35baae"
#!!!Set notion environment Vairable!!!
NOTIONKEY = os.environ.get('NOTION')

#Anki Stuff
#To add sounds or images, set the media_files attribute on your packages
#DECK_NUM = 2077888110
DECK_NUM = 1661450634135
MODEL_NUM = 2999898880

#Imgur Stuff
CLIENT_ID = os.environ.get("IMGUR_CI")
CLIENT_SECRET = os.environ.get('IMGUR_CS')

def displayContours(img, contours):
    res = cv2.drawContours(img, contours, -1, (0,255,0),3)
    cv2.imshow('Contours', res)
    print("Press 0 to continue:")
    cv2.waitKey(0)

def getAvgY(contour):
    ySum = 0
    for i in contour:
        ySum += i[0][1]
    
    return int(ySum/len(contour)) 

def main():
    print(DECK_NUM)
    #Filter image and get main contours
    imgFileList = os.listdir(INPUT_DIR)
    if len(imgFileList) == 0:
        print("No imgs to process!")
        return 
    
    #Genanki setup
    myDeck = genanki.Deck(DECK_NUM, "Test")
    myModel = genanki.Model(
        MODEL_NUM,
        'Model With Link',
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
            {'name': 'Link'}
        ],
        templates=  [
            {
                'name': 'Card 1',
                'qfmt': '{{Question}}',
                'afmt': '{{FrontSide}} <hr id="answer"> {{Answer}} <hr id="Link"> {{Link}}'
            },
        ])
    
    #Go through 
    for i in imgFileList:
        if i[0] == '.':
            continue
        img = cv2.imread(INPUT_DIR + '/' + i)
        
        imgMH = len(img)
        imgMW = len(img[0]) 
        title = i[0:-4]

        #We use color for markers!!!
        imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(imgHSV, LOW_YELLOW, UP_YELLOW)
        res = cv2.bitwise_and(img, img, mask=mask)
        resGrey = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        contours,_ =  cv2.findContours(resGrey, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        #Filter out unintended marks by low contour complexity!
        contours = list(filter(lambda x: len(x) > 10, contours))
        contoursAvgPair = list(map(lambda x: (getAvgY(x),x), contours))
        contoursAvgPair.sort(key=lambda x: x[0])
        contours = list(map(lambda x: x[1], contoursAvgPair))

        pageLink = "https://www.youtube.com"
        imgList = []
        #With Q: A: crops
        for i in range(0,len(contours),3):
            leftX = min(contours[i], key=lambda x : x[0][0])[0][0]
            leftY = min(contours[i], key=lambda x : x[0][1])[0][1]
            mid = contours[i+1][0][0]
            rightX = max(contours[i+2], key=lambda x : x[0][0])[0][0]
            rightY = max(contours[i+2], key=lambda x : x[0][1])[0][1]
            #Add padding if possible:
            leftY = max(leftY-5, 0)
            leftX = min(leftX-5,0)
            rightY = min(rightY+5, imgMH)
            rightX = max(rightX+5, imgMW)
            qCard = img[ leftY:(min(mid[1]+6,imgMH)), leftX:rightX]
            aCard = img[ max(mid[1]-3,0):rightY, leftX:rightX ]
            qCardNum = str(random.randrange(1<<30, 1<<31))+".jpg"
            aCardNum = str(random.randrange(1<<30, 1<<31))+".jpg"
            cv2.imwrite("./cardImgs/"+qCardNum, qCard)
            cv2.imwrite("./cardImgs/"+aCardNum, aCard)
            imgList.append("./cardImgs/"+qCardNum)
            imgList.append("./cardImgs/"+aCardNum)
            #Now we add 
            #Make Note
            #Add Note to model
            #myNote = genanki.Note(myMode, ['<img src=''>', '',])
            myNote = genanki.Note(myModel, fields=['<img src='+qCardNum+'>', '<img src='+aCardNum+'>', '<a href='+pageLink+'>Page Context Link</a>'])
            myDeck.add_note(myNote)
    myPackage = genanki.Package(myDeck)
    myPackage.media_files = imgList
    myPackage.write_to_file('./output.apkg')


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
    contoursNone = list(filter(lambda x: len(x) > 10, contoursNone))
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

def displayRespJson(resp):
    print(resp)
    respJSON = json.loads(resp.content.decode('utf8'))
    for key in respJSON.keys():
        print("Key: " + key)
        print(respJSON[key])

def notionTest():
    print("Notion test!")
    apiURL = "https://api.notion.com/v1/pages"
    header = {
        "Notion-Version":"2022-06-28",
        "Authorization": "Bearer "+NOTIONKEY,
    }
    msg = {
        "parent":{ "database_id":DBID, },
        "properties":{
            "Name":{ "title":[ 
                { "text":{ "content":"Test Adding Page Title" } }
                ]
            },
            "Tags":{ 
                "multi_select": [{"name": "IPAD"}]
            },
        },
        "children":[ {
                "object":"block",
                "type":"heading_2",
                "heading_2":{ "rich_text":[
                    {"type":"text", 
                    "text":{"content":"Ipad Text"}
                    }
                ]}
            },
            { "type": "video",
                "video": {"type":"external",
                        "external":{"url":"https://i.imgur.com/a9Squjj.mp4"}}
            }
        ]
    }
    
    resp = requests.post(apiURL, headers=header, json=msg)
    displayRespJson(resp)

    if resp != None:
        return
    
    apiURL = "https://api.notion.com/v1/databases/"+DBID
    header = {
        "Notion-Version":"2022-06-28",
        "Authorization": "Bearer "+NOTIONKEY,
    }
    resp = requests.get(apiURL, headers=header)
    print(resp)
    print(resp.content)
    respJson = json.loads(resp.content.decode('utf8'))
    print(respJson["properties"])
    for key in respJson["properties"].keys():
        print("Key: " + key)
        print(respJson["properties"][key])

def imgurTest():
    print("Imgur Test")
    #resp = requests.get("https://api.imgur.com/oauth2/authorize?client_id="+CLIENT_ID+"&response_type=ACCESS_TOKEN&token_type=Bearer&expires_in=3600")
    #What we need to do is go and upload photo and get the shared url which 

    client = ImgurClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    authorizationUrl =  client.get_auth_url('pin')
    webbrowser.open(authorizationUrl)

    code = input("Enter Authorization Code: ")
    creds = client.authorize(code, 'pin')
    print(creds)
    client.set_user_auth(creds['access_token'], creds['refresh_token'])

    for i in os.listdir("./inputNotes"):
        if i[0] != '.':
            res = client.upload_from_path("./inputNotes/"+i, anon=False)
            print(res)
            #delRes = client.delete_image(res['id'])

#main()
#getQA()
#contours()
#notionTest()
imgurTest()
