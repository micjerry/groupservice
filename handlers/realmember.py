import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class RealMemberHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        userid = data.get("userid", "")
        realname = data.get("realname", "false")

        logging.info("begin to realname user = %s, realname = %s" % (userid, realname))

        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        if not realname == "false" and not realname == "true":
            logging.error("invalid realname %s" % realname)
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_one({"_id":ObjectId(groupid)})
        if result:
            members = result.get("members", [])
            for member in members:
                if (member.get("id", "") == userid):
                    member["realname"] = realname
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
                logging.error("real member failed")
                self.set_status(500)

        else:
            logging.error("group %s does not exist" % groupid)
            self.se_status(404)
            return

        self.finish()
