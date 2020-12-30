## passwd-webui - A password changer for Linux user

To allow users to change their own password without superuser/root privileges via web UI.

## Language:
* Python 2.7

## Database:
* MongoDB

## Modules:
* bottle
* docopt
* pymongo
* fileinput
* random
* string
* crypt
* spwd
* os

## How To's

This following instructions are made on Ubuntu 20.04.

1 - Install `Python2.7`

```
$ sudo apt install python2.7
```


2 - Install `pip2`

```
$ wget https://bootstrap.pypa.io/get-pip.py
$ sudo python2.7 get-pip.py
```

3 - Install `virtualenv`

```
$ sudo pip3 install virtualenv
```

4 - Install `MongoDB`

```
$ sudo apt install mongodb
```

5 - Make sure `MongoDB` is enabled and running on startup

```
$ sudo systemctl enable --now mongodb.service
```

6 - Clone the repo

```
$ git clone https://github.com/hotfloppy/passwd-webui.git
```

7 - Get into `passwd-webui` and activate the `virtualenv` so that we can use `pip2` modules without messing up system `pip`

```
$ cd passwd-webui
$ source venv/bin/activate
```

* Install all required modules

```
$ pip2 install -r requirements.txt
```

8 - Now everything should be ready. Starts your `passwd-webui` server:

```
$ sudo python2.7 index.py
```

* Help page:

```
$ python2.7 index.py --help
```

9 - And navigate to `http://localhost:8001` or `http://YOUR-IP:8001`.

**Notes:<br>
It's better to test this on dummy account. `sudo adduser dummy-user` would suffice.<br>
DO NOT test on real user account!**
