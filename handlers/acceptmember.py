import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
import mickey.userfetcher
from mickey.basehandler import BaseHandler

class AcceptMemberHandler(BaseHandler):
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

        if result.get("owner", "") != self.p_userid:
            logging.error("%s are not the owner" % self.p_userid)
            self.set_status(403)
            self.finish()
            return;

        #get exist members
        exist_ids = [x.get("id", "") for x in result.get("members", [])]

        # get members and the receivers
        add_members = list(filter(lambda x: x not in exist_ids, [x.get("id", "") for x in members]))

        notify = {}
        notify["name"] = "mx.group.authgroup_invited"
        notify["groupid"] = groupid
        notify["groupname"] = result.get("name", "")
        opter_info = yield mickey.userfetcher.getcontact(self.p_userid)
        if opter_info:
            notify["username"] = opter_info.get("name", "")
        else:
            logging.error("get user info failed %s" % self.p_userid)

        append_result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$addToSet":{"appendings":{"$each": add_members}}})
        if append_result:
            self.set_status(200)
            publish.publish_multi(add_members, notify)
        else:
            self.set_status(500)
            logging.error("add user failed %s" % groupid)
            return

        self.finish()
