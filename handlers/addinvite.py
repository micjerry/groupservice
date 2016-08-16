import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

from mickey.basehandler import BaseHandler
import mickey.users
import mickey.groups
import mickey.smsinter
import mickey.userfetcher
from mickey.commonconf import MAX_MEMBERS

class AddInviteHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        token = self.request.headers.get("Authorization", "")
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        invitees = data.get("invitees", [])
        admin_name = None

        logging.info("begin to add invitees to group %s" % groupid)

        if not groupid or not invitees:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return

        group = yield coll.find_one({"_id":ObjectId(groupid)})
        if not group:
            logging.error("group %s does not exist" % groupid)
            self.set_status(404)
            self.finish()
            return
        else:
            owner = group.get("owner", "")
            if self.p_userid != owner or group.get("invite", "free") != "admin":
                logging.error("import members was forbidden %s" % groupid)
                self.set_status(403)
                self.finish()
                return

            db_invitees = [x.get("number", "") for x in group.get("invitees", [])]
            invitee_numbers = [x.get("number", "") for x in invitees]
            
            all_invitees = list(set(db_invitees + invitee_numbers))
            members = group.get("members", [])
            if len(members) + len(all_invitees) > MAX_MEMBERS:
                logging.error("too many invitees  %s" % groupid)
                self.set_status(403)
                self.finish()
                return

            if not mickey.groups.charge_sms(self.p_userid, len(invitees)):
                logging.error("too many sms %s" % groupid)
                self.set_status(403)
                self.finish()
                return

        invitee_numbers = [x.get("number", "") for x in invitees]
        provisioned_users    = []
        unprovisioned_users  = []

        for item in invitees:
            load_number = item.get("number", "")
            result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$pull":{"invitees":{"number":load_number}}})
            userid = yield mickey.users.get_userwithphone(load_number)
            if userid:
                remark = item.get("remark", "")
                provisioned_users.append({"id":str(userid), "remark":remark})
            else:
                unprovisioned_users.append(load_number)
        
        add_result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$addToSet":{"invitees":{"$each": invitees}}})

        if add_result:
            if provisioned_users:
                mickey.groups.addmember(token, groupid, provisioned_users)

            opter_info = yield mickey.userfetcher.getcontact(self.p_userid, token)
            if opter_info:
                admin_name = opter_info.get("name", "")

            group_name = group.get("name", "")

            for item in unprovisioned_users:
                yield mickey.users.handle_preinvite(item, groupid)

                if admin_name and group_name:
                    if item[0:4] == "0086":
                        phone_number = item[4:]
                        mickey.smsinter.sendSMS(91550640, phone_number, admin = admin_name, group = group_name)
                    else:
                        mickey.smsinter.sendSMS(91550640, item, admin = admin_name, group = group_name)

            self.set_status(200)
        else:
            logging.error("add invitees failed")
            self.set_status(500)

        self.finish()
