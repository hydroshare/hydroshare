## Using http auth

If the user wants to use http auth by setting the **USE\_HTTP\_AUTH** variable to **true** in `hydroshare-config.yml`, the user will first need to generate a `.htpasswd` file for the nginx container to use.

### Generating a new .htpasswd file

By default the username/password combination for the Nginx Docker container using http auth is not set. To set this the user will need to run the **generate_htpasswd.exp** script with a new username and password combination.

**Note** this script requires **sudo** rights and the **expect** package.

```
$ cd /home/hydro/hydroshare/nginx/
$ sudo generate_htpasswd.sh new_username new_password
```

Once completed a new `.htpasswd` file will be generated using OpenSSL. A corresponding `htpasswd` plain text file is also generated as a reminder to the user of what the username/password configuration has been set to.

Example:

To set the username / password combination to be:

- username: **my-user**
- password: **my-password**

The user would run the following:

```
$ cd /home/hydro/hydroshare/nginx/
$ sudo ./generate_htpasswd.exp my-user my-password
[sudo] password for hydro:
spawn sudo sh -c echo -n 'my-user:' > .htpasswd
spawn sudo sh -c openssl passwd -apr1 >> .htpasswd
Password: my-password

Verifying - Password: my-password

spawn sudo sh -c echo 'Username: my-user, Password: my-password' > htpasswd

$ cat .htpasswd
my-user:$apr1$AzSGC/na$WLxG415Zl2AcJ5lukRbV./

$ cat htpasswd
Username: my-user, Password: my-password
```

Once completed, the user could enable the `USE_HTTP_AUTH` variable to be true in the `config/hydroshare-config.yml` file. Then anytime the `USE_NGINX` variable was set to true, simple http auth would be enforced using the contents of the `.htpasswd` file.

```yaml
...
### Deployment Options ###
USE_NGINX: true
USE_SSL: false
USE_HTTP_AUTH: true
...
```