# HydroShare _(hydroshare)_

HydroShare is a website and hydrologic information system for sharing hydrologic data and models aimed at giving users the cyberinfrastructure needed to innovate and collaborate in research to solve water problems. HydroShare is designed to advance hydrologic science by enabling the scientific community to more easily and freely share products resulting from their research, not just the scientific publication summarizing a study, but also the data and models used to create the scientific publication. With HydroShare users can: (1) share data and models with colleagues; (2) manage who has access to shared content; (3) share, access, visualize and manipulate a broad set of hydrologic data types and models; (4) use the web services API to program automated and client access; (5) publish data and models to meet the requirements of research project data management plans; (6) discover and access data and models published by others; and (7) use web apps to visualize, analyze, and run models on data in HydroShare.

## Install

Prerequisites:
- Docker
- Node.js

Supported OS (developer laptops): macOS 10.12+, Win10+ Pro, Ent, Edu, Acad Pro, Acad Ent, CentOS 7 and Ubuntu/Lubuntu 18+ LTS

We got some troubles with Lubuntu 16.04 LTS so probably Ubuntu 16.04 LTS also does not work

Familiarity with docker and git are required to work with HydroShare

disovery-atlas (search) frontend requires Node version specified in [that module's package.json](discovery-atlas/package.json).
It's recommended to use [Node Version Manager](https://github.com/nvm-sh/nvm) to switch between different versions of node in your local environment.

Some VM skills such as network settings (Bridge/NAT/Host only) and file sharing are needed if you work with a virtual machine.

For Windows, this link is required to proceed - https://docs.google.com/document/d/1wIQEYq3OkWmzPTHeyGyjXLZWrinEXojJPBTJq7fczL8/edit#heading=h.mfmd8m9mxvsl

### Getting the source code

1. Open a terminal (macOS, Linux) or command prompt (Windows)
Navigate to where you will store the source code, for example /Users/yourname/repo/

2. Clone repository

Note: the default branch for hydroshare is `develop`
```
git clone https://github.com/hydroshare/hydroshare.git
```

Or if you are using ssh:
```
git clone git@github.com:hydroshare/hydroshare.git
cd hydroshare
```

### One-time local development setup

1. Log into Docker:
```
docker login
```
(You will be asked to authenticate with Docker.)

2. Launch the stack
```
./local-dev-first-start-only.sh --seed-dev-resources
```

This runs a script that will:
- Delete all containers, images, and volumes for a clean start
- Update config files with your user/group IDs
- Install dependencies (npm, pm2) and build frontend assets
- Recreate Docker containers and database
- Run migrations and set up search indexes
- Seed some Hydroshare resources for the seeded user with username asdf (exclude `--seed-dev-resources` from the command above to skip this).  You can also seed data after the fact by running `docker exec hydroshare python manage.py seed_dev_resources --username asdf`.
- Starts the stack defined in the Docker Compose file local-dev.yml

The [local-dev-first-start-only.sh](./local-dev-first-start-only.sh) will spin up all docker containers in the [local-dev.yml](./local-dev.yml). It does NOT spin up a container for Discover -- instead, the script uses [PM2](https://pm2.io/) to run the Vite dev server to take advantage of [HMR](https://vite.dev/guide/features#hot-module-replacement).

Alternatively, to run Discover as a static build inside a local Docker container you can:
- Uncomment the discovery-atlas service in [local-dev.yml](./local-dev.yml)
- Uncomment the line in the nginx service in [local-dev.yml](./local-dev.yml) to have nginx wait for discovery-atlas to be up
- Change the `location /discover/ proxy_pass` entry in [nginx/nginx-local-dev.conf](nginx/nginx-local-dev.conf) to `http://discovery-atlas:80/discover/`

3. Sanity Checks and where to view the app and documentation:
- Some WARNINGs are normal. 
- HydroShare is available in your browser at https://localhost
- The default admin page is https://localhost/admin
- The default admin account is admin:default
- Swagger API docs https://localhost/hsapi/

4. Start & Stop & Log

To start HydroShare, only need to open a shell, change to HydroShare code directory then run
```
docker-compose -f local-dev.yml (up | down) [-d] [--build]
```

Note bracketed -d (run in detached mode) is optional and you don’t paste in the brackets.
Use -d option if you want to run your containers in the background and not see live logs.
Use --build option in case docker keeps image in cache and does not update correctly while modifying the Dockerfile.

To stop HydroShare, only need to close the running windows or open a new windows then run
```
docker-compose -f local-dev.yml down
```

All data is persisted for the next start.

To see the logs in case you start with -d option, run
```
docker-compose -f local-dev.yml logs
```
Or
```
docker logs <container name>
```

5. Logging in / creating an account

The locally-running app will be populated with a couple accounts:
- admin (pw: default)
- asdf (pw: asdf) -- if you ran `./local-dev-first-start-only.sh --seed-dev-resources` this user will have some Hydroshare resources created

Or use the following process to create a new account:

Open Hydroshare in your browser and visit the [sign-up page](http://localhost/sign-up/). Use the UI to sign up for a new account, then view the hydroshare container logs with
```
docker logs hydroshare
```
to get a verification link.  Look for
```
Welcome to HydroShare. This email address was used to request an account on www.hydroshare.org.
If you originated the request, please use the link below to verify your email address and activate your account.
```
and get the link below that text, paste it into your browser and save the new account in the UI.

## Usage

For all intents and purposes, Hydroshare is a large Python/Django application with some extra features and technologies added on:
- A Vue app for searching, backed by MongoDB Atlas
- Redis for caching
- RedPanda for concurrency and serialization
- Minio for a S3 file system
- PostgreSQL for the database backend

## Testing and Debugging

### Testing

Tests are run via normal Django tools and conventions. However, you should use the `hsctl` script mentioned abouve with the `managepy` command. For example: `./hsctl managepy test hs_core.tests.api.rest.test_resmap --keepdb`.

There are currently over 600 tests in the system, so it is highly recommended that you run the test suites separately from one another.

### Debugging

You can debug via PyCharm by following the instructions [here](https://docs.google.com/document/d/1w3hWAPMEUBL4qTjpHb5sYMWEiWFqwaarI0NkpKz3r6w/edit#).

## Other Configuration Options

## Contribute

There are many ways to contribute to Hydroshare. Review [Contributing guidelines](https://github.com/hydroshare/hydroshare/blob/develop/docs/contributing.rst) and github practices for information on
1. Opening issues for any bugs you find or suggestions you may have
2. Developing code to contribute to HydroShare 
3. Developing a HydroShare App
4. Submiting pull requests with code changes for review

## License 

Hydroshare is released under the BSD 3-Clause License. This means that [you can do what you want, so long as you don't mess with the trademark, and as long as you keep the license with the source code](https://tldrlegal.com/license/bsd-3-clause-license-(revised)).

©2017 CUAHSI. This material is based upon work supported by the National Science Foundation (NSF) under awards [1148453](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1148453), [1148090](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1148090), [1664061](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1664061), [1664018](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1664018), [1664119](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1664119), [1338606](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1338606), and [1849458](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1849458). Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.

