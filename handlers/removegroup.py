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
import mickey.userfetcher

class RemoveGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "invalid")
        
        logging.info("begin to remove group %s" % groupid)

        if not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        group = yield coll.find_one({"_id":ObjectId(groupid)})
        receivers = []
        groupname = ""

        if group:
            chatid = group.get("tp_chatid", "")
            members = group.get("members", [])
            groupname = group.get("name", [])
            owner = group.get("owner", "")

            if self.p_userid != owner:
                logging.error("no right")
                self.set_status(403)
                self.finish()
                return

            #remove group from ali
            if chatid:
                mickey.tp.rmvgroup(chatid, owner, "")

            #remove group from conference
            conf_users = [x.get("id", "") for x in members]
            mickey.userfetcher.remove_users_from_conf(groupid, conf_users)

            #update every member delete 
            for item in members:
                userid = item.get("id", "")
                receivers.append(userid)
                yield usercoll.find_and_modify({"id":userid}, 
                                               {
                                                 "$pull":{"groups":{"id":groupid}},
                                                 "$pull":{"realgroups":groupid}
                                               })
            
        else:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return
        
        result = yield coll.remove( {"_id":ObjectId(groupid)}, True)
        if result:
            self.set_status(200)

            #send notify all the members
            notify = {}
            notify["name"] = "mx.group.group_dismiss"
            notify["pub_type"] = "any"
            notify["nty_type"] = "app"
            notify["groupid"] = groupid
            notify["groupname"] = groupname

            publish.publish_multi(receivers, notify)
            
            #remove maps
            mickey.maps.rmvgroup(groupid, self.p_userid, receivers)
        else:
            logging.error("remove failed groupid = %s" % groupid)
            self.set_status(500)
            self.write({"error":"not found"});

        self.finish()
