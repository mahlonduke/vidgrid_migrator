import requests
import logging
import boto3
from botocore.exceptions import ClientError
from base64 import b64encode
import pprint as pp
from xml.etree import ElementTree as ET
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth1Session
import urllib.parse
import random
import json
import math
import time

# API credentials
import api_config

# Vimeo setup
import vimeo

v = vimeo.VimeoClient(
    token=api_config.vimAccessToken,
    key=api_config.vimClientID,
    secret=api_config.vimSecret
)

# -----------------------------------------------------------------
# Open the JSON file containing the videos to upload to Vimeo
with open('videoData.txt') as json_file:
    videos = json.load(json_file)

# -----------------------------------------------------------------
# Setup the API headers
headers={
    "Authorization": f"Bearer {api_config.vimAccessToken}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.vimeo.*+json;version=3.4"
}

print(f"Vimeo request header: \n{headers}")

# -----------------------------------------------------------------
# Function for uploading a video
def uploadVideo(video):
    print("----------")
    print(f"Uploading the video:")

    try:
        videoTitle = video['Title']
        videoDescription = video['Description']
        videoOwner = video['Owner']
        videoURL = video['Link']
    except:
        print("This video doesn't have all of the necessary fields.  Not uploading")
        return

    print(f"Title: {videoTitle}")
    print(f"Description: {videoDescription}")
    print(f"Owner: {videoOwner}")
    print(f"Source URL: {videoURL}")

    url = "https://api.vimeo.com/me/videos"

    data = {
        "upload": {
            "approach": "pull",
            "link": videoURL
            },
        "name": videoTitle,
        "description": videoDescription,
        "privacy": {
            "view": "nobody",
            "add": "true",
            "comments": "nobody",
            "download": "true",
            "embed": "public"
            }
    }

    data = json.dumps(data)

    response = requests.post(url, headers=headers, data=data)

    print("Result:")
    print(f"Response: {response.status_code}")

    if response.status_code == 503:
        # Sleep, then try again
        print("Sleeping for 30 seconds, then trying again")
        time.sleep(30)

        response = requests.post(url, headers=headers, data=data)

        print("Result:")
        print(f"Response: {response.status_code}")

        videoLink = response.json()['link']
        videoID = videoLink.split('/')[3]

        print(f"Vimeo video link: {videoLink}")
        print(f"Vimeo video ID: {videoID}")
        print("----------")

    elif response.status_code != 201:
        pp.pprint(response.json())
        print("----------")
        return
    else:
        videoLink = response.json()['link']
        videoID = videoLink.split('/')[3]

        print(f"Vimeo video link: {videoLink}")
        print(f"Vimeo video ID: {videoID}")
        print("----------")

        return videoID

# -----------------------------------------------------------------
# Moves a video into the designated folder.  The video should already have been uploaded, and the folder created manually
# Accepts:
    # video: ID of an existing Vimeo video
    # folder: ID of an existing Vimeo folder
def moveVideoToFolder(video, folder):
    print("----------")
    print(f"Moving video #{video} to folder #{folder}")

    url = f"https://api.vimeo.com/me/projects/{folder}/videos/{video}"

    response = requests.put(url, headers=headers)

    if response.status_code == 503:
        # Sleep, then try again
        print("Sleeping for 30 seconds, then trying again")
        time.sleep(30)

    elif response.status_code == 204:
        print("Move successful")
    else:
        print("Move unsuccessful.  Details:")
        print(response.json())

        return video

    print("----------")

    return None

# -----------------------------------------------------------------
# Gets the details of existing showcases, so that they can be used to prevent duplicate showcases from being created
# Accepts: (None)
# Returns:
    # showcases: Dictionary of all existing showcases' details
    # showcaseNames: List of all existing showcases' names
    # showcaseLinks: List of all existing showcases' URLs on Vimeo
    # showcaseIDs: List of all existing showcases' IDs on Vimeo

def getShowcases():
    print("----------")
    print("Getting all existing showcases")

    url = 'https://api.vimeo.com/me/albums?page=1&per_page=100'

    showcases = []
    showcaseNames = []
    showcaseLinks = []
    showcaseIDs = []

    response = requests.get(url, headers=headers)

    totalShowcases = response.json()['total']
    currentShowcaseCount = 100
    page = 1

    print(f"{totalShowcases} total showcases")
    print(f'Getting page #1 of {math.ceil(totalShowcases/100)}')
    print(f"Response: {response.status_code}")

    while page <= math.ceil(totalShowcases/100):
        url = f'https://api.vimeo.com/me/albums?page={page}&per_page=100'

        print(f'Getting page #{page} of {math.ceil(totalShowcases/100)}')
        response = requests.get(url, headers=headers)
        print(f"Response: {response.status_code}")

        for i in response.json()['data']:
            name = i['name']
            link = i['link']
            id = link.split('/')[4]
            showcases.append({"Title": i['name'],
                              "link": link,
                             "ID": id
                             })
            print(f'Adding new showcase: {name}')
            showcaseNames.append(name)
            showcaseLinks.append(link)
            showcaseIDs.append(id)

        page += 1
        currentShowcaseCount += 100

    print(f"Final showcase data: \n{showcases}")
    print("----------")

    return showcases, showcaseNames, showcaseLinks, showcaseIDs

# -----------------------------------------------------------------
# Creates a new Vimeo showcase, and password protects it.
# Accepts:
    # name: String containing the title that will be assigned to the new Showcase
# Returns:
    # showcaseName: The title of the newly-created Showcase
    # showcaseLink: Link to view the newly-created Showcase on Vimeo
    # showcaseID: ID of the newly-created Showcase

def createShowcase(name):
    print("----------")

    shortenedName = ''
    if len(name) > 28:
        print(f"23 Category title is too long for Vimeo.  Shortening to the maximum 28 characters")

        for i in name:
            shortenedName = shortenedName + i

            if len(shortenedName) >= 28:
                break;

        name = shortenedName
        print(f"Shortened name: {name}")

    print(f"Creating a new showcase titled \"{name}\"")

    url = "https://api.vimeo.com/me/albums"

    password = name + '1234'
    print(f"Password will be: \"{password}\"")

    data = {
    "name": f"{name}",
    "privacy": "password",
    "password": f"{password}"
    }

    data = json.dumps(data)

    response = requests.post(url, headers=headers, data=data)

    print(f"Response: {response.status_code}")

    if response.status_code == 503:
        # Sleep, then try again
        print("Sleeping for 30 seconds, then trying again")
        time.sleep(30)

    elif response.status_code != 201:
        print(response.json())

    showcaseName = response.json()['name']
    showcaseLink = response.json()['link']
    showcaseURI = response.json()['uri']
    showcaseID = showcaseURI.split('/')[4]

    print("New showcase details")
    print(f"  ID: {showcaseID}")
    print(f"  Name: {showcaseName}")
    print(f"  URI: {showcaseURI}")
    print(f"  Link: {showcaseLink}")

    print("----------")

    return showcaseName, showcaseLink, showcaseID

# -----------------------------------------------------------------
# Adds an existing video on Vimeo to an existing Showcase on Vimeo
# Accepts:
    # videoID: int, ID of an existing video on Vimeo
    # showcaseID: int, ID of an existing Showcase on Vimeo
# Returns:
    # String - "Successful" or "Unsuccessful"

def addToShowcase(videoID, showcaseID):
    print("----------")
    print(f"Adding video ID #{videoID} to showcase ID #{showcaseID}")

    url = f"https://api.vimeo.com/users/115805446/albums/{showcaseID}/videos/{videoID}"

    response = requests.put(url, headers=headers)

    if response.status_code == 204:
        print("Video successfully added to showcase")
        print("----------")

        return "Successful"
    else:
        print(f"Error {response.status_code}")
        print(response.json())
        print("----------")

        return "Unsuccessful"

# -----------------------------------------------------------------
# Upload videos
print(f"Uploading {len(videos)} total videos")

iterator = 1

for video in videos:
    print(f"Uploading video #{iterator} of {len(videos)}")
    video['Vimeo ID'] = uploadVideo(video)
    print(video['Vimeo ID'])
    iterator += 1

print("---------------------------------------")
print("-----Upload complete-----")

# -----------------------------------------------------------------
# Move the videos that were just uploaded into a single folder
videoCount = len(videos)
iterator = 1

badVideos = []

for video in videos:
    print(f"Video #{iterator} of {videoCount}")

    videoID = video['Vimeo ID']
    if video['Category'] == '':
        # Vimeo folder ID to upload videos to when it was not previously part of a category/folder
        folderID = 00000000
    else:
        # Vimeo folder ID to upload videos to when it was previously part of a specific category/folder
        folderID = 00000000

    badVideo = moveVideoToFolder(videoID, folderID)

    badVideos.append(badVideo)

    iterator += 1

# -----------------------------------------------------------------
# Get existing showcases
showcases, showcaseNames, showcaseLinks, showcaseIDs = getShowcases()

# -----------------------------------------------------------------
# Add the uploaded videos to Showcases
videoCount = len(videos)
iterator = 1

showcaseNamesShortened = showcaseNames

print("Adding videos to showcases")

for video in videos:
    print(f"Processing video #{iterator} of {videoCount}")

    if iterator <= 1546:
        print("Already processed this video.  Skipping")
        iterator += 1
        continue

    category = video['Category']

    if category == '' or category == None:
        print("This video didn't have a category.  Skipping")
        continue

    print(f"Video category from 23: {category}")

    if category not in showcaseNames and category not in showcaseNamesShortened:
        print(f"The video \"{video['Title']}\" is part of a category that doesn't exist as a showcase yet.  Creating the showcase and adding it to it")
        showcaseName, showcaseLink, showcaseID = createShowcase(category)

        videoID = video['Vimeo ID']

        video['Showcase Add Status'] = addToShowcase(videoID, showcaseID)

        # Add the newly-created showcase's information to the lists of existing showcases, so that we don't try and create it again
        showcaseNamesShortened.append(showcaseName)
        showcaseNames.append(category)
        showcaseLinks.append(showcaseLink)
        showcaseIDs.append(showcaseID)

    else:
        print(f"The video \"{video}\" is part of a category with an existing showcase.  Adding to it")
        
        try:
            existingShowcaseIndex = showcaseNames.index(category)
            showcaseIndex = existingShowcaseIndexShortened
        except:
            existingShowcaseIndexShortened = showcaseNamesShortened.index(category)
            showcaseIndex = existingShowcaseIndex

        showcaseID = showcaseIDs[showcaseIndex]
        videoID = video['Vimeo ID']

        video['Showcase Add Status'] = addToShowcase(videoID, showcaseID)


    iterator += 1

print("---------Complete---------")
