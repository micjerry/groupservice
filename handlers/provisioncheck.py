import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
from mickey.users.userinter import get_bindphone
from mickey.users.usermongointer import handle_provision

class ProvisionCheckHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        data = json.loads(self.request.body.decode("utf-8"))
        userid      = data.get("userid", "")
        token       = data.get("token", "")

        logging.info("begin to check provision for user %s" % userid)

        if not userid or not token:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        result = yield usercoll.find_one({"id":userid})
        if not result:
            logging.debug("user does not exist")
            self.set_status(404)
            self.finish()
            return

        needpro = result.get("needprovision", None)

        if needpro:
            phone_number = yield get_bindphone(userid)
            if phone_number:
                logging.info("new user %s provision" % phone_number)
                yield handle_provision(token, userid, phone_number)

        self.finish()
        
