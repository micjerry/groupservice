import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId
from mickey.basehandler import BaseHandler
import mickey.tp
import mickey.maps
import mickey.userfetcher

class RemoveMemberHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        publish = self.application.publish
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        userid = data.get("userid", "")

        logging.info("begin to remove member %s from group %s" % (userid, groupid))

        if not userid or not groupid:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        group = yield coll.find_one({"_id":ObjectId(groupid)})
        groupname = ""
        receivers = []

        if group:
            groupname = group.get("name", "")
            owner     = group.get("owner", "")

            if self.p_userid != owner and self.p_userid != userid:
                logging.error("no right")
                self.set_status(403)
                self.finish()
                return

            # the owner can not quit
            if self.p_userid == owner and self.p_userid == userid:
                logging.error("the owner cannot quit, you can dismiss")
                self.set_status(403)
                self.finish()
                return

            receivers = [x.get("id", "") for x in group.get("members", "")]
      
        else:
            self.set_status(404)
            self.finish()
            return
        
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, 
                                            {
                                              "$pull":{"members":{"id":userid}},
                                              "$unset": {"garbage": 1}
                                            })

        # remove group from the user's group list
        yield usercoll.find_and_modify({"id":userid}, 
                                       {
                                         "$pull":{"groups":{"id":groupid}},
                                         "$pull":{"realgroups":groupid},
                                         "$unset": {"garbage": 1}
                                       })

        #remove users from conference
        mickey.userfetcher.remove_users_from_conf(groupid, [userid])

        if result:
            self.set_status(200)

            mickey.tp.removegroupmember(groupid, userid, "")

            #send notify to deleted user
            notify = {}
            notify["name"] = "mx.group.group_kick"
            notify["pub_type"] = "any"
            notify["nty_type"] = "app"
            notify["groupid"] = groupid
            notify["groupname"] = groupname
            notify["userid"] = userid
            if self.p_userid == userid:
                notify["quit"] = "true"
                if userid in receivers:
                    receivers.remove(userid)
            else:
                notify["quit"] = "false"


            publish.publish_multi(receivers, notify)

            #notify self
            if self.p_userid == userid:
                self_notify = {
                "name":"mx.group.self_group_quit",
                "groupid":groupid,
                "pub_type":"any",
                "nty_type":"app"
                }

                publish.publish_one(userid, self_notify)

            #remove maps
            mickey.maps.removemembers(groupid, [userid])
        else:
            logging.error("remove member failed groupid = %s, member = %s" % (groupid, userid))
            self.set_status(500)

        self.finish()
