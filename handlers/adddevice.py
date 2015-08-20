import tornado.web
import tornado.gen
import json
import io
import logging

import motor

import basehandler

from bson.objectid import ObjectId

class AddDeviceHandler(basehandler.BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        coll = self.application.db.groups
        data = json.loads(self.request.body.decode("utf-8"))
        groupid = data.get("groupid", "")
        devices = data.get("devices", [])
        
        logging.info("add devices to %s" % groupid)

        if not groupid or not devices:
            logging.error("invalid request")
            self.set_status(403)
            self.finish()
            return
        
        add_devices = []
        for item in devices:
            device_id   = item.get("id", "")
            device_name = item.get("name", "")
            if device_id:
                add_devices.append({"id":device_id, "name":device_name})

        for device in add_devices:
            dev_id = device.get("id", "")
            result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$pull":{"devices":{"id":dev_id}}})
            
        add_result = yield coll.find_and_modify({"_id":ObjectId(groupid)}, {"$addToSet":{"devices":{"$each": add_devices}}})

        if add_result:
            self.set_status(200)
        else:
            logging.error("add device failed")
            self.set_status(500)

        self.finish()
