import os
import sys

sys.path.append('/opt/webapps/libs')

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.options
import logging
import logging.handlers

import motor

import mickey.publish
import mickey.commonconf
from mickey.daemon import Daemon
import mickey.logutil

from handlers.listgroup import ListGroupHandler
from handlers.displaygroup import DisplayGroupHandler
from handlers.addgroup import AddGroupHandler
from handlers.removegroup import RemoveGroupHandler
from handlers.user_addgroup import UserAddGroupHandler
from handlers.user_removegroup import UserRemoveGroupHandler
from handlers.modgroup import ModGroupHandler
from handlers.addmember import AddMemberHandler
from handlers.removemember import RemoveMemberHandler
from handlers.markmember import MarkMemberHandler
from handlers.addinvite import AddInviteHandler
from handlers.realmember import RealMemberHandler
from handlers.adddevice import AddDeviceHandler
from handlers.removedevice import RemoveDeviceHandler
from handlers.markdevice import MarkDeviceHandler
from handlers.authaddmember import AuthAddMemberHandler
from handlers.acceptmember import AcceptMemberHandler
from handlers.acceptinvite import AcceptInviteHandler

from tornado.options import define, options
define("port", default=8100, help="run on the given port", type=int)
define("cmd", default="run", help="Command")
define("conf", default="/etc/mx_apps/app_group/app_group_is1.conf", help="Server config")
define("pidfile", default="/var/run/app_group_is1.pid", help="Pid file")
define("logfile", default="/var/log/app_group_is1", help="Log file")

class Application(tornado.web.Application):
    def __init__(self):
        handlers=[(r"/group/user/list/groups", ListGroupHandler),
                  (r"/group/display/detail", DisplayGroupHandler),
                  (r"/group/create/group", AddGroupHandler),
                  (r"/group/dismiss/group", RemoveGroupHandler),
                  (r"/group/user/add/group", UserAddGroupHandler),
                  (r"/group/user/remove/group", UserRemoveGroupHandler),
                  (r"/group/mod/group", ModGroupHandler),
                  (r"/group/add/members", AddMemberHandler),
                  (r"/group/remove/member", RemoveMemberHandler),
                  (r"/group/mod/member/remark", MarkMemberHandler),
                  (r"/group/add/invitees", AddInviteHandler),
                  (r"/group/mod/realname", RealMemberHandler),
                  (r"/group/add/device", AddDeviceHandler),
                  (r"/group/remove/device", RemoveDeviceHandler),
                  (r"/group/mod/device/name", MarkDeviceHandler),
                  (r"/group/authadd/members", AuthAddMemberHandler),
                  (r"/group/accept/invitation", AcceptInviteHandler),
                  (r"/group/approve/newmember", AcceptMemberHandler)
                 ]
        self.db = motor.MotorClient(options.mongo_url).group
        self.userdb = motor.MotorClient(options.mongo_url).contact
        self.publish = mickey.publish
        tornado.web.Application.__init__(self, handlers, debug=True)
 

class MickeyDamon(Daemon):
    def run(self):
        mickey.logutil.setuplog(options.logfile)
        http_server = tornado.httpserver.HTTPServer(Application())
        http_server.listen(options.port, options.local_server)
        tornado.ioloop.IOLoop.instance().start()

    def errorcmd(self):
        print("unkown command")
 
def micmain():
    tornado.options.parse_command_line()
    tornado.options.parse_config_file(options.conf)

    miceydamon = MickeyDamon(options.pidfile)
    handler = {}
    handler["start"] = miceydamon.start
    handler["stop"] = miceydamon.stop
    handler["restart"] = miceydamon.restart
    handler["run"] = miceydamon.run

    return handler.get(options.cmd, miceydamon.errorcmd)()

if __name__ == "__main__":
    micmain()
