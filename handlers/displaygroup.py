import tornado.web
import tornado.gen
import tornado.httpclient
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
                
                # get user information
                nickname = ""
                name = ""
                contact_info = []
                c_type = "person"

                httpclient = tornado.httpclient.AsyncHTTPClient()
                url = "http://localhost:9080/cxf/security/contacts/%s" % u_id

                try:
                    response = yield httpclient.fetch(url, None, method = "GET", headers = {}, body = None)

                    if response.code != 200:
                        logging.error("get user info failed userid = %s" % u_id)
                    else:
                        res_body = {}
                        res_body = json.loads(response.body.decode("utf-8"))
                        nickname = res_body.get("commName", "")
                        contact_info = res_body.get("contactInfos", [])
                        name = res_body.get("name", "")
                        c_type = res_body.get("type", "")
                except Exception as e:
                    logging.error("invalid body received")

                u_member["nickname"] = nickname
                u_member["name"] = name
                u_member["type"] = c_type
                u_member["contactInfos"] = contact_info
                
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
