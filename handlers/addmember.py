import tornado.web
import tornado.gen
import json
import io
import logging

from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr, MickeyGroup

class AddMemberHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        members = data.get("members", [])

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

        if group.is_realname() == True:
            return self.redirect("/group/authadd/members")

        #check operate right
        if group.has_member(self.p_userid) == False:
            logging.error("%s are not the member" % self.p_userid)
            self.set_status(403)
            self.finish()
            return

        #add members
        add_rst = yield group.add_members([x.get("id", "") for x in members])

        self.set_status(add_rst)
        self.finish()
