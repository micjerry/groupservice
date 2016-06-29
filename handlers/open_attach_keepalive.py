import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr
import mickey.redis

class OpenAttachKeepAliveHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("id", "")
        device = data.get("device", "")

        if not groupid:
            logging.error("keep alive failed without groupid")
            self.set_status(403)
            self.finish()
            return

        if device:
            kp_key = GroupMgrMgr.get_kpalive_key(device, self.p_userid, groupid)
            mickey.redis.write_to_redis(kp_key, "OK", expire = 120)
            

        GroupMgrMgr.keepalive_attacher(groupid, self.p_userid)

        self.set_status(200)
        self.finish()

