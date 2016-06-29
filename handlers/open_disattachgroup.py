import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr
import mickey.redis

class OpenDisAttachGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("id", "")
        device = data.get("device", "")

        if not groupid:
            logging.error("disattach failed without groupid")
            self.set_status(403)
            self.finish()
            return

        group = yield GroupMgrMgr.getgroup(groupid)
        
        if not group:
            self.set_status(404)
            self.finish()
            return

        #handle pc and app
        if device:
            other_device = GroupMgrMgr.get_other_device(device)

            self.removekey(device, self.p_userid, groupid)
            
            if self.isotherexist(other_device, self.p_userid, groupid) == True:
                self.set_status(200)
                self.finish()
                return

            

        result = yield group.disattach_member(self.p_userid)

        self.set_status(result)
        self.finish()

    def isotherexist(self, device, userid, groupid):
        kp_key = GroupMgrMgr.get_kpalive_key(device, userid, groupid)
        if kp_key:
            redis_key = mickey.redis.read_from_redis(kp_key)
            if redis_key:
                return True

        return False

    def removekey(self, device, userid, groupid):
        kp_key = GroupMgrMgr.get_kpalive_key(device, userid, groupid)
        if kp_key:
            mickey.redis.remove_from_redis(kp_key)
