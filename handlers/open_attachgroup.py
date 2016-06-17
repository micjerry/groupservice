import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class OpenAttachGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        open_id = data.get("open_id", "")
        password = data.get("password", "")

        if not open_id:
            logging.error("attach failed without openid")
            self.set_status(403)
            self.finish()
            return

        group = yield GroupMgrMgr.searchgroup(open_id)
        
        if not group:
            self.set_status(404)
            self.finish()
            return

        result = yield group.attach_member(self.p_userid)

        if result == 200:
            #reload the data from db
            yield group.load()
            res_body = yield group.createDisplayResponse()
            if res_body:
                self.write(res_body)

        self.set_status(result)
        self.finish()

