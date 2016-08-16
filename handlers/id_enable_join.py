import tornado.web
import tornado.gen
import json
import logging

from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class IdEnableJoinHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")

        logging.info("begin to enable id share id = %s" % (groupid))

        if not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        group = yield GroupMgrMgr.getgroup(groupid)

        if not group:
            logging.error("group not found")
            self.set_status(404)
            self.finish()
            return

        owner = group.get_owner()
        if owner != self.p_userid:
            logging.error("just owner was allowd to share the group")
            self.set_status(403)
            self.finish()
            return

        if group.is_realname() == True:
            logging.error("real group is forbidden to share")
            self.set_status(403)
            self.finish()
            return

        shareid = yield group.enable_id_join()

        if shareid:
            self.set_status(200)

            body = {"shareid": shareid}
            self.write(body)
        else:
            logging.error("share group failed")
            self.set_status(500)

        self.finish()
