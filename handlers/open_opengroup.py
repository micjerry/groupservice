import tornado.web
import tornado.gen
import json
import logging


from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class OpenOpenGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("id", "")
        password = data.get("password", None)

        if not groupid:
            logging.error("open failed without groupid")
            self.set_status(403)
            self.finish()
            return

        group = yield GroupMgrMgr.getgroup(groupid)
        
        if not group:
            self.set_status(404)
            self.finish()
            return

        if self.p_userid != group.get_owner():
            logging.error("%s is not the owner of %s" % (self.p_userid, groupid))
            self.set_status(403)
            self.finish()
            return

        (result, open_id) = yield group.open(password)

        if result == 200:
            self.write({"open_id":open_id})

        self.set_status(result)
        self.finish()

