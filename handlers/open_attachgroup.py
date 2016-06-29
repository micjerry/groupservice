import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr
import mickey.redis

class OpenAttachGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("id", "")
        device = data.get("device", "")
        password = data.get("password", "")

        if not groupid:
            logging.error("attach failed without groupid")
            self.set_status(403)
            self.finish()
            return

        group = yield GroupMgrMgr.getgroup(groupid)
        
        if not group:
            self.set_status(404)
            self.finish()
            return

        result = yield group.attach_member(self.p_userid)

        if result == 200:
            #save the attch
            if device:
                kp_key = GroupMgrMgr.get_kpalive_key(device, self.p_userid, groupid)
                if kp_key:
                    mickey.redis.write_to_redis(kp_key, "OK", expire = 120)
                    
            #reload the data from db
            yield group.load()
            res_body = yield group.createDisplayResponse()
            if res_body:
                self.write(res_body)

        self.set_status(result)
        self.finish()

