import sys
from tornado.ioloop import IOLoop
import tornado.web

from dbmgr import DataMgr


port = 8899


class BasisRequestHandler(tornado.web.RequestHandler):
    def send_custom_error(self, code, msg):
        self.clear()
        self.set_status(code)
        self.finish("<html><body>{0}</body></html>".format(msg))


class RegisterUserHandler(BasisRequestHandler):
    def initialize(self, datamgr):
        self.datamgr = datamgr

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    def prepare(self):
        try:
            self.args = None
            if self.request.headers["Content-Type"] == "application/json":
                self.args = tornado.escape.json_decode(self.request.body)
        except Exception as ex:
            pass

    def post(self):
        try:
            userId = self.args["userId"]
            prolificId = self.args["prolificId"]

            trialsID = self.datamgr.register_user(userId, prolificId)
            self.write(trialsID)

            self.finish()
        except Exception as ex:
            print(ex)
            self.send_custom_error(500, "Internal server error")


class DataStorageHandler(BasisRequestHandler):
    def initialize(self, datamgr):
        self.datamgr = datamgr

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    def prepare(self):
        try:
            self.args = None
            if self.request.headers["Content-Type"] == "application/json":
                self.args = tornado.escape.json_decode(self.request.body)
        except Exception as ex:
            pass

    def post(self):
        try:
            userId = self.args["userId"]
            userData = self.args["data"]

            self.datamgr.store_data(userId, userData)

            self.finish()
        except Exception as ex:
            print(ex)
            self.send_custom_error(500, "Internal server error")


class WebServer(tornado.web.Application):
    def __init__(self):
        self.datamgr = DataMgr()

        handlers = [
            (r'/', tornado.web.RedirectHandler, dict(url=r"/index.htm")),
            (r'/(index\.htm)', tornado.web.StaticFileHandler, {'path': 'site'}),
            (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': 'site/js'}),
            (r'/hucemnist/static/(.*)', tornado.web.StaticFileHandler, {'path': 'site/static'}),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'site/static'}),
            (r'/api/dataStorage', DataStorageHandler, dict(datamgr=self.datamgr)),
            (r'/api/registerUser', RegisterUserHandler, dict(datamgr=self.datamgr))
        ]

        tornado.web.Application.__init__(self, handlers)


def runServer():
    WebServer().listen(port)
    IOLoop.instance().start()


def runSslServer(certfile, keyfile):
    tornado.httpserver.HTTPServer(WebServer(), ssl_options={
        "certfile": certfile,
        "keyfile": keyfile,
    }).listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        certfile = sys.argv[1]
        keyfile = sys.argv[2]

        runSslServer(certfile, keyfile)
    else:
        runServer()
