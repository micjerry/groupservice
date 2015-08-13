import tornado.web
import tornado.gen
import json
import io
import logging

import motor

class UserRemoveGroupHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.users
        data = json.loads(self.request.body.decode("utf-8"))
        userid = data.get("userid", "")
        groupid = data.get("groupid", "")

        logging.info("user %s remove group %s" % (userid, groupid))

        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_and_modify({"id":userid}, {"$pull":{"groups":{"id":groupid}}})

        if result:
            self.set_status(200)
        else:
            logging.error("user remove group failed")
            self.set_status(500)

        self.finish()
