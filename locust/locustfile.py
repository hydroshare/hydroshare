# import time
from locust import HttpUser, task, tag, events  # , between
from hsclient import HydroShare
import os
import glob
import urllib3
import logging
import random

import base64
urllib3.disable_warnings()

TUS_ENDPOINT = os.getenv("HS_TUS_ENDPOINT", "/django_s3/tus/")
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

FILES = []


def createFile(size):
    """Create a file of a given size in bytes."""
    filename = f"{size}-locusttestfile.dat"
    with open(filename, "wb") as f:
        f.seek(size - 1)
        f.write(b"\0")
    FILES.append(filename)
    logging.info(f"Created file {filename} of size {size} bytes")
    return filename


# create 3 files, # 1 small, 1 1GB, and 1 2GB
for file_size in [100, 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024]:
    createFile(file_size)


# https://docs.locust.io/en/stable/api.html#locust.event.Events.test_stop
@events.test_stop.add_listener
def test_stop_handler(**kwargs):
    # cleanup the files created
    for f in FILES:
        try:
            os.remove(f)
            logging.info(f"Removed file {f}")
        except Exception as e:
            logging.warning(f"Error removing file {f}: {e}")


class HSUser(HttpUser):
    # wait_time = between(1, 2)
    number_of_resources = 5
    resources = {}
    randname = 0
    files = FILES

    def on_start(self):
        logging.info(f"Starting a new user with hsclient: HOST: {HOST} PORT: {PORT} PROTOCOL: {PROTOCOL}")
        hs = HydroShare(username=USERNAME, password=PASSWORD, host=HOST, port=PORT, protocol=PROTOCOL)
        self.client.get("/accounts/login/", verify=False, auth=(USERNAME, PASSWORD))
        self.hs = hs
        self.resources = {}
        logging.info(f"Logged in as {USERNAME} to HydroShare at {HOST}:{PORT} with protocol {PROTOCOL}")

    def on_stop(self):
        for res in self.resources.values():
            logging.info(f"Deleting resource {res.resource_id}")
            res.delete()

        files = glob.glob('./*.zip')
        for f in files:
            logging.info(f"Cleanup file {f}")

    # =============================================================================
    # Tus upload tests
    # =============================================================================

    def fake_tus_metadata(self, res, file_size=100, file_name="test.txt"):
        return {
            "filename": file_name,
            "hs_res_id": res.resource_id,
            "path": f"{res.resource_id}/data/contents/{file_name}",
            "file_size": str(file_size),
            "username": USERNAME,
        }

    def create_ini_tus_post_request_metadata(self, resource, file_size=100, file_name="test.txt"):
        # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/views.py#L38
        # https://tus.io/protocols/resumable-upload#post
        headers = {}

        # build the HTTP_UPLOAD_METADATA string as comma and space separated key-value pairs
        metadata = self.fake_tus_metadata(resource, file_size=file_size, file_name=file_name)
        # The Upload-Metadata request and response header MUST consist of one or more comma-separated key-value pairs.
        # The key and value MUST be separated by a space.
        # The key MUST NOT contain spaces and commas and MUST NOT be empty.
        # The key SHOULD be ASCII encoded and the value MUST be Base64 encoded.
        # All keys MUST be unique. The value MAY be empty.
        # In these cases, the space, which would normally separate the key and the value, MAY be left out.
        encoded_metadata = ",".join(
            f"{key} {base64.b64encode(value.encode()).decode()}"
            if value else key
            for key, value in metadata.items()
        )
        headers["Upload-Length"] = str(file_size)
        headers["UPLOAD-METADATA"] = encoded_metadata
        headers["TUS-RESUMABLE"] = "1.0.0"

        return headers

    def _tus_upload(self, file_path, resource, chunk_size=10 * 1024 * 1024):  # 10MB chunks by default
        """
        Helper method to handle Tus protocol upload
        """
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Step 1: Create upload (Tus create extension)
        headers = self.create_ini_tus_post_request_metadata(resource, file_size=file_size, file_name=file_name)

        with self.client.post(
            TUS_ENDPOINT,
            headers=headers,
            name=f"{resource.resource_id}/{file_name} [CREATE]",
            catch_response=True,
            auth=(USERNAME, PASSWORD)
        ) as response:
            if not response.ok:
                logging.error(f"Failed to create Tus upload: {resource.resource_id} with response {response}")
                response.failure(f"Failed to create Tus upload {response} with headers {headers}")
            location = response.headers.get("Location")
            if not location:
                response.failure("No Location header in response")

            upload_url = location

        # Step 2: Upload chunks
        with open(file_path, 'rb') as f:
            # use a head request to get the upload offset in case of resuming an upload
            # https://tus.io/protocols/resumable-upload#head
            logging.info(f"Conducting HEAD request to get upload offset for {resource.resource_id}/{file_name}")
            offset = 0
            with self.client.head(
                upload_url,
                headers={"Tus-Resumable": "1.0.0"},
                name=f"{resource.resource_id}/{file_name} [HEAD]",
                catch_response=True,
                auth=(USERNAME, PASSWORD)
            ) as head_response:
                if not head_response.ok:
                    head_response.failure(f"Failed to get upload offset: {head_response.text}")
                offset = int(head_response.headers.get("Upload-Offset", 0))
            while offset < file_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                chunk_len = len(chunk)
                # https://tus.io/protocols/resumable-upload#patch
                headers = {
                    "Tus-Resumable": "1.0.0",
                    "Content-Type": "application/offset+octet-stream",
                    "Upload-Offset": str(offset),
                    "Content-Length": str(chunk_len),
                }

                with self.client.patch(
                    upload_url,
                    headers=headers,
                    data=chunk,
                    name=f"{resource.resource_id}/{file_name} [UPLOAD_CHUNK]",
                    catch_response=True,
                    auth=(USERNAME, PASSWORD)
                ) as response:
                    if not response.ok:
                        response.failure(f"Failed to upload chunk: {response.text}")

                    new_offset = int(response.headers.get("Upload-Offset", 0))
                    if new_offset != offset + chunk_len:
                        response.failure(
                            f"Upload-Offset mismatch: expected {offset + chunk_len}, got {new_offset}"
                        )

                    offset = new_offset

        return upload_url

    @task
    @tag("upload")
    @tag("tus")
    @tag('post')
    def add_small_file(self):
        logging.info("Creating a new resource and uploading a small file")
        new_res = self.hs.create()
        logging.info(f"Created resource {new_res.resource_id}")
        resIdentifier = new_res.resource_id
        self.resources[resIdentifier] = new_res
        filename = self.files[0]  # use the first file created
        logging.info(f"Uploading small file {filename} to resource {resIdentifier}")
        try:
            self._tus_upload(filename, resource=new_res)
            logging.info(f"Uploaded small file {filename} to resource {resIdentifier}")
        except Exception as e:
            logging.error(f"Error adding files to resource: {e}")

    @task
    @tag("upload")
    @tag("tus")
    @tag('post')
    def add_1gb_file(self):
        logging.info("Creating a new resource and uploading a 1gb file")
        new_res = self.hs.create()
        logging.info(f"Created resource {new_res.resource_id}")
        resIdentifier = new_res.resource_id
        self.resources[resIdentifier] = new_res
        filename = self.files[1]  # use the first file created
        logging.info(f"Uploading 1GB file {filename} to resource {resIdentifier}")
        try:
            self._tus_upload(filename, resource=new_res, chunk_size=10 * 1024 * 1024)  # 10MB chunks
            logging.info(f"uploaded 1GB file to {resIdentifier}")
        except Exception as e:
            logging.error(f"Error adding files to resource: {e}")

    @task
    @tag("upload")
    @tag("tus")
    @tag('post')
    def add_2gb_file(self):
        logging.info("Creating a new resource and uploading a 2gb file")
        new_res = self.hs.create()
        logging.info(f"Created resource {new_res.resource_id}")
        resIdentifier = new_res.resource_id
        self.resources[resIdentifier] = new_res
        filename = self.files[2]  # use the second file created
        logging.info(f"Uploading 2GB file {filename} to resource {resIdentifier}")
        try:
            self._tus_upload(filename, resource=new_res, chunk_size=10 * 1024 * 1024)  # 10MB chunks
            logging.info(f"uploaded 2GB file to {resIdentifier}")
        except Exception as e:
            logging.error(f"Error adding files to resource: {e}")

    # =============================================================================
    # Auth tests
    # =============================================================================

    def _test_auth(self, resource):
        """
        Helper method to test authentication
        """
        with self.client.get(
            f"/hsapi/resource/{resource.resource_id}/",
            auth=(USERNAME, PASSWORD),
            name="/hsapi/resource/auth [GET]",
            catch_response=True,
        ) as response:
            if not response.ok:
                logging.error(f"Failed to get resource: {resource.resource_id} with response {response}")
                response.failure(f"Failed to get resource {resource.resource_id} with response {response}")

    def _test_no_auth(self, resource):
        """
        Helper method to test authentication
        """
        with self.client.get(
            f"/hsapi/resource/{resource.resource_id}/",
            name="/hsapi/resource/no_auth [GET]",
            catch_response=True
        ) as response:
            if not response.ok:
                logging.info(f"As expected, failed to get resource: {resource.resource_id} with response {response}")
                if response.status_code == 403:
                    response.success()
            else:
                response.failure(f"Failed to get resource {resource.resource_id} with response {response}")

    @task
    @tag("auth")
    @tag('get')
    def test_auth(self):
        logging.info("Creating a new resource and testing authentication")
        new_res = self.hs.create()
        logging.info(f"Created resource {new_res.resource_id}")
        resIdentifier = new_res.resource_id
        self.resources[resIdentifier] = new_res
        self._test_auth(new_res)

    @task
    @tag("auth")
    @tag('get')
    def test_no_auth(self):
        logging.info("Creating a new resource and testing no authentication")
        new_res = self.hs.create()
        logging.info(f"Created resource {new_res.resource_id}")
        resIdentifier = new_res.resource_id
        self.resources[resIdentifier] = new_res
        self._test_no_auth(new_res)

    # =============================================================================
    # General page render GET tests
    # =============================================================================

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

    # =============================================================================
    # Resource manipulation tests
    # =============================================================================

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
    @tag("upload")
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
            logging.warning("No resources available for deletion")
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
