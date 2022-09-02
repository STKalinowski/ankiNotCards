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
    #Imgur Setup
    client = ImgurClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    authorizationUrl = client.get_auth_url('pin')
    webbrowser.open(authorizationUrl)
    code = input("Enter Authorization Code: ")
    creds = client.authorize(code, 'pin')
    client.set_user_auth(creds['access_token'], creds['refresh_token'])

    #Notion Setup
    notionApiURL = "https://api.notion.com/v1/pages"
    notionHeader = {
        "Notion-Version":"2022-06-28",
        "Authorization": "Bearer "+NOTIONKEY,
    }
    notionPage = {
        "parent":{ "database_id":DBID, },
        "properties":{
            "Name":{ "title":[ 
                { "text":{ "content":"" } }
                ]
            },
            "Tags":{ 
                "multi_select": [{"name": "IPAD"}]
            },
        },
        "children":[
            {
                "type":"image",
                "image":{"type":"external",
                        "external":{"url":""}}
            }
        ]
    }

    #Go through Notes
    for filename in imgFileList:
        #Filter out any hidden unwanted files!
        if filename[0] == '.':
            continue
        print("Working on " + filename)
        img = cv2.imread(INPUT_DIR + '/' + filename)
        
        imgMH = len(img)
        imgMW = len(img[0]) 
        title = filename[0:-4]

        #Upload image and make notion page
        imgurResp = client.upload_from_path(INPUT_DIR+'/'+filename, anon=False)
        imgLink = imgurResp["link"]
        notionPage["properties"]["Name"]["title"][0]["text"]["content"]=title
        notionPage["children"][0]["image"]["external"]["url"]=imgLink
        resp = requests.post(notionApiURL, headers=notionHeader, json=notionPage)
        if resp.status_code != 200:
            print(resp)
            print(resp.content)
            raise Exception("Trouble making Notion page for file: " + i)
        respJson = json.loads(resp.content.decode('utf8'))
        pageLink = respJson["url"]

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
        print("Finished with " + filename)
    print("Generating Deck Package!")
    myPackage = genanki.Package(myDeck)
    myPackage.media_files = imgList
    myPackage.write_to_file('./output.apkg')

main()