#!usr/bin/env python3

import os
import json

import pytest_asyncio

from core import CoreMetadata
from dataset import DatasetMetadata


@pytest_asyncio.fixture(scope="function")
async def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest_asyncio.fixture
async def core_data(change_test_dir):
    with open("data/core_metadata.json", "r") as f:
        return json.loads(f.read())


@pytest_asyncio.fixture
async def dataset_data(change_test_dir):
    with open("data/dataset_metadata.json", "r") as f:
        return json.loads(f.read())


@pytest_asyncio.fixture
async def core_model():
    return CoreMetadata


@pytest_asyncio.fixture
async def dataset_model():
    return DatasetMetadata


@pytest_asyncio.fixture
async def hydroshare_resource_metadata(change_test_dir):
    with open("data/hydroshare_resource_meta.json", "r") as f:
        return json.loads(f.read())


@pytest_asyncio.fixture
async def hydroshare_collection_metadata(hydroshare_resource_metadata):
    collection_meta = hydroshare_resource_metadata.copy()
    collection_meta["type"] = "CollectionResource"
    collection_meta["content_files"] = []
    relations = [
        {
            "type": "This resource includes",
            "value": "Tarboton, D. (2019). Created from iRODS by copy from create resource page, HydroShare, http://www.hydroshare.org/resource/abba182072cc48b691ca61509019e9f8",
        },
        {
            "type": "This resource includes",
            "value": "Dash, P. (2017). Water quality sensor data from the Little Bear River at Mendon Road near Mendon, UT, HydroShare, http://www.hydroshare.org/resource/fd6f39c25ccf492992c79465a2bf0030",
        },
        {
            "type": "This resource includes",
            "value": "Gan, T. (2016). Composite Resource Type Design, HydroShare, http://www.hydroshare.org/resource/e8cd813e376347c5b617deb321227a36",
        },
        {"type": "This resource is described by", "value": "another resource"},
    ]
    collection_meta["relations"] = relations
    return collection_meta
