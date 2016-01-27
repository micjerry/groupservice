import tornado.web
import tornado.gen
import json
import io
import logging
import datetime

import motor

from mickey.basehandler import BaseHandler
import mickey.tp
import mickey.userfetcher
import mickey.commonconf
import mickey.maps

from mickey.commonconf import MAX_REALGROUPS, MAX_MEMBERS
from libgroup import filter_mydevice, getreal_groups

_garbage = ""
for i in range(50):
    _garbage += "this only to occupy the space for user, avoid mongo to  move the data when it get bigger. "

class AddGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        token = self.request.headers.get("Authorization", "")
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupname = data.get("name", "")
        owner = data.get("owner", self.p_userid)
        invite = data.get("invite", "free").lower()

        logging.info("begin to create group owner = %s, owner = %s, invite = %s" % (owner, groupname, invite))
        logging.info("data = %r" % data)

        if self.p_userid != owner:
            logging.error("forbiden you can not create group for other user")
            self.set_status(403)
            self.finish()
            return

        if (invite != "free") and (invite != "admin"):
            logging.error("invalid invite type %s" % invite)
            self.set_status(403)
            self.finish()
            return
        
        members = data.get("members", [])
        member_ids = [x.get("id", "") for x in members]
        if self.p_userid not in member_ids:
            members.append({"id" : self.p_userid})

        groupinfo = {}
        groupinfo["name"] = groupname
        groupinfo["owner"] = owner
        groupinfo["invite"] = invite

        if invite == "admin":
            realgroups = yield getreal_groups(self.p_userid)
            if ((realgroups + 1) > MAX_REALGROUPS) or (len(members) > MAX_REALGROUPS):
                self.set_status(413)
                self.finish()
                return
            
            canadd_members = [self.p_userid]
            my_devices =  yield filter_mydevice(self.p_userid, member_ids)
            if my_devices:
                for item in my_devices:
                    canadd_members.append(item)

            groupinfo["appendings"] = list(filter(lambda x: x.get("id", "") not in canadd_members, members))
            groupinfo["members"] = list(filter(lambda x: x.get("id", "") in canadd_members, members))
        else:
            groupinfo["members"] = members
            groupinfo['expireAt'] = datetime.datetime.utcnow() + datetime.timedelta(days = mickey.commonconf.conf_expire_time)

        groupinfo["garbage"] = _garbage

        result = yield coll.insert(groupinfo)

        if result:
            result_rt = {}
            groupid = str(result)
            logging.info("create group success %s" % groupid)

            #create ytx group for chat
            mickey.tp.addgroup(groupid, self.p_userid, "")

            result_rt["members"] = groupinfo.get("members", [])
            result_rt["appendings"] = groupinfo.get("appendings", [])
            result_rt["groupid"] = groupid
            result_rt["name"] = groupname
            result_rt["owner"] = owner
            result_rt["invite"] = invite

            added_members = [x.get("id", "") for x in groupinfo.get("members", [])]
            if invite == "admin":
                for item in added_members:
                    yield usercoll.find_and_modify({"id":item}, 
                                                   {
                                                     "$push":{"groups":{"id": groupid}, "realgroups":groupid},
                                                     "$unset": {"garbage": 1}
                                                   })

            self.set_status(200)
            self.write(result_rt)
    
            #notify all the members
            add_receivers = list(filter(lambda x: x != self.p_userid, added_members))
            notify = {}
            notify["name"] = "mx.group.group_invite"
            notify["pub_type"] = "any"
            notify["nty_type"] = "app"
            notify["msg_type"] = "other"
            notify["groupname"] = groupname
            notify["groupid"] = groupid

            publish.publish_multi(add_receivers, notify)

            #notify all the invited members
            if invite == "admin":
                invite_receivers = [x.get("id", "") for x in groupinfo.get("appendings", [])]
                notify["name"] = "mx.group.authgroup_invited"
                notify["userid"] = self.p_userid
                opter_info = yield mickey.userfetcher.getcontact(self.p_userid, token)
                if opter_info:
                    notify["username"] = opter_info.get("name", "")
                publish.publish_multi(invite_receivers, notify)

            # add maps
            if invite == "admin":
                mickey.maps.addgroup(groupid, self.p_userid, [], 1)
            else:
                add_receivers.append(self.p_userid)
                mickey.maps.addgroup(groupid, self.p_userid, add_receivers)

        else:
            self.set_status(500)

        self.finish()
