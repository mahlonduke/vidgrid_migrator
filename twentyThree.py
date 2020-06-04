# Dependencies
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

# -----------------------------------------------------------------
# OAuth setup
oauth = OAuth1Session(api_config.ttConsumerKey,
                      client_secret = api_config.ttConsumerSecret,
                      resource_owner_key = api_config.ttAccessToken,
                      resource_owner_secret = api_config.ttAccessTokenSecret)

# Create a list of unique video owners and categories so that they can be mapped, and Categories/folders/showcases can be created

# -----------------------------------------------------------------
# Function to get all of the unique owners and categories found in the videos in 23
def getUnique(videos):
    print("----Getting unique data----")

    uniqueOwners = []
    uniqueCategories = []

    for i in videos:
        print(f"Reviewing: {i}")

        owner = i['Owner']
        category = i['Category']

        if owner not in uniqueOwners:
            print(f"New unique owner: {owner}")
            uniqueOwners.append(owner)
        else:
            print(f"Known owner: {owner}")

        if category not in uniqueCategories:
            print(f"New unique category: {category}")
            uniqueCategories.append(category)
        else:
            print(f"Known category: {category}")

        print("-------------------")

    print(f'All unique owners: {uniqueOwners}')
    print(f'All unique categories: {uniqueCategories}')
    print("----Complete----")

    return(uniqueOwners, uniqueCategories)

# -----------------------------------------------------------------
# Function to map the owner
def mapOwner(videos):
    iterator = 0
    vidNum = 1
    videoCount = len(videos)

    for i in videos:
        owner = i['Owner']

        print(f"Reviewing video #{vidNum} of {videoCount}")
        print(f"Original owner: {owner}")

        # Switch for mapping the owner to the properly-formatted owner
        if owner == 'johnsmith':
            owner = 'John Smith'
            videos[iterator]['Owner'] = owner
            print(f"New owner: {owner}")

        elif owner == 'janesmith':
            owner = 'Jane Smith'
            videos[iterator]['Owner'] = owner
            print(f"New owner: {owner}")

        else:
            print(f"Owner not changed: {owner}")

        vidNum += 1

        print("--------------")

    return(videos)

# -----------------------------------------------------------------
# Get the count of total videos in 23
response = oauth.get(f'{api_config.baseURL}/api/photo/list?include_unpublished_p=1&size=1')
root = ET.fromstring(response.content)

for child in root.iter('*'):

    if child.tag == 'response':
        totalRecords = int(child.attrib['total_count'])
        print(f"Total videos: {totalRecords}")

# -----------------------------------------------------------------
# Get the videos' data from 23
if totalRecords < 100:
    totalRecords = 100

vidNum = 1
page = 1
videos = []
totalPages = math.ceil(totalRecords/100)
baseURL = api_config.baseURL



print("----- Begin -----")
print(f"Pages of 100 records each to process: {totalPages}")
while page <= totalPages:
    print(f"Getting page #{page}")

    response = oauth.get(f'{api_config.baseURL}/api/photo/list?include_unpublished_p=1&size=100&p={page}')
    root = ET.fromstring(response.content)

    vidCount = len(root.getchildren())

    # Iterate over the XML response, and create a new object containing just the desired fields
    for child in root.iter('*'):
        video = {}

        # Clear the variables for this iteration
        ownerRaw = ''
        category = ''
        title = ''
        description = ''
        link = ''

        # If the object is a photo (AKA video, thanks 23), then pull out the desired info
        if child.tag == 'photo':
            print("---------------------------------------")
            print(f"Reviewing video #{vidNum} of {vidCount} for page #{page} of {totalRecords} total records")

            try:
                videoID = child.attrib['photo_id']
                print(f"23 Video ID: {videoID}")
            except:
                print("No video ID")

            try:
                title = child.attrib['title']
                print(f"Title: {title}")

                description = child.attrib['title']
                print(f"Description: {description}")
            except:
                print("No title")
                print("No description")

            try:
                ownerRaw = child.attrib['username']
                print(f"Owner: {ownerRaw}")
            except:
                print("No User URL")

            if child.attrib['video_1080p_download'] != '':
                link = str(baseURL) + child.attrib['video_1080p_download']
                print(f"Download link: {link}")
            else:
                if child.attrib['video_medium_download'] != '':
                    link = str(baseURL) + child.attrib['video_medium_download']
                    print(f"Download link: {link}")
                else:
                    print("No download link found")

            try:
                category = child.attrib['album_title']
                print(f"Category: {category}")
            except:
                print("No category")

            try:
                protectedToken = child.attrib['protected_token']
                print(f"Protected Token: {protectedToken}")
            except:
                print("No protected token")

            # Increment the video counter
            vidNum+=1

        # If this object wasn't a video, then end this iteration
        else:
            continue

        if link == '' and protectedToken == '':
            print("Invalid video file.  Skipping")
            continue

        # Add the video information to the video object
        video['23 ID'] = videoID
        video['Owner'] = ownerRaw
        video['Category'] = category
        video['Title'] = title
        video['Description'] = description
        video['Link'] = link
        video['Protected Token'] = protectedToken

        # Add the video object to the main videos object
        videos.append(video)

    page += 1
    print("---------------------------------------")

print("----- Complete -----")
# -----------------------------------------------------------------
print("----- Getting download URLs for password-protected videos -----")
for video in videos:
    if video['Link'] == '':
        videoID = video['23 ID']
        videoTitle = video['Title']
        protectedToken = video['Protected Token']

        print(f"Getting the password protected link for \"{videoTitle}\"")

        response = oauth.get(f'{api_config.baseURL}/api/photo/list?photo_id={videoID}&token={protectedToken}')
        root = ET.fromstring(response.content)

        for child in root.iter('*'):

            # Clear the variables for this iteration
            link = ''

            # If the object is a photo (AKA video, thanks 23), then pull out the desired info
            if child.tag == 'photo':
                link = str(baseURL) + child.attrib['video_hd_download']
                print(link)
                video['Link'] = link

    else:
        print(f"Skipping \"{video['Title']}\" since it already has a valid link: {video['Link']}")


    print("---------------------------------------")


print("----- Complete -----")
# -----------------------------------------------------------------
# Get the unique records
uniqueOwners, uniqueCategories = getUnique(videos)

# Map the owners and categories
videos = mapOwner(videos)
# -----------------------------------------------------------------
# Save the video data to JSON
with open('videoData.txt', 'w') as outfile:
    json.dump(videos, outfile)
