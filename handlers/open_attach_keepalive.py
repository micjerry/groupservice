import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class OpenAttachKeepAliveHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("id", "")

        if not groupid:
            logging.error("keep alive failed without groupid")
            self.set_status(403)
            self.finish()
            return

        GroupMgrMgr.keepalive_attacher(groupid, self.p_userid)

        self.set_status(200)
        self.finish()

