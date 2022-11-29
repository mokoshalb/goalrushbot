#!/usr/bin/env python3
"""Goal Rush Bot v2
Python bot that scrapes goals from r/soccer and sends to my server and leaves a comment on reddit/twitter.
"""

from time import sleep
import requests
import praw
from praw.models import Comment
from praw.models import Submission
from datetime import datetime
import tweepy
import pyimgur
from bs4 import BeautifulSoup
import json
import os
import subprocess
import re
import sys
import time

def main():
    reddit = redditConnect()
    twitter = twitterConnect()
    subreddit = reddit.subreddit('soccer')
    domains = ["streamja.com", "streamable.com", "streamff.com", "streamin.me", "dubz.co"]
    acceptedTeams = ['Tottenham', 'Arsenal', 'Forest', 'Palace', 'Wolves', 'Wolvehampton', 'Fulham', 'Chelsea', 'Liverpool','Southampton', 'Barcelona', 'Bournemouth', 'Juventus', 'Bayern', 'Munich', 'Manchester','Man Utd', 'Man City', 'Milan', 'Everton', 'Madrid', 'Barca', 'Dortmund', 'Leicester', 'Newcastle', 'Inter', 'Aston Villa', 'PSG', 'West Ham', 'Leeds', 'Napoli', 'PSG', 'England', 'Netherlands', 'Senegal', 'Qatar', 'Argentina', 'Brazil', 'Portugal', 'France', 'Mexico', 'Poland', 'Ghana', 'Uruguay', 'USA', 'Wales', 'Ecuador', 'Denmark', 'Australia', 'Germany', 'Croatia', 'Spain', 'Belgium', 'Canada', 'Switzerland', 'Costa Rica', 'Korea', 'Serbia', 'Tunisia', 'Cameroon', 'Morocco', 'Saudi Arabia']
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("\nListening to r/soccer...", current_time)
            posts = list(subreddit.new(limit=20))
            posts.reverse()
            for item in posts:
                link_id = item.id
                try:
                    submission = Submission(reddit, str(link_id))
                    title = str(submission.title)
                    domain = str(submission.domain)
                    if(submission.link_flair_text != "Media"):
                        print("Not a goal/video thread...")
                    elif(submission.likes == True):
                        print("Already done, skipping...")
                    elif domain not in domains:
                        print(domain+" is not supported...")
                    elif any(x in title for x in acceptedTeams) is False:
                        print(title+" is not relevant and won't give us enough traffic...")
                    elif bool(re.search(r'\d', title)) is False:
                        print(title+" is not an actual goal...")
                    else:
                        reddid = str(submission.id)
                        print("\n"+title+" is good to go!")
                        classic_url = submission.url_overridden_by_dest
                        if domain == "streamja.com":
                            r = requests.get(classic_url)
                            soup = BeautifulSoup(r.content, features='html.parser')
                            video_tags = soup.findAll('video')
                            if len(video_tags) != 0:
                                for video_tag in video_tags:
                                    mp4 = video_tag.find("source")['src']
                        elif domain == "dubz.co" or domain == "streamin.me":
                            r = requests.get(classic_url)
                            soup = BeautifulSoup(r.content, features='html.parser')
                            mp4 = soup.find("video").get("src")
                            video_tags = soup.findAll('video')
                        elif domain == "streamable.com":
                            source = requests.get(classic_url).text
                            soup = BeautifulSoup(source, features="html.parser")
                            video = soup.find("meta", attrs={'property': 'og:video'})
                            mp4 = video["content"]
                        elif domain == "streamff.com":
                            #content = requests.get("https://streamff.com/api/videos/"+ffid)
                            #mp4 = content.json()["externalLink"]
                            ffid = classic_url.split("/")[4]
                            mp4 = "https://streamff.com/uploads/"+ffid+".mp4"
                        else:
                            print("Whooot!?!")
                            mp4 = ""
                        print("Video source from "+domain+" is: "+mp4)
                        r = requests.get(mp4, allow_redirects=True, stream=True)
                        file = "temp/" + reddid + ".mp4"
                        with open(file, "wb") as vid:
                            for chunk in r.iter_content(chunk_size=1024):
                                if chunk:
                                    vid.write(chunk)
                        #open(file, 'wb').write(r.content)
                        fh = open(file, "rb")
                        fh.seek(0)
                        content = requests.post(url="https://pomf.lain.la/upload.php", files={"files[]":fh})
                        fh.close()
                        video_url = content.json()["files"][0]["url"]
                        print("Video URL: "+video_url)
                        thumbnail = "temp/"+reddid+".png"
                        command = "C:\\ffmpeg\\bin\\ffmpeg.exe -loglevel quiet -hide_banner -y -i {video} -ss 00:00:01.000 -vframes 1 {output}".format(video=file, output=thumbnail)
                        subprocess.call(command, shell=True)
                        im = pyimgur.Imgur("dd32dd3c6aaa9a0")
                        result = im.upload_image(thumbnail)
                        thumbnail_url = result.link
                        print("Thumbnail URL: "+thumbnail_url)
                        great = 0
                        tweetHeader = ""
                        if "great" in title.lower():
                            great = 1
                            tweetHeader = "Goallazzo!!!\n"
                        server_url = "https://goalrush.xyz/uppy.php"
                        myobj = {'title': title, 'video': video_url, 'thumbnail': thumbnail_url, 'is_great': great}
                        x = requests.post(server_url, data=myobj).text
                        if x == "NULL":
                            print("Null Error Occured")
                        else:
                            if(len(x) == 8):
                                url = "https://goalrush.xyz/"+x
                                downloadurl = "https://goalrush.xyz/download/"+x
                                print(title+" uploaded successfully on "+url)
                                #Reddit Comment
                                allow = True
                                submission.comments.replace_more(limit=0)
                                for top_level_comment in submission.comments.list():
                                    if(str(top_level_comment.author.name) == "AutoModerator"):
                                        print("Found AutoModerator!")
                                        comment = Comment(reddit, top_level_comment.id)
                                        numofr = 0
                                        try:
                                            comment.refresh()
                                            repliesarray = comment.replies
                                            numofr = len(list(repliesarray))
                                            if numofr > 0:
                                                for repl in comment.replies:
                                                    if repl.author.name == 'streamleak':
                                                        allow = False
                                            else:
                                                print("Arrived first!")
                                        except:
                                            print("yeye pass")
                                            pass
                                        if(allow):
                                            try:
                                                reply = "Watch or Download the video:\n\n"
                                                reply += f'* [**Watch link**]({url})'
                                                reply += "\n"
                                                reply += f'* [**Download link**]({downloadurl})'
                                                reply += '\n\n ___ '
                                                reply += "\n^(Mention `u/RedditMP4Bot` under a reddit video thread to download the video.)"
                                                comment.reply(body=reply)
                                                submission.upvote()
                                                print('Replied successfully on Reddit!')
                                            except Exception as e:
                                                print(e)
                                                sleep(5)
                                        else:
                                            print("Already responded move on!\n")
                                #Twitter Comment
                                tweetBody = title+"\n"
                                tweetFooter = "\n"+url
                                tweet = tweetHeader+tweetBody+tweetFooter
                                twitter.update_status_with_media(tweet, thumbnail)
                                print("Posted successfully on Twitter!\n")
                                os.remove("temp/"+reddid+".mp4")
                                os.remove("temp/"+reddid+".png")
                            else:
                                print("Error: "+x)
                except Exception as error:
                    print("Error occured", error)
                    crash=["Error on line {}".format(sys.exc_info()[-1].tb_lineno), "\n", error, "\n\n"]
                    timeX=str(time.time())
                    with open("error_log.txt","a") as crashLog:
                        for i in crash:
                            i=str(i)
                            crashLog.write(i)
                    sleep(10)
                    continue
            print("Current batch is done, sleeping for 2 minutes to crawl through sub again.\n")
            sleep(120)
        except Exception as death:
            print("Rate limit exceeded. Pausing for 5 minutes.\n", death)
            sleep(300)

def redditConnect(max_attempts=-1, seconds_between_attempts=60):
    attempt = 0
    while attempt != max_attempts:
        try:
            print('Authenticating Reddit...')
            redditAPI = praw.Reddit('StreamLeak', user_agent='goalrush')
            print(f'Successfully authenticated as {redditAPI.user.me()}\n')
            return redditAPI
        except praw.exceptions.APIException as error:
            print("Unable to authenticate:", error)
            print("Retrying in {} "
                  "seconds".format(seconds_between_attempts))
            sleep(seconds_between_attempts)
            attempt += 1
    raise RuntimeError('Failed to authenticate after {} '
                           'attempts'.format(max_attempts))

def twitterConnect(max_attempts=-1, seconds_between_attempts=60):
    attempt = 0
    while attempt != max_attempts:
        try:
            print('Authenticating Twitter...')
            auth = tweepy.OAuthHandler("lNa5LhFXCxftudB8LvPBhec5H", "U8vFetZVxqD4sMc6mY7suA3zv3DYXD4XF8ByN5pk39TtjFundj")
            auth.set_access_token("1546879800123473922-8DDqO6mvXvjgqmS1cPM20PkO6yDftz", "ZmHZz5e6RqpznRrjTnUfSc2VsYJcVhcS91KgIZjpL7JU3")
            twitterAPI = tweepy.API(auth)
            twitterAPI.verify_credentials()
            print("Authentication OK!\n")
            return twitterAPI
        except Exception as error:
            print("Error during authentication", error)
            print("Retrying in {} "
                  "seconds".format(seconds_between_attempts))
            sleep(seconds_between_attempts)
            attempt += 1
    raise RuntimeError('Failed to authenticate after {} '
                           'attempts'.format(max_attempts))
                           
if __name__ == '__main__':
    main()
