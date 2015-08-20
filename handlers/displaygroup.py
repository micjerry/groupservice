import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

import basehandler

class DisplayGroupHandler(basehandler.BaseHandler):
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
            members = result.get("members", [])
            rs_members = []

            for item in members:
                u_member = {}
                u_id = item.get("id", "")
                u_member["id"] = u_id
                u_member["remark"] = item.get("remark", "")
                u_member["realname"] = item.get("realname", "")
                u_info = yield usercoll.find_one({"id":u_id})
                if u_info:
                    u_member["nickname"] = u_info.get("nickname", "")
                    u_member["name"] = u_info.get("name", "")
                else:
                    u_member["nickname"] = item.get("nickname", "")
                
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
