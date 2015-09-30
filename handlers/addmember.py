import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
from mickey.basehandler import BaseHandler

class AddMemberHandler(BaseHandler):
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

        if not result:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return

        if result.get("invite", "free") == "admin":
            return self.redirect("/group/authadd/members")

        # if add sucess we should send notify to members which already exist
        old_receivers = [x.get("id", "") for x in result.get("members", [])]

        if not self.p_userid in old_receivers:
            logging.error("%s are not the member" % self.p_userid)
            self.set_status(403)
            self.finish()
            return


        # get members and the receivers
        receivers = list(filter(lambda x: x not in old_receivers, [x.get("id", "") for x in members]))
        add_members = [{"id":x} for x in receivers]
        
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, 
                                            {
                                              "$addToSet":{"members":{"$each": add_members}},
                                              "$unset": {"garbage": 1}
                                            })

        if result:
            self.set_status(200)
            #send notify to new members, Hi you are invited to join groupxxx
            notify = {}
            notify["name"] = "mx.group.group_invite"
            notify["pub_type"] = "any"
            notify["nty_type"] = "device"
            notify["msg_type"] = "other"
            notify["groupid"] = groupid
            notify["groupname"] = result.get("name", "")

            publish.publish_multi(receivers, notify)

            #send notify to exist members, Hi groupxxx changed, new guys added
            notify_mod = {}
            notify_mod["name"] = "mx.group.group_change"
            notify_mod["pub_type"] = "any"
            notify_mod["nty_type"] = "app"
            notify_mod["groupid"] = groupid
            notify_mod["action"] = "new_member"
            notify_mod["members"] = add_members

            publish.publish_multi(old_receivers, notify_mod)
        else:
            logging.error("add member failed")
            self.set_status(500)

        self.finish()
