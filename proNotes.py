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
#WHAT USER SHOULD SET:
#INPUT_DIR -> Directory to store images
#ENV VAR: IMGUR_CI -> Imgur client id account, get it from:
#ENV VAR:



#Anki Stuff
#To add sounds or images, set the media_files attribute on your packages
DECK_NUM = 1661450634135
MODEL_NUM = 2999898880

#Imgur Stuff
CLIENT_ID = os.environ.get("IMGUR_CI")
CLIENT_SECRET = os.environ.get('IMGUR_CS')

#Function to help with debugging
def displayContours(img, contours):
    res = cv2.drawContours(img, contours, -1, (0,255,0),3)
    cv2.imshow('Contours', res)
    print("Press 0 to continue:")
    cv2.waitKey(0)

#Given a contour, calculate avg y position
#Function is used to sort the contours by y position
def getAvgY(contour):
    ySum = 0
    for i in contour:
        ySum += i[0][1]
    
    return int(ySum/len(contour)) 


def main():
    ### SETUP ### 
    #Input and OPENCV Stuff
    INPUT_DIR = "./inputNotes"
    #Using Yellow to filter and identify Q & A Markers
    UP_YELLOW = np.array([48, 255, 255])
    LOW_YELLOW = np.array([20, 70, 70])
    #The list of Images to process from the set directory.
    imgFileList = os.listdir(INPUT_DIR)
    if len(imgFileList) == 0:
        print("No imgs to process!")
        return 

    #Notion stuff
    #Detect contours with opensv2 I think
    DBID = "72f8d794702d4de4bf6e19c84c35baae"
    NOTIONKEY = os.environ.get('NOTION')
    if not NOTIONKEY:
        print("Notion secret key not set! Exiting!")
        return
    #Notion pages put into a table. 
    #Pages just contain the image of the notes processed
    #The page is then linked on the card.
    notionApiURL = "https://api.notion.com/v1/pages"
    notionHeader = {
        "Notion-Version":"2022-06-28",
        "Authorization": "Bearer " + NOTIONKEY,
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

    #Anki Stuff
    #To add sounds or images, set the media_files attribute on your packages
    #DECK_NUM: Each Anki deck has a id number, 
    #imported cards with same id automatically go to the same deck
    DECK_NUM = 1661450634135
    #MODEL_NUM: Anki card layouts have a id to be identified as.
    MODEL_NUM = 2999898880
    #Genanki setup
    myDeck = genanki.Deck(DECK_NUM, "AutoNotes")
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

    #Imgur Stuff
    #Notion does not allow direct upload of images, use imgur as host
    CLIENT_ID = os.environ.get("IMGUR_CI")
    if not CLIENT_ID:
        print("No imgur client id set! Exiting!")
        return
    CLIENT_SECRET = os.environ.get('IMGUR_CS')
    if not CLIENT_SECRET:
        print("No imgur client secret set! Exiting!")

    client = ImgurClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    authorizationUrl = client.get_auth_url('pin')
    webbrowser.open(authorizationUrl)
    code = input("Enter Authorization Code: ")
    creds = client.authorize(code, 'pin')
    client.set_user_auth(creds['access_token'], creds['refresh_token'])

    #Go through Notes
    for filename in imgFileList:
        #Filter out any hidden unwanted files!
        if filename[0] == '.':
            continue
        print("Working on " + filename)
        img = cv2.imread(INPUT_DIR + '/' + filename)
        #Dimensions & Filename
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

        #Get yellow Markers
        imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(imgHSV, LOW_YELLOW, UP_YELLOW)
        res = cv2.bitwise_and(img, img, mask=mask)
        resGrey = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        contours,_ =  cv2.findContours(resGrey, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        #Filter out unintended marks by low contour complexity!
        #Not a perfect solution, but has worked for all of my notes!
        #Deals with unintended dots that could happen when making markers.
        contours = list(filter(lambda x: len(x) > 10, contours))
        #Create list of (contour, avgY) pairs, and then sort and extract.
        contoursAvgPair = list(map(lambda x: (getAvgY(x),x), contours))
        contoursAvgPair.sort(key=lambda x: x[0])
        contours = list(map(lambda x: x[1], contoursAvgPair))

        #With sorted list, process 3 at a time.
        #i -> Top marker
        #i+1 -> Middle marker
        #i+2 -> Bottom marker
        #Top Marker is left boundary
        #Bottom Marker is right boundary
        #Question=Top->Middle, Answer=Middle->Bottom
        imgList = []
        for i in range(0,len(contours),3):
            if i+2 >= len(contours):
                continue

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

            #Make Anki card with our imgs + notion page link,
            #then add it to our deck
            myNote = genanki.Note(myModel, fields=['<img src='+qCardNum+'>', '<img src='+aCardNum+'>', '<a href='+pageLink+'>Page Context Link</a>'])
            myDeck.add_note(myNote)
        print("Finished with " + filename)

    print("Generating Deck Package!")
    myPackage = genanki.Package(myDeck)
    myPackage.media_files = imgList
    myPackage.write_to_file('./output.apkg')

main()