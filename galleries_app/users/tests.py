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


class UserTestCase(BaseTestCase):
    def testEmptyList(self):
        client = APIClient()
        result = client.get('/api-v1/users/')
        self.assertEquals(result.status_code, 200)
        self.assertEquals(len(result.data), 0)

    def testCreate(self):
        client = APIClient()
        result = client.post('/api-v1/users/', {'name': 'user1 name',
                                                'last_name': 'user1 last',
                                                'father_name': 'user1 father',
                                                'password': 'pass1',
                                                'email': 'user1@localhost'})
        self.assertEquals(result.status_code,201)
        result = client.get('/api-v1/users/')
        self.assertEquals(result.status_code,200)
        self.assertEquals(len(result.data), 1)
        result = client.post('/api-v1/users/', {'name': 'user1 name',
                                                'last_name': 'user1 last',
                                                'father_name': 'user1 father',
                                                'password': 'pass1',
                                                'email': 'user1@localhost'})
        self.assertEquals(result.status_code, 400) # Non-unique email fails with bad request
        result = client.post('/api-v1/users/', {'name': 'user2 name',
                                                'last_name': 'user1 last',
                                                'father_name': 'user1 father',
                                                'password': 'pass2',
                                                'email': 'user2@localhost'})
        self.assertEquals(result.status_code, 201)
        result = client.post('/api-v1/users/', {'name': 'user3 name',
                                                'last_name': 'user1 last',
                                                'father_name': 'user1 father',
                                                'password': 'pass3',
                                                'email': 'user3@localhost'})
        self.assertEquals(result.status_code, 201)
        result = client.get('/api-v1/users/')
        self.assertEquals(result.status_code, 200)
        self.assertEquals(len(result.data), 3)
        self.assertCollectionContains(result.data, {'name': 'user3 name',
                                                    'last_name': 'user1 last',
                                                    'father_name': 'user1 father',
                                                    'email': 'user3@localhost'})
    def testUpdate(self):
        client = APIClient()

        user1_data = {'name': 'user1 name',
                      'last_name': 'user1 last',
                      'father_name': 'user1 father',
                      'password': 'pass1',
                      'email': 'user1@localhost'}

        user2_data = {'name': 'user2 name',
                      'last_name': 'user2 last',
                      'father_name': 'user2 father',
                      'password': 'pass2',
                      'email': 'user2@localhost'}

        result = client.post('/api-v1/users/', user1_data)
        user1_id = result.data['id']

        result = client.post('/api-v1/users/', user2_data)
        user2_id = result.data['id']
        # Put (all fields)
        user1_data2 = {'name': 'user1 name updated',
                       'last_name': 'user1 last',
                       'father_name': 'user1 father',
                       # 'password': 'pass1',
                       'email': 'user1@localhost'}
        result = client.put('/api-v1/users/{}/'.format(user1_id), user1_data2)
        self.assertEquals(result.status_code, 400) # all fields are required in PUT
        user1_data2['password'] = 'pass2'
        result = client.put('/api-v1/users/{}/'.format(user1_id), user1_data2)
        self.assertEquals(result.status_code, 200)
        self.assertEqual(result.data['name'], user1_data2['name'])
        # Patch (partial)
        result = client.patch('/api-v1/users/{}/'.format(user2_id), {'email': 'user1@localhost'})
        self.assertEquals(result.status_code, 400) # integrity error
        result = client.patch('/api-v1/users/{}/'.format(user2_id), {'last_name': 'user2 updated last'})
        self.assertEquals(result.status_code, 200)
        # Check in list
        result = client.get('/api-v1/users/')
        del user1_data2['password']
        user2_data['last_name'] = 'user2 updated last'
        del user2_data['password']
        self.assertCollectionContains(result.data, user1_data2)
        self.assertCollectionContains(result.data, user2_data)
