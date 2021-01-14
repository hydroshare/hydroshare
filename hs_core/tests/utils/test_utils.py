import pytest

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
