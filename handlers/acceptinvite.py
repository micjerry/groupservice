import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

from mickey.basehandler import BaseHandler
import mickey.tp
import mickey.maps
import mickey.users

class AcceptInviteHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")

        logging.info("begin to add members to group %s" % groupid)

        if not groupid:
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

        #get the appendings
        appendings = [x.get("id", "") for x in result.get("appendings", [])]

        #get the exist ids
        exist_ids = [x.get("id", "") for x in result.get("members", [])]

        if not self.p_userid in appendings:
            logging.error("%s are not the appendings" % self.p_userid)
            self.set_status(403)
            self.finish()
            return

        #get the remark
        remark=""
        for item in result.get("appendings", []):
            if item.get("id", "") == self.p_userid:
                remark = item.get("remark", "")

        phone_number = yield mickey.users.get_bindphone(self.p_userid)

        #add member
        modresult = yield coll.find_and_modify({"_id":ObjectId(groupid)}, 
                                               {
                                                 "$push":{"members":{"id":self.p_userid, "remark":remark}},
                                                 "$pull":{"appendings":{"id":self.p_userid}},
                                                 "$unset": {"garbage": 1}
                                               })
        if phone_number:
            yield coll.find_and_modify({"_id":ObjectId(groupid)},
                                       {
                                         "$pull":{"invitees":{"number":phone_number}},
                                         "$unset": {"garbage": 1}
                                       })

        user_rst = yield usercoll.find_and_modify({"id":self.p_userid},
                                                  {
                                                    "$push":{"groups":{"id": groupid}},
                                                    "$push":{"realgroups":groupid},
                                                    "$unset": {"garbage": 1}
                                                  }
                                                 )
        if not modresult or not user_rst:
            logging.error("add %s to members failed" % self.p_userid)
            self.set_status(500)
            self.finish()
            return


        #add members to ytx chat room
        mickey.tp.addgroupmember(groupid, self.p_userid, "")

        #publish notify to users
        add_members = []
        add_members.append({"id":self.p_userid})

        notify_mod = {}
        notify_mod["name"] = "mx.group.group_change"
        notify_mod["pub_type"] = "any"
        notify_mod["nty_type"] = "app"
        notify_mod["groupid"] = groupid
        notify_mod["action"] = "new_member"
        notify_mod["members"] = add_members

        publish.publish_multi(exist_ids, notify_mod)

        #add maps
        mickey.maps.addmembers(groupid, [self.p_userid], 1)

        self.finish()

