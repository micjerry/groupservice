import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
import mickey.userfetcher
from mickey.basehandler import BaseHandler

from mickey.groups import GroupMgrMgr, MickeyGroup

from libgroup import filter_mydevice

class AuthAddMemberHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        publish = self.application.publish
        token = self.request.headers.get("Authorization", "")
        data = json.loads(self.request.body.decode("utf-8"))
        groupid      = data.get("groupid", "")
        members      = data.get("members", [])
        operasadmin  = data.get("operasadmin", "false")

        logging.info("begin to add members to group %s" % groupid)

        if not groupid or not members:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return
        
        group = yield GroupMgrMgr.getgroup(groupid)

        if not group:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return

        if group.is_realname() == False:
            return self.redirect("/group/add/members")

        #get exist members

        if operasadmin == "false" and group.has_member(self.p_userid) == False:
            logging.error("%s are not the member" % self.p_userid)
            self.set_status(403)
            self.finish()
            return

        group_members = group.get_members()

        # get members and the receivers
        add_members = list(filter(lambda x: x not in group_members, [x.get("id", "") for x in members]))

        owner = group.get_owner()
        if operasadmin == "true":
            self.p_userid = owner

        if owner == self.p_userid:
            mydevices = yield filter_mydevice(self.p_userid, add_members)
            if mydevices:
                add_devices = [{"id":x} for x in mydevices]
                yield group.add_members(add_devices)
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
            notify["groupname"] = group.get_name()
            notify["userid"] = self.p_userid
            opter_info = yield mickey.userfetcher.getcontact(self.p_userid, token)
            if opter_info:
                notify["username"] = opter_info.get("name", "")
            else:
                logging.error("get user info failed %s" % self.p_userid)
                
            adddb_members = list(filter(lambda x: x.get("id", "") in add_members, members))
            append_result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, 
                                                       {
                                                         "$addToSet":{"appendings":{"$each": adddb_members}},
                                                         "$unset": {"garbage": 1}
                                                       })
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
            notify["groupname"] = group.get_name()
            notify["userid"] = self.p_userid
            opter_info = yield mickey.userfetcher.getcontact(self.p_userid, token)
            if opter_info:
                notify["username"] = opter_info.get("name", "")
                notify["usernickname"] = opter_info.get("commName", "")
            else:
                logging.error("get user failed %s" % self.p_userid)
                
            noti_members = []
            for item in add_members:
                member = {}
                member["id"] = item
                user_info = yield mickey.userfetcher.getcontact(item, token)
                if user_info:
                    member["name"] = user_info.get("name", "")
                    member["nickname"] = user_info.get("commName", "")

                noti_members.append(member)

            notify["members"] = noti_members
            publish.publish_one(owner, notify)
            self.finish()
            return


