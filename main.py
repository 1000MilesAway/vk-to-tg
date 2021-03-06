import vk_api
import telebot
from settings import consts
from PIL import Image
import requests
import youtube_dl
import os
from datetime import datetime, timedelta
import pymongo
import tracemalloc
import random

class MongoCollection:

    def __init__(self, collection):
        self.client = pymongo.MongoClient(consts["DB"]["host"], consts["DB"]["port"])
        self.db = self.client[consts["DB"]["db"]]
        self.collection = self.db[collection]

    def __str__(self):
        return self.collection.name

    def insert(self, data):
        return self.collection.insert_one(data).inserted_id

    def get(self, elements=None, multiple=True):
        if multiple:
            results = self.collection.find(elements)
            return [r for r in results]
        else:
            return self.collection.find_one(elements)

    def delete(self, row):
        self.collection.delete_one(row)


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
        self.most_views_posts = daily_posts[0:post_count]

    def write_to_bd(self, db_collection):

        for post in self.most_views_posts:
            db_collection.insert(post.get_data())
        # for post in most_views_posts:
        #     if post.type == 'image':
        #         image_to_tg(post)
        #     elif post.content_type == 'video':
        #         video_to_tg(post)


class TgBot:
    def __init__(self):
        self.bot = telebot.TeleBot(consts["TOKEN"])

    def post_video(self, url):
        ydl_opts = {'outtmpl': 'video.mp4'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        f = open("video.mp4", 'rb')
        self.bot.send_video(-1001454625424, f)
        os.remove("video.mp4")

    def post_image(self, url):
        im = Image.open(requests.get(url, stream=True).raw)
        self.bot.send_photo(-1001454625424, im)


def post_to_tg(db_collection):
    tg = TgBot()
    posts = db_collection.get()
    if not posts:
        return
    random_post = random.choice(posts)
    if len(random_post["content"]) == 1 and random_post["content"][0]["type"] == 'image':
        tg.post_image(random_post["content"][0]["url"])
    elif len(random_post["content"]) == 1 and random_post["content"][0]["type"] == 'video':
        tg.post_video(random_post["content"][0]["url"])
    elif len(random_post["content"]) > 1:
        print("multiple content")
    db_collection.delete({"_id": random_post["_id"]})




def main():
    memes_db = MongoCollection("channel_1")
    # vk = VKSession()
    # pubs = ["ru2ch", "webmland"]
    # vk.parse_posts(pubs[0], 3, datetime.today() - timedelta(days=1), datetime.today() - timedelta(days=2))
    # vk.write_to_bd(memes_db)
    post_to_tg(memes_db)

if __name__ == '__main__':
    main()
