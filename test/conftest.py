import pytest


# @pytest.fixture(scope="session")
# def test_top_url(client):
#     response = client.get('/')
#     assert response.status_code == 200



        # self.hostname = socket.gethostname()
        # self.resource_url = "http://example.com/resource/{res_id}/"
        # self.maxDiff = None
        # self.client = APIClient()
        #
        # self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # # create a user
        # self.user = users.create_account(
        #     'test_user@email.com',
        #     username='testuser',
        #     password='foobar',
        #     first_name='some_first_name',
        #     last_name='some_last_name',
        #     superuser=False)
        #
        # self.client.force_authenticate(user=self.user)
        # self.client.login(username='testuser', password='foobar')
        #
        # self.resources_to_delete = []
        # self.groups_to_delete = []