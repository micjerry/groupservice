import tornado.web
import tornado.gen
import tornado.httpclient
import json
import io
import logging

import motor

from bson.objectid import ObjectId
import mickey.userfetcher
from mickey.basehandler import BaseHandler

class DisplayGroupHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        usercoll = self.application.userdb.users
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "invalid")

        logging.info("begin to display group %s" % groupid)

        result = yield coll.find_one({"_id":ObjectId(groupid)})

        if result:
            groupinfo = {}
            groupinfo["groupid"] = groupid
            rs_members = []

            for item in result.get("members", []):
                u_member = {}
                u_id = item.get("id", "")
                u_member["id"] = u_id
                u_member["remark"] = item.get("remark", "")
                u_member["realname"] = item.get("realname", "")
                
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
            groupinfo["devices"] = result.get("devices", [])
           
            groupinfo["name"] = result.get("name", "")
            groupinfo["owner"] = result.get("owner", "")
            groupinfo["vip"] = result.get("vip", "false")
            groupinfo["vipname"] = result.get("vipname", "")
            groupinfo["invite"] = result.get("invite", "free")

            self.write(groupinfo)
        else:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.write({"error":"not found"});

        self.finish()
