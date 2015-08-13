import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class ModGroupHandler(tornado.web.RequestHandler):
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

        groupinfo = {}

        if groupname:
            groupinfo["name"] = groupname

        if owner:
            groupinfo["owner"] = owner

        if invite:
            if invite == "free" or invite == "admin":
                groupinfo["invite"] = invite

        
        result = yield coll.update({"_id":ObjectId(groupid)}, {"$set":groupinfo})

        if result:
            self.set_status(200)
            
            # send notify
            group = yield coll.find_one({"_id":ObjectId(groupid)})

            if group:
                members = group.get("members", [])
                receivers = []
                for item in members:
                    receivers.append(item.get("id", ""))

                notify = {}
                notify["name"] = "mx.group.group_change"
                notify["groupid"] = groupid

                publish.publish_multi(receivers, notify)
        else:
            logging.error("mod group failed")
            self.set_status(500)

        self.finish()
