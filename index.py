#!/usr/bin/env python

"""
Password changer.

Usage:
  index.py [-s SERVER -H DBHOST -p port -P DBPORT]
  index.py [-h | --help]
  index.py --version

Options:
  -h --help                 Show this screen.
  -v --version              Show version.
  -s --server SERVER        Web server host [default: localhost].
  -p --port PORT            Web server port [default: 8001].
  -H --dbhost DBHOST        Database host [default: localhost].
  -P --dbport DBPORT        Database port [default: 27017].
"""

import os
base_dir = os.path.dirname(os.path.abspath(__file__))
activate_this = os.path.join(base_dir, 'venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import spwd
import crypt
import random
import string
from bottle import run, route, abort, request, template, app
from pymongo import MongoClient, errors as e
from docopt import docopt


class PasswordHandler(object):
    def __init__(self,
                 username=None,
                 current_passwd=None,
                 passwd=None,
                 **kwargs):
        self.username = username
        self.current_passwd = current_passwd
        self.passwd = passwd
        self.shadow_hashed = None
        self.current_hashed = None
        self.salt = None

    def check_data(self):
        print "[DEBUG] Entering check_data()"
        print self.username, self.passwd, self.current_passwd
        if not self.username:
            abort(400, "Name required")
        else:
            self.getshadow(True)
        if not self.passwd:
            abort(400, "Password required")
        if not self.current_passwd:
            abort(400, "Current password required")
        print "[DEBUG] Exiting check_data()"

    def getshadow(self, chk_flag=None):
        try:
            # print "[DEBUG] args[4] = %s" % kwargs[4]
            self.shadow_hashed = spwd.getspnam(self.username)[1]
            if chk_flag is None:
                print "[DEBUG] %s" % self.shadow_hashed
                return self.shadow_hashed
            else:
                print "[DEBUG] User %s exist" % self.username
        except KeyError:
            print "[DEBUG] User %s doesn't exist" % self.username
            abort(400, "User %s doesn't exist" % self.username)

    def getsalt(self):
        print "[DEBUG] shadow_hashed = %s" % self.shadow_hashed
        self.salt = self.shadow_hashed.split("$")[2]
        return self.salt

    def compare(self):
        self.getshadow()
        self.getsalt()
        self.current_hashed = hashing(self.current_passwd, self.salt)
        print "[DEBUG] current_hashed = %s" % self.current_hashed
        print "[DEBUG] shadow_hashed = %s" % self.shadow_hashed
        if self.shadow_hashed == self.current_hashed:
            return True
        else:
            abort(400, "Current password are incorrect")


class DatabaseHandler(object):
    def __init__(self,
                 username=None,
                 current_passwd=None,
                 passwd=None,
                 **kwargs):
        self.phandler = PasswordHandler(username, current_passwd, passwd)
        self.connection = None
        self.db = None
        self.userdata = None

    def connect(self):
        try:
            # connection = MongoClient(ServerSelectionTimeoutMS=1)
            self.connection = MongoClient(
                host=args['--dbhost'],
                port=int(args['--dbport']),
                ServerSelectionTimeoutMS=1
            )
            self.connection.server_info()
            # return connection
        # except e.ServerSelectionTimeoutError, err:
        except Exception as err:
            print "[DEBUG] DB unavailable: %s" % err
            abort(500, "Could not establish connection to database")

    # def store(username, passwd):
    def store(self):
        # connection = self.connect()
        self.connect()
        try:
            # TODO: store or replace. check the id/username
            self.db = self.connection.anima.users
            # shadow_hashed = self.PasswordHandler.getshadow()
            self.phandler.getshadow()
            self.passwd = hashing(self.phandler.username, self.phandler.passwd)
            self.userdata = {
                'username': self.phandler.username,
                'previous_passwd': self.phandler.shadow_hashed,
                'current_passwd': self.passwd
            }
            self.db.insert_one(self.userdata)
        # except e.OperationFailure, err:
        except Exception as err:
            print "[DEBUG] Operation failed: %s" % err
            abort(500, "Operation failed: %s" % err)


def change_passwd():
    ''' Replace shadow_file.example with the actual shadow file'''
    with open("shadow_file.example", 'r+') as file:
        lines = file.readlines()
        for line in lines:
            # TODO: SEARCH AND REPLACE HERE
            print line


def hashing(passwd, salt=None):
    if not salt:
        random_salt = ([random.choice(string.ascii_letters +
                                      string.digits) for _ in range(16)])
        random_salt = "$6$" + ''.join(random_salt) + "$"
        passwd = crypt.crypt(passwd, str(random_salt))
    else:
        passwd = crypt.crypt(passwd, '$6$' + salt + "$")
    return passwd


@route('/')
def index():
    return template('index.html')


@route('/modify_user', method='POST')
def modify_user():
    username = request.forms.get('username')
    current_passwd = request.forms.get('current_passwd')
    passwd = request.forms.get('passwd')

    print "[DEBUG] Instantiate class PasswordHandler"
    phandler = PasswordHandler(**locals())
    dbhandler = DatabaseHandler(**locals())

    phandler.check_data()

    print "[DEBUG] Compare password"
    if phandler.compare():
        # passwd = hashing(passwd)
        dbhandler.store()
        # Return hashed password, just for debug. To be remove.
        return """<p>User: %s<br>Pass: %s</p>""" % (username, dbhandler.passwd)


if __name__ == "__main__":
    args = docopt(__doc__, version="FIXME")

    app = app()

    run(host=args['--server'],
        port=int(args['--port']),
        app=app,
        reloader=True,
        debug=True)
