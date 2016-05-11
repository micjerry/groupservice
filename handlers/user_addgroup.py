import tornado.web
import tornado.gen
import json
import io
import logging

from bson.objectid import ObjectId

import motor
from mickey.basehandler import BaseHandler

class UserAddGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.userdb.users
        groupcoll = self.application.db.groups
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        userid = data.get("userid", "")
        groupid = data.get("groupid", "")

        logging.info("user %s begin to add group %s" % (userid, groupid))
        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        if self.p_userid != userid:
            logging.error("no right")
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_and_modify({"id":userid}, 
                                            {
                                              "$addToSet":{"groups":{"id":groupid}},
                                              "$unset": {"garbage": 1}
                                            })

        #update group savers, if someone save this group, set it not expire
        grp_result = yield groupcoll.find_and_modify({"_id":ObjectId(groupid)},
                                                {
                                                  "$addToSet":{"savers":self.p_userid},
                                                  "$unset": {"garbage": 1, "expireAt": 1}
                                                })
        if result:
            self.set_status(200)
            #notify user self
            notify = {
             "name":"mx.group.self_group_added",
             "groupid":groupid
            }
            
            publish.publish_one(userid, notify)
        else:
            logging.error("user add group failed")
            self.set_status(500)

        self.finish()
