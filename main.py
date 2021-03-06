import vk_api
import telebot
from settings import consts
from PIL import Image
import requests
import youtube_dl
import os
from datetime import datetime, timedelta
import pymongo


class MongoCollection:

    def __init__(self, collection):
        self.client = pymongo.MongoClient(consts["DB"]["host"], consts["DB"]["port"])
        self.db = self.client[consts["DB"]["db"]]
        self.collection = self.db[collection]

    def __str__(self):
        return self.collection.name

    def insert(self, data):
        return self.collection.insert_one(data).inserted_id

    def get(self, elements, multiple=True):
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
            self.text = post['text']
            self.date = datetime.fromtimestamp(post['date'])
            self.likes = post['likes']['count']
            self.views = post['views']['count']
            self.source = source
            if post['attachments'][0]['type'] == 'photo':
                self.content = []
                self.type = 'image'
                for im in post['attachments']:
                    self.content.append(im['photo']['sizes'][-1]['url'])

            elif post['attachments'][0]['type'] == 'video':
                self.content = []
                self.type = 'video'
                for vid in post['attachments']:
                    # response = vk.video.get(owner_id=post['owner_id'],
                    #                         videos=str(post['owner_id']) + "_" + str(vid['video']['id']))
                    self.content.append('https://vk.com/video'+str(post['owner_id']) + "_" + str(vid['video']['id']))
        except Exception:
            pass

    def get_data(self):
        dick = {"text": self.text, "date": self.date, "likes": self.likes, "views": self.views,
                "source": self.source, "type": self.type, "content": self.content}
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

    def get_posts(self, vk_public, count=50):
        most_views_posts = []
        posts = self.vk.wall.get(domain=vk_public, count=count)
        daily_posts = []
        for post in posts['items']:
            daily_posts.append(Media(post, vk_public))
        daily_posts = [x for x in daily_posts if x.date > (datetime.today() - timedelta(days=1))]
        most_views_posts.append(max(daily_posts, key=lambda post: post.likes))
        for post in most_views_posts:
            if post.content_type == 'image':
                image_to_tg(post)
            elif post.content_type == 'video':
                video_to_tg(post)


def video_to_tg(post):
    ydl_opts = {'outtmpl': 'video.mp4'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([post.video[0]])
    f = open("video.mp4", 'rb')
    bot.send_video(-1001454625424, f)
    os.remove("video.mp4")


def image_to_tg(post):
    im = Image.open(requests.get(post.image[0], stream=True).raw)
    bot.send_photo(-1001454625424, im)



bot = telebot.TeleBot(consts["TOKEN"])


def main():
    memes_db = MongoCollection("channel_1")
    memes_db.insert({"url": "sasis"})
    pubs = ["ru2ch", "webmland"]


    # post_to_tg(finall_posts)


if __name__ == '__main__':
    main()
