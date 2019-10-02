#!/usr/bin/env python3

import logging
import json

from django.test import TestCase, Client
from credo.models import User, Comment

class TestServerBlackBox(TestCase):
    def setUp(self):
        logging.basicConfig(filename='/tmp/credo-test.log')
        self.logger = logging.getLogger(__name__)

        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

        self.authed_client = Client()
        self.authed_client.login(username='testuser', password='12345')
        self.client = Client()

    def test_revision_GET(self):
        response = self.authed_client.get('/songs/1/revisions/1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('revision.html')

    def test_save_revision_POST(self):
        '''Tests adding of comments through the 'save' button'''
        response = self.authed_client.post(
            '/songs/1/revisions/1',
            json.dumps({
                'comments': {
                    'm-1': 'hello',
                    'm-2': 'world',
                }
            }),
            content_type='application/json'
        )

        # Did the server accept the request?
        self.assertEqual(response.status_code, 200)

        # Did it return the correct JSON?
        self.assertEqual(response.json(), {'ok': True}, response.json())

        # Were the comments created?
        self.assertTrue(
            Comment.objects.filter(revision_id=1,
                                   text='hello',
                                   mei_element_id='m-1').exists()
        )

        self.assertTrue(
            Comment.objects.filter(revision_id=1,
                                   text='world',
                                   mei_element_id='m-2').exists()
        )

    def test_save_revision_auth(self):
        response = self.client.post(
            '/songs/1/revisions/1',
            json.dumps({
                'comments': {
                    'm-1': 'hello',
                    'm-2': 'world',
                }
            }),
            content_type='application/json'
        )
        self.assertEquals(response.status_code, 403)
