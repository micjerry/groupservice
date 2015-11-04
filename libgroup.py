import logging
import tornado.gen

import tornado_mysql
from mickey.mysqlcon import get_mysqlcon
from bson.objectid import ObjectId

_logger = logging.getLogger(__name__)

_filtermydevice_sql = """
  SELECT device_userID FROM deviceusermap WHERE userEntity_userID = %s AND device_userID IN %s;
"""

@tornado.gen.coroutine
def filter_mydevice(userid, members):
    conn = yield get_mysqlcon('mxsuser')
    if not conn:
        logging.error("connect to mysql failed")
        return False

    mem_list = "("
    for item in members:
        mem_list = mem_list + item + ','

    mem_list = mem_list[:-1]
    mem_list = mem_list + ")"
    try:
        cur = conn.cursor(tornado_mysql.cursors.DictCursor)
        format_sql = _filtermydevice_sql % (userid, mem_list)
        yield cur.execute(format_sql)
        rows = cur.fetchall()
        mylist = []
        for item in rows:
            mylist.append(str(item.get("device_userID", "")))

        cur.close()
        return mylist
    except Exception as e:
        logging.error("oper db failed {0}".format(e))
        return False
    finally:
        conn.close()

@tornado.gen.coroutine
def add_groupmembers(coll, publish, groupid, members, expires=None):
    if not coll or not publish or not groupid or not members:
        _logger.error("invalid parameter")
        return False

    result = None
    if not expires:    
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)},
                                            {
                                              "$addToSet":{"members":{"$each": members}},
                                              "$unset": {"garbage": 1}
                                            })
    else:
        result = yield coll.find_and_modify({"_id":ObjectId(groupid)},
                                            {
                                              "$addToSet":{"members":{"$each": members}},
                                              "$set":{"expireAt": expires},
                                              "$unset": {"garbage": 1}
                                            })

    if not result:
        _logger.error("add group error")
        return False

    notify = {}
    notify["name"] = "mx.group.group_invite"
    notify["pub_type"] = "any"
    notify["nty_type"] = "app"
    notify["msg_type"] = "other"
    notify["groupid"] = groupid
    notify["groupname"] = result.get("name", "")

    invite_receivers = [x.get("id", "") for x in members]

    publish.publish_multi(invite_receivers, notify)

    notify_mod = {}
    notify_mod["name"] = "mx.group.group_change"
    notify_mod["pub_type"] = "any"
    notify_mod["nty_type"] = "app"
    notify_mod["groupid"] = groupid
    notify_mod["action"] = "new_member"
    notify_mod["members"] = members

    old_receivers = [x.get("id", "") for x in result.get("members", [])]
    publish.publish_multi(old_receivers, notify_mod)
    return True
