import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class AddInviteHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        invitees = data.get("invitees", [])

        logging.info("begin to add invitees to group %s" % groupid)

        if not groupid or not invitees:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        invitee_numbers = []
        for item in invitees:
            number = item.get("number", "")
            if number:
                invitee_numbers.append(number)

        for load_number in invitee_numbers:
            result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$pull":{"invitees":{"number":load_number}}})
        
        add_result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$addToSet":{"invitees":{"$each": invitees}}})

        if add_result:
            self.set_status(200)
        else:
            logging.error("add invitees failed")
            self.set_status(500)

        self.finish()
