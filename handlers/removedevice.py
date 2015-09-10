import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
from mickey.basehandler import BaseHandler

class RemoveDeviceHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        deviceid = data.get("deviceid", "")

        logging.info("begin to remove device %s from group %s" % (deviceid, groupid))

        if not groupid or not deviceid:
            logging.error("invalid request")
            self.set_status(403)
            self.set_header("Reason-Phrase", "param error")
            self.finish()
            return
        
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$pull":{"devices":{"id":deviceid}}})

        if result:
            self.set_status(200)
        else:
            logging.error("remove member failed")
            self.set_status(500)

        self.finish()
