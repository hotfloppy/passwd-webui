#!/usr/bin/env python

"""
Password changer for Linux user

To allow users to change their own password without superuser/root privileges.

Usage:
  index.py [-s SERVER -H DBHOST -p port -P DBPORT]
  index.py [-h | --help]
  index.py --version

Options:
  -h --help                 Show this screen.
  -v --version              Show version.
  -s --server SERVER        Web server host [default: 0.0.0.0]
  -p --port PORT            Web server port [default: 8001].
  -H --dbhost DBHOST        Database host [default: localhost].
  -P --dbport DBPORT        Database port [default: 27017].
"""

import os
base_dir = os.path.dirname(os.path.abspath(__file__))
activate_this = os.path.join(base_dir, 'venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from bottle import run, route, abort, request, template, app
from pymongo import MongoClient, errors as e
from docopt import docopt
import spwd
import crypt
import random
import string
import fileinput


'''
  ____                                     _
 |  _ \ __ _ ___ _____      _____  _ __ __| |
 | |_) / _` / __/ __\ \ /\ / / _ \| '__/ _` |
 |  __/ (_| \__ \__ \\ V  V / (_) | | | (_| |
 |_| _ \__,_|___/___/ \_/\_/ \___/|_|  \__,_|
    | | | | __ _ _ __   __| | | ___ _ __
    | |_| |/ _` | '_ \ / _` | |/ _ \ '__|
    |  _  | (_| | | | | (_| | |  __/ |
    |_| |_|\__,_|_| |_|\__,_|_|\___|_|
'''


class PasswordHandler(object):
    def __init__(self,
                 username=None,
                 previous_passwd=None,
                 new_passwd=None,
                 **kwargs):
        """
        Class initialization

        Args:
            username:           Username
            previous_passwd:    Current/previous password
            new_passwd:         New password
        """
        self.username = username
        self.previous_passwd = previous_passwd
        self.new_passwd = new_passwd
        self.shadow_hashed = None
        self.previous_salt = None
        self.previous_hashed = None

    def check_input(self):
        """Check input

            Validate input given by user

            Args:
                None - use class variable:
                    self.username,
                    self.previous_passwd,
                    self.new_passwd

            Returns:
                None - just checking for:
                1 - all fields filled up
                2 - username exists, password match.
                    if user doesn't exist or password doesn't match,
                    raise HTTP error 400.

            Raises:
                None
        """
        print "[DEBUG] Entering check_input()"
        print self.username, self.previous_passwd, self.new_passwd

        if not self.previous_passwd:
            abort(400, "Current password required")

        if not self.username:
            abort(400, "Name required")
        else:
            self.getshadow(self.username)

        if not self.new_passwd:
            abort(400, "Password required")

        print "[DEBUG] Exiting check_input()"

    def compare(self):
        """Compare passwords

        Comparing password given by user
            with the one currently in shadown file

        Args:
            None

        Returns:
            True boolean if both passwords are match
            Error 400 if doesn't match

        Raises:
            None
        """

        print "self.username = {}".format(self.username)
        self.getshadow(self.username)
        self.getsalt(self.username)

        print "[DEBUG] previous_passwd = %s" % self.previous_passwd
        print "[DEBUG] previous_salt = %s" % self.previous_salt

        self.previous_hashed = self.hashing(self.previous_passwd, "$6$" + self.previous_salt + "$")

        print "[DEBUG] previous_hashed = %s" % self.previous_hashed
        print "[DEBUG] shadow_hashed = %s" % self.shadow_hashed

        if self.shadow_hashed == self.previous_hashed:
            return True
        else:
            abort(400, "Current password are incorrect")

    def getshadow(self, username=None):
        """Get hashed from shadow file

        Retrieve hashed stored in shadow file for given username

        Args:
            username:   (Optional) username to be check

        Returns:
            Hashed string from shadow file

        Raises:
            KeyError
        """
        try:
            print "username = {}".format(username)
            if username:
                self.shadow_hashed = spwd.getspnam(username)[1]
            else:
                self.shadow_hashed = spwd.getspnam(self.username)[1]
            return self.shadow_hashed
        except KeyError:
            print "[DEBUG] User %s doesn't exist" % self.username
            abort(400, "User %s doesn't exist" % self.username)

    def getsalt(self, username=None):
        """
        Retrieve salt used to hashing the password
            for given username

        Args:
            username:   (Optional) username of which salt to be retrieved.
                        If no username given, will use class self.username

        Returns:
            Salt used in shadow file

        Raises:
            None
        """
        if username:
            shadow_hashed = self.getshadow(username)
            self.previous_salt = shadow_hashed.split("$")[2]
        else:
            print "[DEBUG] shadow_hashed = %s" % self.shadow_hashed
            self.previous_salt = self.shadow_hashed.split("$")[2]
        return self.previous_salt

    def hashing(self, passwd, salt=None):
        """Hashing password with salt

        Generate a hashed value for given password and salt

        Args:
            passwd:     Password to be hashed
            salt:       (Optional) Salt to be use when hashing

        Returns:
            Hashed value

        Raises:
            None
        """
        print salt
        if not salt:
            hashed = crypt.crypt(passwd, str(self.generate_salt()))
        else:
            # hashed = crypt.crypt(passwd, '$6$' + salt + "$")
            hashed = crypt.crypt(passwd, salt)
        print "in hashing() | hashed = " + hashed
        return hashed

    def generate_salt(self):
        """Generate salt

        Generate salt to be use with hashing()

        Args:
            None

        Returns:
            Salt value

        Raises:
            None
        """
        salt = ([random.choice(string.ascii_letters +
                               string.digits) for _ in range(16)])
        salt = "$6$" + ''.join(salt) + "$"
        return salt

    def change_passwd(self, prev_hashed, new_hashed):
        """Change password

        Search and replace /etc/shadow file with newly generated hashed value

        Args:
            prev_hashed:    Hashed from current/previous password
            new_hashed:     Hashed from new password

        Returns:
            None

        Raises:
            None
        """

        # TODO: Retrieve hashed value from DB and write to /etc/shadow ,
        #       instead of directly write

        shadow_file = "/etc/shadow"
        for line in fileinput.input(shadow_file, inplace=True, backup='.bak'):
            line = line.replace(prev_hashed, new_hashed)
            print line,
        fileinput.close()


"""
  ____        _        _
 |  _ \  __ _| |_ __ _| |__   __ _ ___  ___
 | | | |/ _` | __/ _` | '_ \ / _` / __|/ _ \
 | |_| | (_| | || (_| | |_) | (_| \__ \  __/
 |____/ \__,_|\__\__,_|_.__/ \__,_|___/\___|
    | | | | __ _ _ __   __| | | ___ _ __
    | |_| |/ _` | '_ \ / _` | |/ _ \ '__|
    |  _  | (_| | | | | (_| | |  __/ |
    |_| |_|\__,_|_| |_|\__,_|_|\___|_|

"""


class DatabaseHandler(object):
    def __init__(self,
                 username=None,
                 previous_passwd=None,
                 new_passwd=None,
                 **kwargs):
        """
        Class initialization

        Args:
            username:           Username
            previous_passwd:    Current/previous password
            new_passwd:         New password
        """
        self.pwhandler = PasswordHandler(username, previous_passwd, new_passwd)

        self.username = username
        self.new_passwd = new_passwd
        self.new_salt = None
        self.new_hashed = None
        self.connection = None
        self.db = None
        self.userdata = None

    def connect(self):
        """Connect to database

        Establish new connection to Mongo database

        Args:
            None - use class variable:
                    self.connection

        Returns:
            None

        Raises:
            None
        """
        print "[DEBUG] Entering DatabaseHandler.connect() function"
        try:
            self.connection = MongoClient(
                host=args['--dbhost'],
                port=int(args['--dbport']),
                ServerSelectionTimeoutMS=1
            )
            self.connection.server_info()
        except Exception as err:
            print "[DEBUG] DB unavailable: %s" % err
            abort(500, "Could not establish connection to database")

    def store(self):
        self.connect()
        try:
            # TODO: store or replace. check the id/username
            # DB Name    : passwd_webui
            # Collection : users
            self.db = self.connection.passwd_webui.users

            self.previous_hashed = self.pwhandler.getshadow(self.username)
            self.previous_salt = self.pwhandler.getsalt(self.username)

            self.new_salt = self.pwhandler.generate_salt()
            self.new_hashed = self.pwhandler.hashing(self.new_passwd, self.new_salt)
            self.userdata = {
                'username': self.username,
                'previous_salt': self.previous_salt,
                'previous_hashed': self.previous_hashed,
                'new_salt': self.new_salt,
                'new_hashed': self.new_hashed
            }
            self.db.insert_one(self.userdata)
            self.pwhandler.change_passwd(self.previous_hashed, self.new_hashed)
        # except e.OperationFailure, err:
        except Exception as err:
            print "[DEBUG] Operation failed: %s" % err
            abort(500, "Operation failed: %s" % err)


@route('/')
def index():
    return template('index.html')


@route('/modify_user', method='POST')
def modify_user():
    username = request.forms.get('username').lower()
    previous_passwd = request.forms.get('previous_passwd')
    new_passwd = request.forms.get('new_passwd')

    print "[DEBUG] Instantiate class PasswordHandler"
    pwhandler = PasswordHandler(username, previous_passwd, new_passwd)
    dbhandler = DatabaseHandler(username, previous_passwd, new_passwd)

    pwhandler.check_input()

    print "[DEBUG] Compare password"
    if pwhandler.compare():
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
