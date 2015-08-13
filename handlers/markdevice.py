import tornado.web
import tornado.gen
import json
import io
import logging

import motor

from bson.objectid import ObjectId

class MarkDeviceHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        deviceid = data.get("deviceid", "")
        name = data.get("name", "")

        logging.info("begin to mark device %s of group %s with name %s" % (deviceid, groupid, name))

        if not deviceid or not groupid or not name:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return
        
        result = yield coll.find_one({"_id":ObjectId(groupid)})
        if result:
            devices = result.get("devices", [])
            for device in devices:
                if (device.get("id", "") == deviceid):
                    device["name"] = name
                    break

            modresult = yield coll.find_and_modify(
                           {"_id": ObjectId(groupid)},
                           {"$set":
                              {
                               "devices":devices
                              }
                           }
                       )

            if modresult:
                self.set_status(200)
            else:
                logging.error("mark device failed")
                self.set_status(500)

        else:
            logging.error("group %s does not exist" % groupid)
            self.se_status(404)
            return

        self.finish()
