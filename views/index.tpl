<html>
    <head>
        <title>Modify Users</title>
    </head>
    <body>
        <center>
            <h1>Release the Kraken!</h1>
            <form action="/modify_user" method="POST">
            <p>Current Password:<br>
            <input type="password" name="current_passwd" id="current_passwd"></p>
            <p>Username:<br>
            <input type="text" name="username" id="username"></p>
            <p>New Password:<br>
            <input type="password" name="passwd" id="passwd"></p>
            <input type="submit" value="Submit">
            </form>
        </center>
    </body>
</html>
