import tornado.web
import tornado.gen
import tornado.httpclient
import json
import io
import logging

import motor

from mickey.basehandler import BaseHandler
from mickey.groups import GroupMgrMgr

class DisplayGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        chatcoll = self.application.db.tbchats
        sharecoll = self.application.db.shareids
        groupid = data.get("groupid", None)
        chatid = data.get("chatid", None)
        shareid = data.get("shareid", None)

        if not groupid and not chatid and not shareid:
            logging.error("invalid parameter")
            self.set_status(403)
            self.finish()
            return

        logging.info("begin to display group %s" % groupid)

        if not groupid and chatid:
            chat = yield chatcoll.find_one({"id":chatid})
            if not chat:
                self.set_status(404)
                self.finish()
                return

            groupid = chat.get('gid', '')

        if not groupid and shareid:
            shareinfo = yield sharecoll.find_one({"id": shareid})
            if not shareinfo:
                self.set_status(404)
                self.finish()
                return

            groupid = shareinfo.get("groupid", "")

        group = yield GroupMgrMgr.getgroup(groupid)

        if group:
            groupinfo = yield group.createDisplayResponse()
            if groupinfo:
                self.write(groupinfo)
            else:
                self.set_status(404)
                self.write({"error":"not found"});
        else:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.write({"error":"not found"});

        self.finish()
