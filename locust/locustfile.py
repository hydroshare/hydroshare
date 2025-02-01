# import time
from locust import HttpUser, task, tag  # , between
from hsclient import HydroShare
import os
import glob
import urllib3
import logging
import random
urllib3.disable_warnings()

USERNAME = os.getenv("HS_USERNAME", "asdf")
PASSWORD = os.getenv("HS_PASSWORD", "asdf")

# get the host port and protocol from LOCUST_HOST which is the full origin
HOST = "localhost"
PORT = 8000
PROTOCOL = 'http'

LOCUST_HOST = os.getenv("LOCUST_HOST", "http://localhost:8000")
if LOCUST_HOST:
    parts = LOCUST_HOST.split(":")
    HOST = parts[1][2:]
    PROTOCOL = parts[0]
    try:
        PORT = int(parts[2])
    except IndexError:
        if PROTOCOL == 'https':
            PORT = 443
        else:
            PORT = 80


class HSUser(HttpUser):
    # wait_time = between(1, 2)
    number_of_resources = 1
    resources = {}
    randname = 0

    def on_start(self):
        logging.info(f"Starting a new user with hsclient: HOST: {HOST} PORT: {PORT} PROTOCOL: {PROTOCOL}")
        hs = HydroShare(username=USERNAME, password=PASSWORD, host=HOST, port=PORT, protocol=PROTOCOL)
        self.client.get("/accounts/login/", verify=False)
        self.hs = hs
        self.resources = {}

    def on_stop(self):
        for res in self.resources.values():
            logging.info(f"deleting {res}")
            res.delete()

        files = glob.glob('./*.zip')
        for f in files:
            logging.info(f"Cleanup file {f}")
            os.remove(f)

    @task
    @tag('get')
    def home(self):
        self.client.get("/home", verify=False)

    @task
    @tag('get')
    def discover(self):
        self.client.get("/search", verify=False)

    @task
    @tag('get')
    def my_resources(self):
        self.client.get("/my-resources/?f=owned&f=discovered&f=favorites&f=shared", verify=False)

    @task
    @tag('get')
    def get_resources(self):
        url = f"/hsapi/resource/?owner={USERNAME}&edit_permission=false&published=false&include_obsolete=false"
        with self.client.get(url, verify=False, catch_response=True) as response:
            if response.status_code == 200:
                # get the resources from the json
                resources = response.json().get('results')
                for res in resources:
                    resIdentifier = res.get('resource_id')
                    self.resources[resIdentifier] = self.hs.resource(resIdentifier)
                response.success()
            else:
                response.failure("Failed to get resources")
        pass

    @task
    @tag('post')
    def create(self):
        with self.client.post("/create", catch_response=True) as response:
            try:
                new_res = self.hs.create()
                resIdentifier = new_res.resource_id
                self.resources[resIdentifier] = new_res
                logging.info(f"created {resIdentifier}")
                response.success()
            except Exception as e:
                logging.error(f"Error creating resource: {e}")
                # mark as a locust failure
                response.failure(f"Error creating resource: {e}")

    @task
    @tag("async")
    @tag('post')
    def download(self):
        if not self.resources:
            return
        with self.client.post("/download", catch_response=True) as response:
            res_key = random.choice(list(self.resources.keys()))
            try:
                self.resources[res_key].download()
                logging.info(f"downloaded {res_key}")
                response.success()
            except Exception as e:
                logging.error(f"Error downloading resource: {e}")
                # mark as a locust failure
                response.failure(f"Error downloading resource: {e}")

    @task
    @tag("async")
    @tag('post')
    def copy(self):
        if not self.resources:
            return
        with self.client.post("/copy", catch_response=True) as response:
            res_key = random.choice(list(self.resources.keys()))
            try:
                self.resources[res_key].copy()
                logging.info(f"copied {res_key}")
                response.success()
            except Exception as e:
                logging.error(f"Error copying resource: {e}")
                # mark as a locust failure
                response.failure(f"Error copying resource: {e}")

    @task
    @tag("async")
    @tag('post')
    def add_files(self):
        if not self.resources:
            return
        with self.client.post("/add_files", catch_response=True) as response:
            res_key = random.choice(list(self.resources.keys()))
            # generate a random file name
            filename = f"{self.randname}-locustfile.py"
            self.randname = self.randname + 1
            # create the file locally
            with open(filename, "w") as f:
                f.write("Hello World")
            try:
                self.resources[res_key].file_upload(filename)
                logging.info(f"uploaded file to {res_key}")
                response.success()
            except Exception as e:
                logging.error(f"Error adding files to resource: {e}")
                # mark as a locust failure
                response.failure(f"Error adding files to resource: {e}")
            # cleanup the file
            os.remove(filename)

    @task
    @tag("async")
    @tag('post')
    def delete(self):
        if not self.resources:
            return
        with self.client.post("/delete_res", catch_response=True) as response:
            try:
                res_key = random.choice(list(self.resources.keys()))
                res = self.resources.pop(res_key)
                res.delete()
                print(f"deleted {res}")
                response.success()
            except Exception as e:
                logging.error(f"Error deleting resource: {e}")
                # mark as a locust failure
                response.failure(f"Error deleting resource: {e}")
