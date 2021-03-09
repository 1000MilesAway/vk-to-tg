from celery import Celery
from main import MongoCollection, VKSession, TgBot
from datetime import datetime, timedelta
import random


app = Celery(broker="amqp://localhost")
app.conf.beat_schedule = {
    'parse': {
        'task': 'tasks.parse_vk',
        'schedule': 60.0,
        'args': ["channel_1"]
    },
    'post': {
        'task': 'tasks.post_to_tg',
        'schedule': 4.0,
        'args': ["channel_1"]
    },
}
app.conf.timezone = 'UTC'


@app.task()
def parse_vk(channel):
    tg = TgBot()
    db_collection = MongoCollection(channel)
    vk = VKSession()
    vk_pubs = ["ru2ch", "webmland"]
    for pub in vk_pubs:
        posts = vk.parse_posts(pub, 3, datetime.today() - timedelta(days=1), datetime.today() - timedelta(days=2))
        db_collection.insert([post.get_data() for post in posts])
    tg.post_message("Проведен парсинг вк, база данных пополнена")


@app.task()
def post_to_tg(channel):
    db_collection = MongoCollection(channel)
    tg = TgBot()
    posts = db_collection.get()
    if not posts:
        return
    random_post = random.choice(posts)
    print(random_post["_id"])
    if len(random_post["content"]) == 1 and random_post["content"][0]["type"] == 'image':
        tg.post_message("Случайное изображение из базы")
        tg.post_image(random_post["content"][0]["url"])
    elif len(random_post["content"]) == 1 and random_post["content"][0]["type"] == 'video':
        tg.post_message("Случайное видео из базы")
        tg.post_video(random_post["content"][0]["url"])
    elif len(random_post["content"]) > 1:
        tg.post_message("Альбом, пока не поддерживается")
    db_collection.delete({"_id": random_post["_id"]})
