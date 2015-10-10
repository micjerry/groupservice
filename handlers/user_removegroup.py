import tornado.web
import tornado.gen
import json
import io
import logging
import datetime

import motor
from bson.objectid import ObjectId

from mickey.basehandler import BaseHandler
import mickey.commonconf

class UserRemoveGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.userdb.users
        groupcoll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        userid = data.get("userid", "")
        groupid = data.get("groupid", "")

        logging.info("user %s remove group %s" % (userid, groupid))

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
                                              "$pull":{"groups":{"id":groupid}}
                                            })

        grp_result = yield groupcoll.find_and_modify({"_id":ObjectId(groupid)},
                                                     {
                                                       "$pull":{"savers":self.p_userid}
                                                     },
                                                     new = True)
        #set expire
        if grp_result:
            if not grp_result.get('savers', []) and grp_result.get('invite', 'free') == 'free':
                new_expiredate = datetime.datetime.utcnow() + datetime.timedelta(days = mickey.commonconf.conf_expire_time)
                yield groupcoll.find_and_modify({"_id":ObjectId(groupid)},
                                                {
                                                  "$set":{"expireAt": new_expiredate}
                                                })

        if result:
            self.set_status(200)
        else:
            logging.error("user remove group failed")
            self.set_status(500)

        self.finish()
