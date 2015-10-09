import tornado.web
import tornado.gen
import json
import io
import logging

import motor
from bson.objectid import ObjectId

from mickey.basehandler import BaseHandler

class ListGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.userdb.users
        groupcoll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        userid = data.get("userid", "invalid")

        logging.info("begin to list group of user %s" % userid)

        if self.p_userid != userid:
            logging.error("forbiden you can not query other user")
            self.set_status(403)
            self.finish()
            return

        user = yield coll.find_one({"id":userid})
        if user:
            groups = user.get("groups", [])

            list_groups = []
            for item in groups:
                groupid = item.get("id", "")
                if groupid:
                    group = yield groupcoll.find_one({"_id":ObjectId(groupid)})
                    if group:
                        groupinfo = {}
                        groupinfo["id"] = groupid
                        groupinfo["name"] = group.get("name", "")
                        groupinfo["invite"] = group.get("invite", "")
                        groupinfo["chatid"] = group.get("chatid", "")
                        list_groups.append(groupinfo)
                
            self.write({"groups": list_groups})
        else:
            logging.error("user %s found" % userid)
            self.set_status(404)
            self.write({"error":"not found"});

        self.finish()
