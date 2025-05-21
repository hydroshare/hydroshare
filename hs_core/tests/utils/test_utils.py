from time import sleep
import pytest
import sys
import pdb
import functools
import traceback

from hs_core.hydroshare.utils import encode_resource_url, decode_resource_url


@pytest.mark.parametrize("decoded_url,encoded_url", [
    ("https://www.hydroshare.org/oh look/ a/ space /weird names.txt",
     "https://www.hydroshare.org/oh%20look/%20a/%20space%20/weird%20names.txt"),
    ("https://www.hydroshare.org/data/contents/just file.txt",
     "https://www.hydroshare.org/data/contents/just%20file.txt"),
    ("https://www.hydroshare.org/data/contents/just folder/",
     "https://www.hydroshare.org/data/contents/just%20folder/"),
    ("https://www.hydroshare.org/data/contents/just folder/file.txt",
     "https://www.hydroshare.org/data/contents/just%20folder/file.txt")
])
def test_encode_decode_resource_url(decoded_url, encoded_url):
    """
    Tests the encode/decode url functions work correctly
    """
    assert encode_resource_url(decoded_url) == encoded_url
    assert decode_resource_url(encoded_url) == decoded_url


def debug_on(*exceptions):
    """Utility decorator for debugging within unittest runs

    Returns:
        decorator: To decorate unittest functions
    """
    if not exceptions:
        exceptions = (AssertionError, )

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                info = sys.exc_info()
                traceback.print_exception(*info)
                pdb.post_mortem(info[2])
        return wrapper
    return decorator


def set_quota_usage_over_hard_limit(uquota):
    uquota.save_allocated_value(1, "B")
    sleep(30)


def wait_for_quota_update():
    sleep(30)
