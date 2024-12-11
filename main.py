import tornado.ioloop
import tornado.web
import tornado.websocket
import redis
import threading
import os
import json
import logging
import random
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', 8888))

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
pubsub = redis_client.pubsub()
pubsub.subscribe('chat')

history = []
nickname_colors = {}

def get_random_color():
    letters = '0123456789ABCDEF'
    return '#' + ''.join(random.choice(letters) for _ in range(6))

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = []

    def open(self):
        WebSocketHandler.clients.append(self)
        self.update_online_count()

        for message in history:
            self.write_message(json.dumps(message))
        
        logger.info(f"new connection")

    def on_message(self, message):
        data = json.loads(message)
        nickname = data.get('nickname', 'anonymous')
        message_text = data.get('message', '')

        if nickname not in nickname_colors:
            nickname_colors[nickname] = get_random_color()

        message_data = {
            "nickname": nickname,
            "message": message_text,
            "color": nickname_colors[nickname]
        }
        history.append(message_data)

        for client in WebSocketHandler.clients:
            client.write_message(json.dumps(message_data))

        redis_client.publish('chat', message)

    def on_close(self):
        WebSocketHandler.clients.remove(self)
        self.update_online_count()
        logger.info(f"connection closed")

    def check_origin(self, origin):
        return True

    def update_online_count(self):
        online_count = len(WebSocketHandler.clients)
        message = json.dumps({"type": "online_count", "count": online_count})
        logger.info(f"users count: {online_count}")
        for client in WebSocketHandler.clients:
            client.write_message(message)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", WebSocketHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
    ])

def redis_listener():
    for message in pubsub.listen():
        if message['type'] == 'message':
            logger.info(f"got message: {message['data'].decode('utf-8')}")
            for client in WebSocketHandler.clients:
                tornado.ioloop.IOLoop.current().add_callback(lambda c=client, msg=message['data'].decode('utf-8'): c.write_message(msg))

def start_redis_listener():
    thread = threading.Thread(target=redis_listener)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")

    app = make_app()
    app.listen(SERVER_PORT, address=SERVER_HOST)
    logger.info(f"server started: http://{SERVER_HOST}:{SERVER_PORT}")
    
    start_redis_listener()
    
    tornado.ioloop.IOLoop.current().start()
