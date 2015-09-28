import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
from mickey.basehandler import BaseHandler

class ModGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        groupname = data.get("name", "")
        owner = data.get("owner", "")
        vip = data.get("vip", "")
        vipname = data.get("vipname", "")
        invite = data.get("invite", "")

        logging.info("begin to mod group, id = %s, groupname = %s, owner = %s, vip = %s, invite = %s" % (groupid, groupname, owner, vip, invite))

        if not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        group = yield coll.find_one({"_id":ObjectId(groupid)})
        if not group:
            logging.error("group not exist")
            self.set_status(404)
            self.finish()
            return
        else:
            owner = group.get("owner", "")
            invite = group.get("invite", "free")
            if self.p_userid != owner and invite == "admin":
                logging.error("you are not the owner")
                self.set_status(403)
                self.finish()
                return

        groupinfo = {}

        if groupname:
            groupinfo["name"] = groupname

        if owner:
            groupinfo["owner"] = owner
        
        result = yield coll.update({"_id":ObjectId(groupid)}, 
                                   {
                                     "$set":groupinfo,
                                     "$unset": {"garbage": 1}
                                   })

        if result:
            self.set_status(200)
            receivers = [x.get("id", "") for x in group.get("members", [])]

            notify = {}
            notify["name"] = "mx.group.group_change"
            notify["nty_type"] = "app"
            notify["groupid"] = groupid
            notify["action"] = "info_change"

            publish.publish_multi(receivers, notify)
        else:
            logging.error("mod group failed")
            self.set_status(500)

        self.finish()
