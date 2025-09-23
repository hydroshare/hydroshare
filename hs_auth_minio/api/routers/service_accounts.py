import logging
import secrets
import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("micro-auth")


class KeyRequest(BaseModel):
    username: str
    expiry_days: int = 30


class ServiceAccountResponse(BaseModel):
    access_key: str
    secret_key: str


class AccessKeyAndExpiry(BaseModel):
    access_key: str
    expiry: str


class ServiceAccountListResponse(BaseModel):
    service_accounts: list[AccessKeyAndExpiry]


@router.post("/auth/minio/sa/")
async def create_service_account(key_request: KeyRequest, response: Response) -> ServiceAccountResponse:
    try:
        # mc admin user add myminio newuser newusersecret
        try:
            proc = await asyncio.create_subprocess_shell("mc admin user info hydroshare " + key_request.username,
                                                         stdout=asyncio.subprocess.PIPE,
                                                         stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if "Specified user does not exist" in stdout.decode('utf-8') or \
               "Specified user does not exist" in stderr.decode('utf-8'):
                print(f"Creating user for {key_request.username}")
                await asyncio.create_subprocess_shell(
                    "mc admin user add hydroshare '" + key_request.username
                    + "' " + secrets.token_urlsafe(16),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
        except Exception:
            print(f"Creating user for {key_request.username}")
            await asyncio.create_subprocess_shell(
                "mc admin user add hydroshare '" + key_request.username
                + "' " + secrets.token_urlsafe(16),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
        print(f"Creating Service Account for {key_request.username}")
        expiry_date = (
            datetime.now() + timedelta(days=key_request.expiry_days)).strftime("%Y-%m-%d")
        proc = await asyncio.create_subprocess_shell(
            "mc admin user svcacct add hydroshare '"
            + key_request.username + "' --expiry " + expiry_date,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        output = stdout.decode('utf-8')
    except Exception as e:
        logger.error(f"CLI command failed with error: {e}")
        raise e
    if "Access Key:" not in output:
        logger.error(f"Failed to create service account for {
                     key_request.username}")
        raise Exception(f"Failed to create service account {output}")
    access_key = output.split("Access Key: ")[1].split("\n")[0]
    secret_key = output.split("Secret Key: ")[1].split("\n")[0]
    response.status_code = status.HTTP_201_CREATED
    return ServiceAccountResponse(access_key=access_key, secret_key=secret_key)


@router.get("/auth/minio/sa/{username}")
async def get_service_accounts(username: str) -> ServiceAccountListResponse:
    try:
        proc = await asyncio.create_subprocess_shell(
            "mc admin user svcacct list hydroshare " + username,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        stdout = stdout.decode('utf-8')
    except Exception as e:
        logger.error(f"CLI command failed with error: {e.stderr}")
        raise e
    print(f"Service Accounts retrieved successfully for {username}")
    print(stdout)
    lines = stdout.splitlines()[1:]  # Skip the header line
    service_accounts = []
    for line in lines:
        parts = line.split("|")
        service_account = {"access_key": parts[
            0].strip(), "expiry": parts[1].strip()}
        service_accounts.append(service_account)
    return {"service_accounts": service_accounts}


@router.delete("/auth/minio/sa/{service_account_key}")
async def delete_service_account(service_account_key: str, response: Response):
    try:
        print(f"Deleting Service Account {service_account_key}")
        proc = await asyncio.create_subprocess_shell(
            "mc admin user svcacct remove hydroshare " + service_account_key,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        _, _ = await proc.communicate()
        print("Service Account deleted successfully")
        response.status_code = status.HTTP_204_NO_CONTENT
    except Exception as e:
        logger.error(f"CLI command failed with error: {e.stderr}")
        raise e
