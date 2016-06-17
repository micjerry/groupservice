import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class OpenQueryGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        open_id = data.get("open_id", "")

        if not open_id:
            logging.error("query failed without openid")
            self.set_status(403)
            self.finish()
            return

        group = yield GroupMgrMgr.searchgroup(open_id)
        
        if not group:
            self.set_status(404)
            self.finish()
            return

        groupinfo = {}
        groupinfo["id"] = group.get_id()
        groupinfo["name"] = group.get_name()
        groupinfo["invite"] = group.get_invite()
        groupinfo["tp_chatid"] = group.get_chatid()
        groupinfo["open_id"] = group.get_openid()


        self.write(groupinfo)
        self.finish()

