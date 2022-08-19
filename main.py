import os
import sys
import json
import sqlite3
import genanki

#Create and make sure its unique note!
def noteIdGen():
    return None

def main():
    print("Hello")
    #Import settings from files.
    #Please fill in your information appropriatly.
    
    with open("./settings.json") as f:
        entry = json.load(f)
    con = sqlite3.connect(entry[0]['ankiLocation']+'/User 1/collection.anki2')    
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(cursor.fetchall())

    #Lets just try a simple test, read the list of cards!
    with open("./testInput.json") as f:
        input = json.load(f)    
    
    #Right now hard coded, I dont think there is any other template we want top get out do we?

    noteType = cursor.execute('''SELECT id,name FROM notetypes WHERE name=? COLLATE BINARY''',("Basic",)).fetchall()
    for i in noteType:
        print(i)
        #BANDAID: Just do a if statement and break on first one found!
    #print(list(map(lambda x:x[0],cursor.description)))

    '''
    tempalteNum = noteType['id']
    tempalte = cursor.execute("SELECT * FROM tempaltes WHERE ntid=?", (tempalteNum))
    print(tempalte)
    #So to create a note we just fill in the template and then the default
    for i in input:
        print(i)
    '''
main()