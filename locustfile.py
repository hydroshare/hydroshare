# import time
from locust import HttpUser, task
from hsclient import HydroShare
import os
import glob


class HSUser(HttpUser):
    # wait_time = between(1, 5)

    @task
    def home(self):
        self.client.get("/home", verify=False)

    @task
    def discover(self):
        self.client.get("/search", verify=False)

    @task
    def create(self):
        new_res = self.hs.create()
        resIdentifier = new_res.resource_id
        print(f"created {resIdentifier}")
        self.resources[resIdentifier] = new_res

    @task
    def delete(self):
        if self.resources:
            res_key = list(self.resources.keys())[-1]
            res = self.resources.pop(res_key)
            print(f"deleted {res}")
            res.delete()

    @task
    def download(self):
        if self.resources:
            res_key = list(self.resources.keys())[-1]
            print(f"downloaded {res_key}")
            self.resources[res_key].download()

    @task
    def my_resources(self):
        self.client.get("/my-resources/?f=owned&f=discovered&f=favorites&f=shared", verify=False)

    def on_start(self):
        hs = HydroShare(username="asdf", password="asdf", host="localhost", port=8000, protocol='http')
        self.client.get("/accounts/login/", verify=False)
        self.hs = hs
        self.resources = {}

    def on_stop(self):
        for res in self.resources.values():
            print(f"deleting {res}")
            res.delete()

        files = glob.glob('./*.zip')
        for f in files:
            print(f"Cleanup file {f}")
            os.remove(f)
