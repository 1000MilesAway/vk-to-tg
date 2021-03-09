import vk_api
import telebot
from settings import consts
from PIL import Image
import requests
import youtube_dl
import os
from datetime import datetime, timedelta
import pymongo
import random
from pathlib import Path


class MongoCollection:

    def __init__(self, collection):
        self.client = pymongo.MongoClient(consts["DB"]["host"], consts["DB"]["port"])
        self.db = self.client[consts["DB"]["db"]]
        self.collection = self.db[collection]

    def __str__(self):
        return self.collection.name

    def insert(self, data):
        self.collection.insert(data)

    def get(self, elements=None, multiple=True):
        if multiple:
            results = self.collection.find(elements)
            return [r for r in results]
        else:
            return self.collection.find_one(elements)

    def delete(self, row):
        self.collection.delete_one(row)

    def clear(self):
        self.collection.drop()


class Media:

    def __init__(self, post, source):
        try:
            self.content = []
            self.text = post['text']
            self.date = datetime.fromtimestamp(post['date'])
            self.likes = post['likes']['count']
            self.views = post['views']['count']
            self.source = source
            if post['attachments'][0]['type'] == 'photo':
                for im in post['attachments']:
                    self.content.append({"type": "image", "url": im['photo']['sizes'][-1]['url']})
            elif post['attachments'][0]['type'] == 'video':
                for vid in post['attachments']:
                    # response = vk.video.get(owner_id=post['owner_id'],
                    #                         videos=str(post['owner_id']) + "_" + str(vid['video']['id']))
                    self.content.append({"type": "video", "url": 'https://vk.com/video'+str(post['owner_id']) + "_" + str(vid['video']['id'])})
        except Exception:
            pass

    def get_data(self):
        dick = {"text": self.text, "date": self.date, "likes": self.likes, "views": self.views,
                "source": self.source, "content": self.content}
        return dick


class VKSession:

    @classmethod
    def auth_handler(cls):
        key = input("Enter authentication code: ")
        remember_device = True
        return key, remember_device

    def __init__(self):
        self.vk_session = vk_api.VkApi(consts["VK"]["login"], consts["VK"]["password"], auth_handler=self.auth_handler)
        try:
            self.vk_session.auth()
        except vk_api.AuthError as error_msg:
            print(error_msg)
        self.vk = self.vk_session.get_api()

    def parse_posts(self, vk_public, post_count, time_end, time_beg, count=50):
        posts = self.vk.wall.get(domain=vk_public, count=count)
        daily_posts = []
        for post in posts['items']:
            daily_posts.append(Media(post, vk_public))
        daily_posts = [x for x in daily_posts if (x.date > time_beg) and (x.date < time_end)]
        daily_posts.sort(key=lambda post: post.likes, reverse=True)
        return daily_posts[0:post_count]



class TgBot:
    def __init__(self):
        self.bot = telebot.TeleBot(consts["TOKEN"])

    def post_video(self, url):
        os.system("youtube-dl -o vid.mp4 "+url+" -f url480")
        f = open("vid.mp4", 'rb')
        self.bot.send_video(-1001454625424, f)
        f.close()
        os.remove("vid.mp4")

    def post_image(self, url):
        im = Image.open(requests.get(url, stream=True).raw)
        self.bot.send_photo(-1001454625424, im)

    def post_message(self, text):
        self.bot.send_message(-1001454625424, text)




def main():
    db_collection = MongoCollection("channel_1")
    db_collection.clear()
    vk = VKSession()
    pubs = ["ru2ch", "webmland"]
    posts = vk.parse_posts(pubs[1], 3, datetime.today() - timedelta(days=1), datetime.today() - timedelta(days=2))
    db_collection.insert([post.get_data() for post in posts])

    tg = TgBot()
    posts = db_collection.get()
    if not posts:
        return
    random_post = random.choice(posts)
    tg = TgBot()
    tg.post_video(random_post["content"][0]["url"])


if __name__ == '__main__':
    main()
