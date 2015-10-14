import tornado.web
import tornado.gen
import tornado.httpclient
import json
import io
import logging
import datetime

import motor

from bson.objectid import ObjectId
import mickey.userfetcher
from mickey.basehandler import BaseHandler
import mickey.commonconf

class DisplayGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        chatcoll = self.application.db.chats
        usercoll = self.application.userdb.users
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", None)
        chatid = data.get("chatid", None)

        if not groupid and not chatid:
            logging.error("invalid parameter")
            self.set_status(403)
            self.finish()
            return

        logging.info("begin to display group %s" % groupid)

        if not groupid and chatid:
            print(chatid)
            chat = yield chatcoll.find_one({"id":chatid})
            if not chat:
                self.set_status(404)
                self.finish()
                return

            print(chat)
            groupid = chat.get('gid', '')
            print(groupid)

        result = yield coll.find_one({"_id":ObjectId(groupid)})

        if result:
            #set new expire
            expire_set = result.get('expireAt', None)
            if expire_set:
                new_expiredate = datetime.datetime.utcnow() + datetime.timedelta(days = mickey.commonconf.conf_expire_time)
                modresult = yield coll.find_and_modify({"_id":ObjectId(groupid)},
                                                       {
                                                         "$set":{"expireAt": new_expiredate},
                                                         "$unset": {"garbage": 1}
                                                       })

            groupinfo = {}
            groupinfo["groupid"] = groupid
            rs_members = []

            for item in result.get("members", []):
                u_member = {}
                u_id = item.get("id", "")
                u_member["id"] = u_id
                u_member["remark"] = item.get("remark", "")
                
                # get user information
                c_info = yield mickey.userfetcher.getcontact(u_id)

                if not c_info:
                    logging.error("get user info failed %s" % u_id)
                    continue

                u_member["nickname"] = c_info.get("commName", "")
                u_member["name"] = c_info.get("name", "")
                u_member["type"] = c_info.get("type", "PERSON")
                u_member["contactInfos"] = c_info.get("contactInfos", [])
                
                rs_members.append(u_member)

            groupinfo["members"] = rs_members 
            groupinfo["invitees"] = result.get("invitees", [])
           
            groupinfo["name"] = result.get("name", "")
            groupinfo["owner"] = result.get("owner", "")
            groupinfo["vip"] = result.get("vip", "false")
            groupinfo["vipname"] = result.get("vipname", "")
            groupinfo["invite"] = result.get("invite", "free")
            groupinfo["chatid"] = result.get("chatid", "")

            self.write(groupinfo)
        else:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.write({"error":"not found"});

        self.finish()
