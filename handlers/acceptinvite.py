import tornado.web
import tornado.gen
import json
import io
import logging

from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr, MickeyGroup

class AcceptInviteHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")

        logging.info("begin to add members to group %s" % groupid)

        if not groupid:
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

        rst_code = yield group.add_realmember(self.p_userid)
        self.set_status(rst_code)
        self.finish()

