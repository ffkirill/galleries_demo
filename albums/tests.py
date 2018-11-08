import os
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient
from sa_helper import Session

@override_settings(SA_DATABASE_URL = 'sqlite:///test.db')
class BaseTestCase(SimpleTestCase):

    def setUp(self):
        from sa_helper.management.commands.create_schema import Command
        try:
            os.remove(os.path.join(settings.BASE_DIR, 'test.db'))
        except:
            pass
        Command().handle()

    def tearDown(self):
        session = Session()
        session.close_all()
        os.remove(os.path.join(settings.BASE_DIR, 'test.db'))

    def assertCollectionContains(self, collection, elem):
        found = False
        for guess in collection:
            cnt = 0
            for k, v in elem.items():
                if guess[k] == elem[k]:
                    cnt+=1
            if cnt == len(elem):
                found = True
                break
        self.assertTrue(found, 'Collection {} has no {} element'.format(collection, elem))


class AlbumTestCase(BaseTestCase):
    user1_id = None
    user2_id = None
    session1_key = None
    session2_key = None

    def setUp(self):
        super().setUp()
        client = APIClient()
        result = client.post('/api-v1/users/', {'name': 'user1 name',
                                                'last_name': 'user1 last',
                                                'father_name': 'user1 father',
                                                'password': 'pass1',
                                                'email': 'user1@localhost'})
        self.user1_id = result.data['id']
        result = client.post('/api-v1/users/', {'name': 'user2 name',
                                                'last_name': 'user2 last',
                                                'father_name': 'user2 father',
                                                'password': 'pass2',
                                                'email': 'user2@localhost'})
        self.user2_id = result.data['id']
        result = client.post('/api-v1/auth/', {'email': 'user1@localhost',
                                               'password': 'pass1'})
        self.session1_key = result.data['session_key']
        result = client.post('/api-v1/auth/', {'email': 'user2@localhost',
                                               'password': 'pass2'})
        self.session2_key = result.data['session_key']

    def testEmpty(self):
        client = APIClient()

        result = client.get('/api-v1/albums/')
        self.assertEquals(result.status_code, 403)

        result = client.get('/api-v1/albums/?session_key={}'.format(self.session1_key))
        self.assertEquals(result.status_code, 200)
        self.assertEquals(len(result.data), 0)

    def testCreateRetrieveDelete(self):
        album = {'name': 'album1', 'description': ''}
        client = APIClient()

        result = client.post('/api-v1/albums/', album)
        self.assertEquals(result.status_code, 403)

        result = client.post('/api-v1/albums/?session_key={}'.format(self.session1_key), album)
        album1_id = result.data['id']

        self.assertEquals(result.status_code, 201)

        result = client.get('/api-v1/albums/?session_key={}'.format(self.session1_key))
        self.assertEquals(result.status_code, 200)

        self.assertCollectionContains(result.data, album)

        result = client.get('/api-v1/albums/{}/?session_key={}'.format(album1_id,
                                                                       self.session1_key))
        self.assertEquals(result.status_code, 200)

        result = client.get('/api-v1/albums/{}/?session_key={}'.format(album1_id,
                                                                       self.session2_key))
        self.assertEquals(result.status_code, 404)

        result = client.get('/api-v1/albums/?session_key={}'.format(self.session2_key))
        self.assertEquals(result.status_code, 200)
        self.assertEquals(len(result.data), 0)

        result = client.delete('/api-v1/albums/{}/?session_key={}'.format(album1_id,
                                                                       self.session2_key))
        self.assertEquals(result.status_code, 404)

        result = client.delete('/api-v1/albums/{}/?session_key={}'.format(album1_id,
                                                                          self.session1_key))
        self.assertEquals(result.status_code, 204)

        result = client.get('/api-v1/albums/?session_key={}'.format(self.session1_key))
        self.assertEquals(result.status_code, 200)
        self.assertEquals(len(result.data), 0)