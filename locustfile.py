from locust import HttpUser, task, constant_throughput, constant, between
from hsclient import HydroShare
from urllib3 import PoolManager
from gevent.pool import Group

num_of_parallel_requests = 15


class HSUser(HttpUser):
    # pool_manager = PoolManager(maxsize=100, block=True)
    # wait_time = between(0.05, 0.1)
    # @task
    # def my_resources(self):
    #     self.client.get("/my-resources/?f=owned&f=discovered&f=favorites&f=shared", verify=False)

    # @task
    # def landing_page(self):
    #     self.client.get("/landingPage/", verify=False)

    # @task
    # def landing_page_parallel(self):
    #     # self.client.get("/landingPage/", verify=False)
    #     group = Group()
    #     for i in range(0, num_of_parallel_requests):
    #         group.spawn(lambda: self.client.get("/landingPage/"))
    #     group.join()
    #         # print("Response status code:", resp.status_code)
    #         # print("Response text:", resp.text)
    #         # resp.success()
    #     # wait_time = constant(.0001)

    # @task
    # def invalid_bounding_box_parallel(self):
    #     url = "/hsapi/resource/?full_text_search=lthia&west=-84.211434&east=-83.376577&north=42.17689&south=42.735607&coverage_type=box&page=1"
    #     group = Group()
    #     for i in range(0, num_of_parallel_requests):
    #         group.spawn(lambda: self.client.get(url))
    #     group.join()
        # self.client.get(url, verify=False)

    # @task
    # def invalid_bounding_box(self):
    #     self.client.get("/hsapi/resource/?full_text_search=lthia&west=-84.211434&east=-83.376577&north=42.17689&south=42.735607&coverage_type=box&page=1", verify=False)
    #         print("Response status code:", resp.status_code)
    #         print("Response text:", resp.text)
    #         resp.success()
    #     wait_time = constant(.0001)

    # @task
    # def discover_param(self):
    #     self.client.get("/search/?subject=Schmidt", verify=False)
    #     # wait_time = constant_throughput(0.01)

    # @task
    # def discover_bare(self):
    #     self.client.get("/search", verify=False)
    #     # wait_time = constant_throughput(0.01)

    # @task
    # def get_task(self):
    #     self.client.get("/hsapi/_internal/get_task/ffd71847-e0d4-43b3-bef6-4e809b6643bf", verify=False)
    #     # self.client.get("/hsapi/_internal/", verify=False)
    #     wait_time = constant_throughput(0.0001)

    def on_start(self):
        hs = HydroShare(username="meh", password="meh", host="beta.hydroshare.org", port=443, protocol='https')
        # self.client.get("/accounts/login/", verify=False)
        # self.client.get("/hsapi/user", verify=False)
        self.hs = hs
        new_resource = self.hs.create()

        # Get the HydroShare identifier for the new resource
        resIdentifier = new_resource.resource_id
        # Construct a hyperlink for the new resource
        print('Your new resource is available at: ' + new_resource.metadata.url)

    @task
    def create_resource(self):
        self.client.get("/hsapi/test", verify=False)
        new_resource = self.hs.create()

        # Get the HydroShare identifier for the new resource
        resIdentifier = new_resource.resource_id
        # Construct a hyperlink for the new resource
        print('Your new resource is available at: ' + new_resource.metadata.url)