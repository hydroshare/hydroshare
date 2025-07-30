# import time
from locust import HttpUser, task, tag  # , between
from locust.exception import RescheduleTask
from hsclient import HydroShare
import os
import glob
import urllib3
import logging
import time

import base64
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

FILES = []
randname = 0


def createFile(size, randname=0):
    """Create a file of a given size in bytes."""
    filename = f"{randname}-locustfile.py"
    randname += 1
    with open(filename, "wb") as f:
        f.seek(size - 1)
        f.write(b"\0")
    FILES.append(filename)
    logging.info(f"Created file {filename} of size {size} bytes")
    return filename


# create 3 files, # 1 small, 1 1GB, and 1 2GB
for file_size in [100, 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024]:
    createFile(file_size, randname=randname)


class HSUser(HttpUser):
    # wait_time = between(1, 2)
    number_of_resources = 5
    resources = {}
    randname = 0
    files = FILES

    def on_start(self):
        logging.info(f"Starting a new user with hsclient: HOST: {HOST} PORT: {PORT} PROTOCOL: {PROTOCOL}")
        hs = HydroShare(username=USERNAME, password=PASSWORD, host=HOST, port=PORT, protocol=PROTOCOL)
        self.client.get("/accounts/login/", verify=False)
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

        # cleanup the files created
        for f in self.files:
            try:
                os.remove(f)
                logging.info(f"Removed file {f}")
            except Exception as e:
                logging.error(f"Error removing file {f}: {e}")

    def fake_metadata(self, res, file_size=100, file_name="test.txt"):
        return {
            "filename": file_name,
            "hs_res_id": res.resource_id,
            "path": f"{res.resource_id}/data/contents/{file_name}",
            "file_size": str(file_size),
            "username": USERNAME,
        }

    def create_request_metadata(self, resource, file_size=100, file_name="test.txt"):
        # https://github.com/alican/django-tus/blob/2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8/django_tus/views.py#L38
        headers = {}

        # build the HTTP_UPLOAD_METADATA string as comma and space separated key-value pairs
        metadata = self.fake_metadata(resource, file_size=file_size, file_name=file_name)
        # The Upload-Metadata request and response header MUST consist of one or more comma-separated key-value pairs.
        # The key and value MUST be separated by a space. 
        # The key MUST NOT contain spaces and commas and MUST NOT be empty. 
        # The key SHOULD be ASCII encoded and the value MUST be Base64 encoded. 
        # All keys MUST be unique. The value MAY be empty. In these cases, the space, which would normally separate the key and the value, MAY be left out.
        encoded_metadata = ",".join(
            f"{key} {base64.b64encode(value.encode()).decode()}"
            if value else key
            for key, value in metadata.items()
        )
        headers["HTTP_UPLOAD_METADATA"] = encoded_metadata
        headers["HTTP-UPLOAD-METADATA"] = encoded_metadata
        headers["UPLOAD_METADATA"] = encoded_metadata
        headers["UPLOAD-METADATA"] = encoded_metadata
        headers["HTTP_TUS_RESUMABLE"] = "1.0.0"
        headers["HTTP_CONTENT_LENGTH"] = str(file_size)

        # set auth headers using the self.hs._hs_session
        # _hs_session can have username and password, or a token
        token = getattr(self.hs._hs_session, "token", None)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            headers["Authorization"] = f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode()).decode()}"
        return headers

    def _tus_upload(self, file_path, resource, chunk_size=100 * 1024 * 1024):  # 100MB chunks by default
        """
        Helper method to handle Tus protocol upload
        """
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Step 1: Create upload (Tus create extension)
        headers = self.create_request_metadata(resource, file_size=file_size, file_name=file_name)

        with self.client.post(
            "/hsapi/tus/",
            headers=headers,
            name="/hsapi/tus/ [CREATE]",
            catch_response=True
        ) as response:
            if not response.ok:
                logging.error(f"Failed to create Tus upload: {resource.resource_id} with response {response}")
                raise RescheduleTask(f"Failed to create Tus upload {response} with headers {headers}")
            location = response.headers.get("Location")
            if not location:
                raise RescheduleTask("No Location header in Tus create response")

            upload_url = location

        # Step 2: Upload chunks
        offset = 0
        with open(file_path, 'rb') as f:
            while offset < file_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                chunk_len = len(chunk)
                headers = {
                    "Tus-Resumable": "1.0.0",
                    "Content-Type": "application/offset+octet-stream",
                    "Upload-Offset": str(offset)
                }

                with self.client.patch(
                    upload_url,
                    headers=headers,
                    data=chunk,
                    name="/hsapi/tus/ [UPLOAD_CHUNK]",
                    catch_response=True
                ) as response:
                    if not response.ok:
                        raise RescheduleTask(f"Failed to upload chunk: {response.text}")

                    new_offset = int(response.headers.get("Upload-Offset", 0))
                    if new_offset != offset + chunk_len:
                        raise RescheduleTask(f"Offset mismatch: expected {offset + chunk_len}, got {new_offset}")

                    offset = new_offset

        return upload_url

    @task
    @tag("async")
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

    # @task
    # @tag("async")
    # @tag('post')
    # def add_1gb_file(self):
    #     with self.client.post("/add_1gb_file", catch_response=True) as response:
    #         new_res = self.hs.create()
    #         resIdentifier = new_res.resource_id
    #         self.resources[resIdentifier] = new_res
    #         filename = self.files[1]  # use the second file created
    #         try:
    #             self._tus_upload(filename, chunk_size=10*1024*1024)  # 10MB chunks for larger files
    #             logging.info(f"uploaded 1GB file to {resIdentifier}")
    #             response.success()
    #         except Exception as e:
    #             logging.error(f"Error adding files to resource: {e}")
    #             response.failure(f"Error adding files to resource: {e}")

    # @task
    # @tag("async")
    # @tag('post')
    # def add_2gb_file(self):
    #     with self.client.post("/add_2gb_file", catch_response=True) as response:
    #         new_res = self.hs.create()
    #         resIdentifier = new_res.resource_id
    #         self.resources[resIdentifier] = new_res
    #         filename = self.files[2]  # use the third file created
    #         try:
    #             self._tus_upload(filename, chunk_size=10*1024*1024)  # 10MB chunks for larger files
    #             logging.info(f"uploaded 2GB file to {resIdentifier}")
    #             response.success()
    #         except Exception as e:
    #             logging.error(f"Error adding files to resource: {e}")
    #             response.failure(f"Error adding files to resource: {e}")
