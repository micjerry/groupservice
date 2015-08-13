import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class RemoveMemberHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.db.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        userid = data.get("userid", "")

        logging.info("begin to remove member %s from group %s" % (userid, groupid))

        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        group = yield coll.find_one({"_id":ObjectId(groupid)})
        groupname = ""
        receivers = []

        if group:
            groupname = group.get("name", "")
            members = group.get("members", "")

            for item in members:
                receivers.append(item.get("id", ""))
      
        else:
            self.set_status(404)
            self.finish()
            return
        
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$pull":{"members":{"id":userid}}})

        # remove group from the user's group list
        yield usercoll.find_and_modify({"id":userid}, {"$pull":{"groups":{"id":groupid}}})

        if result:
            self.set_status(200)

            #send notify to deleted user
            notify = {}
            notify["name"] = "mx.group.group_kick"
            notify["groupid"] = groupid
            notify["groupname"] = groupname
            notify["userid"] = userid

            #publish.publish_one(userid, notify)

            #send notify to all user group changed
            #notify_mod = {}
            #notify_mod["name"] = "mx.group.group_change"
            #notify_mod["groupid"] = groupid
            #notify_mod["groupname"] = groupname

            publish.publish_multi(receivers, notify)
        else:
            logging.error("remove member failed groupid = %s, member = %s" % (groupid, userid))
            self.set_status(500)

        self.finish()
