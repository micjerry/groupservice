import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

from mickey.basehandler import BaseHandler

class RejectInviteHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")

        logging.info("begin to add members to group %s" % groupid)

        if not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_one({"_id":ObjectId(groupid)})

        if not result:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return

        #get the appendings
        appendings = result.get("appendings", [])        

        #get the exist ids
        exist_ids = [x.get("id", "") for x in result.get("members", [])]

        if not self.p_userid in appendings:
            logging.error("%s are not the appendings" % self.p_userid)
            self.set_status(403)
            self.finish()
            return

        new_appendings = list(filter(lambda x: x!= self.p_userid, appendings))

        #add member
        modresult = yield coll.find_and_modify({"_id":ObjectId(groupid)}, 
                                               {
                                                 "$pull":{"appendings":self.p_userid},
                                                 "$unset": {"garbage": 1}
                                               })

        if not modresult:
            logging.error("remove %s from appendings failed" % self.p_userid)
            self.set_status(500)
            self.finish()
            return


        self.finish()

