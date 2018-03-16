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

    '''
    previous_passwd : this is current password
    new_passwd      : this is new password
    '''

    def __init__(self,
                 username=None,
                 previous_passwd=None,
                 new_passwd=None,
                 **kwargs):
        self.username = username
        self.previous_passwd = previous_passwd
        self.new_passwd = new_passwd
        self.shadow_hashed = None
        self.previous_hashed = None
        self.salt = None

    def check_data(self):
        print "[DEBUG] Entering check_data()"
        print self.username, self.previous_passwd, self.new_passwd

        if not self.previous_passwd:
            abort(400, "Current password required")

        if not self.username:
            abort(400, "Name required")
        else:
            self.getshadow(True)

        if not self.new_passwd:
            abort(400, "Password required")

        print "[DEBUG] Exiting check_data()"

    def getshadow(self, chk_flag=None):
        try:
            # print "[DEBUG] args[4] = %s" % kwargs[4]
            self.shadow_hashed = spwd.getspnam(self.username)[1]
            print self.shadow_hashed
            if chk_flag is None:
                print "[DEBUG] %s" % self.shadow_hashed
            else:
                print "[DEBUG] User %s exist" % self.username
            return self.shadow_hashed
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
        self.previous_hashed = hashing(self.previous_passwd, self.salt)
        print "[DEBUG] previous_hashed = %s" % self.previous_hashed
        print "[DEBUG] shadow_hashed = %s" % self.shadow_hashed
        if self.shadow_hashed == self.previous_hashed:
            return True
        else:
            abort(400, "Current password are incorrect")


class DatabaseHandler(object):

    '''
    previous_passwd : this is current password
    new_passwd      : this is new password
    '''

    def __init__(self,
                 username=None,
                 previous_passwd=None,
                 new_passwd=None,
                 **kwargs):
        self.phandler = PasswordHandler(username, previous_passwd, new_passwd)
        self.previous_hashed = self.phandler.getshadow()
        self.previous_salt = self.phandler.getsalt()

        self.username = username
        self.new_passwd = new_passwd
        self.new_hashed = None
        self.connection = None
        self.db = None
        self.userdata = None

    def connect(self):
        print "[DEBUG] Entering DatabaseHandler.connect() function"
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
            # DB Name    : passwd_webui
            # Collection : users
            self.db = self.connection.passwd_webui.users
            # shadow_hashed = self.PasswordHandler.getshadow()
            self.salt = generate_salt()
            self.new_hashed = hashing(self.new_passwd, self.salt)
            self.userdata = {
                'username': self.username,
                'previous_salt': self.previous_salt,
                'previous_hashed': self.previous_hashed,
                'new_salt': self.salt,
                'new_hashed': self.new_hashed
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
        hashed = crypt.crypt(passwd, str(generate_salt()))
    else:
        hashed = crypt.crypt(passwd, '$6$' + salt + "$")
    return hashed


def generate_salt():
    salt = ([random.choice(string.ascii_letters +
                           string.digits) for _ in range(16)])
    salt = "$6$" + ''.join(salt) + "$"
    return salt


@route('/')
def index():
    return template('index.html')


@route('/modify_user', method='POST')
def modify_user():
    username = request.forms.get('username')
    previous_passwd = request.forms.get('previous_passwd')
    new_passwd = request.forms.get('new_passwd')

    print "[DEBUG] Instantiate class PasswordHandler"
    phandler = PasswordHandler(**locals())
    dbhandler = DatabaseHandler(**locals())

    phandler.check_data()

    print "[DEBUG] Compare password"
    if phandler.compare():
        # passwd = hashing(passwd)
        dbhandler.store()
        # Return hashed password, just for debug. To be remove.
        return """<p>User: %s<br>Pass: %s</p>""" % (username, dbhandler.new_hashed)


if __name__ == "__main__":
    args = docopt(__doc__, version="FIXME")

    app = app()

    run(host=args['--server'],
        port=int(args['--port']),
        app=app,
        reloader=True,
        debug=True)
