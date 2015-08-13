import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class AddMemberHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        members = data.get("members", [])

        logging.info("begin to add members to group %s" % groupid)

        if not groupid or not members:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_one({"_id":ObjectId(groupid)})

        # if add sucess we should send notify to members which already exist
        old_receivers = []

        if not result:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return
        else:
            #get exist members
            old_members = result.get("members", [])
            for item in old_members:
                old_receivers.append(item.get("id", ""))

        exist_members = result.get("members", [])
        exist_ids = []
        for item in exist_members:
            exist_ids.append(item.get("id"))

        # get members and the receivers
        add_members = []
        receivers = []
        for item in members:
            userid = item.get("id", "")
            if userid and not userid in exist_ids:
                add_members.append({"id": userid})
                receivers.append(userid)
        
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$addToSet":{"members":{"$each": add_members}}})

        if result:
            self.set_status(200)
            #send notify to new members, Hi you are invited to join groupxxx
            notify = {}
            notify["name"] = "mx.group.group_invite"
            notify["groupid"] = groupid
            notify["groupname"] = result.get("name", "")

            publish.publish_multi(receivers, notify)

            #send notify to exist members, Hi groupxxx changed, new guys added
            notify_mod = {}
            notify_mod["name"] = "mx.group.group_change"
            notify_mod["groupid"] = groupid

            publish.publish_multi(old_receivers, notify_mod)
        else:
            logging.error("add member failed")
            self.set_status(500)

        self.finish()
