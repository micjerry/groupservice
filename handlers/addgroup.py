import tornado.web
import tornado.gen
import json
import io
import logging

import motor

class AddGroupHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.db.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupname = data.get("name", "")
        owner = data.get("owner", "")
        invite = data.get("invite", "free")

        logging.info("begin to create group owner = %s, owner = %s, invite = %s" % (owner, groupname, invite))

        if not groupname:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        if (invite.lower() != "free") and (invite.lower() != "admin"):
            logging.error("invalid invite type %s" % invite)
            self.set_status(403)
            self.finish()
            return
        
        members = data.get("members", [])

        groupinfo = {}
        groupinfo["name"] = groupname
        groupinfo["owner"] = owner
        groupinfo["invite"] = invite
        groupinfo["members"] = members
        
        result = yield coll.insert(groupinfo)

        if result:
            result_rt = {}
            groupid = str(result)
            result_rt["groupid"] = groupid
            result_rt["name"] = groupname
            result_rt["owner"] = owner
            result_rt["invite"] = invite
            result_rt["members"] = members

            if owner:
                yield usercoll.find_and_modify({"id":owner}, {"$push":{"groups":{"id":groupid}}})

            self.set_status(200)
            self.write(result_rt)
    
            #notify all the members
            receivers = []
            for item in members:
                receivers.append(item.get("id"))

            notify = {}
            notify["name"] = "mx.group.group_invite"
            notify["groupid"] = str(result)
            notify["groupname"] = groupname

            publish.publish_multi(receivers, notify)
            
            
        else:
            self.set_status(500)

        self.finish()
