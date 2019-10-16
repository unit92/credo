#!/usr/bin/env python3

import logging
import json

from django.test import TestCase, Client
from credo.models import Comment, Revision, User


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
        """Ensure revisions can be retrived at their appropriate endpoint."""
        response = self.authed_client.get('/songs/1/revisions/1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('revision.html')

    def test_save_revision_POST(self):
        """Ensure comments can be added through a POST request.

        This endpoint is used by the 'save' button on the front end.
        """

        response = self.authed_client.post(
            '/songs/1/revisions/1',
            json.dumps({
                'comments': {
                    'm-1': 'hello',
                    'm-2': 'world',
                },
                'mei': '<music xml:id="m-22"></music>'
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
        """Ensure comments cannot be added if a user is not logged in."""

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

    def test_make_revision_from_single_edition(self):
        """Verify that making a revision from a single edition works

        This makes a request to the make_revision view and asserts that a
        revision is made, and that the client is redirected to the new
        revision.
        """

        num_revisions = Revision.objects.count()

        response = self.authed_client.get('/revise?e=1')

        self.assertEquals(response.status_code, 302)
        self.assertEquals(Revision.objects.count(), num_revisions + 1)
