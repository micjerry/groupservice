import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class AddGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))

        (result_code, result_body) = yield GroupMgrMgr.createGroup(self.p_userid, data)

        self.set_status(result_code)
        if result_body:
            self.write(result_body)

        self.finish()

