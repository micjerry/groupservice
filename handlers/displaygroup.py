import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class DisplayGroupHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "invalid")

        logging.info("begin to display group %s" % groupid)

        result = yield coll.find_one({"_id":ObjectId(groupid)})
        if result:
            groupinfo = {}
            groupinfo["groupid"] = groupid
            groupinfo["members"] = result.get("members", [])
            groupinfo["invitees"] = result.get("invitees", [])
            groupinfo["devices"] = result.get("devices", [])
           
            groupinfo["name"] = result.get("name", "")
            groupinfo["owner"] = result.get("owner", "")
            groupinfo["vip"] = result.get("vip", "false")
            groupinfo["vipname"] = result.get("vipname", "")
            groupinfo["invite"] = result.get("invite", "free")

            self.write(groupinfo)
        else:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.write({"error":"not found"});

        self.finish()
