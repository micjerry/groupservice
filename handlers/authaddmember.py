import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
import mickey.userfetcher
from mickey.basehandler import BaseHandler

from libgroup import filter_mydevice
from libgroup import add_groupmembers

class AuthAddMemberHandler(BaseHandler):
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

        if result.get("invite", "free") == "free":
            return self.redirect("/group/add/members")

        #get exist members
        exist_ids = [x.get("id", "") for x in result.get("members", [])]

        if not self.p_userid in exist_ids:
            logging.error("%s are not the member" % self.p_userid)
            self.set_status(403)
            self.finish()
            return

        # get members and the receivers
        add_members = list(filter(lambda x: x not in exist_ids, [x.get("id", "") for x in members]))

        owner = result.get("owner", "")        

        if owner == self.p_userid:
            mydevices = yield filter_mydevice(self.p_userid, add_members)
            if mydevices:
                add_devices = [{"id":x} for x in mydevices]
                yield add_groupmembers(coll, publish, groupid, add_devices, None)
                add_members = list(set(add_members) - set(mydevices))

            if not add_members:
                self.finish()
                return

            notify = {}
            notify["name"] = "mx.group.authgroup_invited"
            notify["pub_type"] = "any"
            notify["nty_type"] = "device"
            notify["msg_type"] = "other"
            notify["groupid"] = groupid
            notify["groupname"] = result.get("name", "")
            notify["userid"] = self.p_userid
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

            self.finish()
            return
        else:
            notify = {}
            notify["name"] = "mx.group.member_apply"
            notify["pub_type"] = "any"
            notify["nty_type"] = "device"
            notify["msg_type"] = "other"
            notify["groupid"] = groupid
            notify["groupname"] = result.get("name", "")
            notify["userid"] = self.p_userid
            opter_info = yield mickey.userfetcher.getcontact(self.p_userid)
            if opter_info:
                notify["username"] = opter_info.get("name", "")
                notify["usernickname"] = opter_info.get("commName", "")
            else:
                logging.error("get user failed %s" % self.p_userid)
                
            noti_members = []
            for item in add_members:
                member = {}
                member["id"] = item
                user_info = yield mickey.userfetcher.getcontact(item)
                if user_info:
                    member["name"] = user_info.get("name", "")
                    member["nickname"] = user_info.get("commName", "")

                noti_members.append(member)

            notify["members"] = noti_members
            publish.publish_one(owner, notify)
            self.finish()
            return


