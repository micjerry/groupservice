import tornado.web
import tornado.gen
import json
import io
import logging

import motor
from mickey.basehandler import BaseHandler

class UserAddGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.userdb.users
        data = json.loads(self.request.body.decode("utf-8"))
        userid = data.get("userid", "")
        groupid = data.get("groupid", "")

        logging.info("user %s begin to add group %s" % (userid, groupid))
        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        if self.p_userid != userid:
            logging.error("no right")
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_and_modify({"id":userid}, {"$push":{"groups":{"id":groupid}}})

        if result:
            self.set_status(200)
        else:
            logging.error("user add group failed")
            self.set_status(500)

        self.finish()
