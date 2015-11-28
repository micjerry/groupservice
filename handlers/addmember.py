import tornado.web
import tornado.gen
import json
import io
import logging
import datetime
import motor

from bson.objectid import ObjectId
from mickey.basehandler import BaseHandler
import mickey.commonconf
import mickey.tp

from libgroup import add_groupmembers

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
        if not add_members:
            self.finish()
            return

        new_expiredate = None
        if result.get('expireAt', None):
            new_expiredate = datetime.datetime.utcnow() + datetime.timedelta(days = mickey.commonconf.conf_expire_time)
            
        result = yield add_groupmembers(coll, publish, groupid, add_members, new_expiredate)

        #add members to openapi chat room
        for item in receivers:
            mickey.tp.addgroupmember(groupid, item, "")

        if result:
            self.set_status(200)
        else:
            logging.error("add member failed")
            self.set_status(500)

        self.finish()
