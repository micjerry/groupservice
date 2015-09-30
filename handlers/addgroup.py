import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from mickey.basehandler import BaseHandler

_garbage = ""
for i in range(50):
    _garbage += "this only to occupy the space for user, avoid mongo to  move the data when it get bigger. "

class AddGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupname = data.get("name", "")
        owner = data.get("owner", "")
        invite = data.get("invite", "free")

        logging.info("begin to create group owner = %s, owner = %s, invite = %s" % (owner, groupname, invite))

        if self.p_userid != owner:
            logging.error("forbiden you can not create group for other user")
            self.set_status(403)
            self.finish()
            return

        if (invite.lower() != "free") and (invite.lower() != "admin"):
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
            member_ids.remove(self.p_userid)
            groupinfo["appendings"] = member_ids
            groupinfo["members"] = [{"id":self.p_userid}]
        else:
            groupinfo["members"] = members

        groupinfo["garbage"] = _garbage
        
        result = yield coll.insert(groupinfo)

        if result:
            result_rt = {}
            groupid = str(result)
            result_rt["members"] = groupinfo.get("members", [])
            result_rt["appendings"] = groupinfo.get("appendings", [])
            result_rt["groupid"] = groupid
            result_rt["name"] = groupname
            result_rt["owner"] = owner
            result_rt["invite"] = invite

            if owner:
                yield usercoll.find_and_modify({"id":owner}, 
                                               {
                                                 "$push":{"groups":{"id":groupid}},
                                                 "$unset": {"garbage": 1}
                                               })

            self.set_status(200)
            self.write(result_rt)
    
            #notify all the members
            receivers = list(filter(lambda x: x != self.p_userid, [x.get("id", "") for x in members]))
            notify = {}
            if invite == "admin":
                notify["name"] = "mx.group.authgroup_invited"
            else:
                notify["name"] = "mx.group.group_invite"

            notify["pub_type"] = "any"
            notify["nty_type"] = "device"
            notify["msg_type"] = "other"
            notify["groupname"] = groupname
            notify["groupid"] = groupid

            publish.publish_multi(receivers, notify)
            
        else:
            self.set_status(500)

        self.finish()
