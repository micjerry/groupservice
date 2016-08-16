import tornado.web
import tornado.gen
import json
import logging

from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class IdDisableJoinHandler(BaseHandler):
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
            self.set_status(403)
            self.finish()
            return

        yield group.disable_id_join()

        self.set_status(200)
        self.finish()
