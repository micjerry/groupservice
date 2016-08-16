import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr, MickeyGroup

class IdJoinGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        sharecoll = self.application.db.shareids
        shareid = data.get("shareid", "")

        logging.info("begin to add member with share id %s" % shareid)

        if not shareid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        shareinfo = yield sharecoll.find_one({"id": shareid})

        if not shareinfo:
            logging.error("share id not found")
            self.set_status(404)
            self.finish()
            return

        groupid = shareinfo.get("groupid", "")
        
        group = yield GroupMgrMgr.getgroup(groupid)

        if not group:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return

        if group.is_realname() == True:
            self.set_status(403)
            self.finish()
            return

        if group.get_join_id() != shareid:
            logging.error("shareid not macth")
            self.set_status(404)
            self.finish()
            return

        #add members
        add_rst = yield group.add_members([self.p_userid])

        if add_rst == 200:
            new_group = yield GroupMgrMgr.getgroup(groupid)
            groupinfo = yield new_group.createDisplayResponse()
            self.write(groupinfo)

        self.set_status(add_rst)
        self.finish()
