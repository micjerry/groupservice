import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
from mickey.basehandler import BaseHandler

class MarkMemberHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        userid = data.get("userid", "")
        remark = data.get("remark", "")

        logging.info("mark %s of group %s with %s" % (userid, groupid, remark))

        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.set_header("Reason-Phrase", "param error")
            self.finish()
            return
        

        result = yield coll.find_one({"_id":ObjectId(groupid)})
        if result:
            owner = result.get("owner", "")
            if owner != self.p_userid:
                logging.error("%s is not the owner" % owner)
                self.set_status(403)
                self.set_header("Reason-Phrase", "not the owner")
                self.finish()
                return

            members = result.get("members", [])
            for member in members:
                if (member.get("id", "") == userid):
                    member["remark"] = remark
                    break

            modresult = yield coll.find_and_modify(
                           {"_id": ObjectId(groupid)},
                           {"$set":
                              {
                               "members":members
                              }
                           }
                       )

            if modresult:
                self.set_status(200)
            else:
                logging.error("mark member failed")
                self.set_status(500)

        else:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            return

        self.finish()
