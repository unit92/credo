#!/usr/bin/env python3

import logging
import json

from django.test import TestCase, Client
from django.core.files.base import ContentFile
from credo.models import Comment, Revision, User, Edition, Composer, Song, MEI


class TestServerBlackBox(TestCase):
    def setUp(self):
        logging.basicConfig(filename='/tmp/credo-test.log')
        self.logger = logging.getLogger(__name__)

        self.user = User(username='testuser')
        self.user.set_password('12345')
        self.user.save()

        unowned_user = User(username='unowned')
        unowned_user.save()

        self.authed_client = Client()
        self.authed_client.login(username='testuser', password='12345')
        self.client = Client()

        # Create test data
        self.composer = Composer(name="Test Composer")
        self.song = Song(name="Test Song", composer=self.composer)

        self.composer.save()
        self.song.save()

        with open("tests/credo/utils/mei/data/test_a.mei") as f:
            self.mei = MEI()
            self.mei.data.save('test', ContentFile(f.read()))

        self.mei.save()

        self.edition = Edition(
            name="Test Edition Owned",
            song=self.song,
            mei=self.mei,
            uploader=self.user
        )

        self.edition.save()

        self.revision_owned = Revision(
            name="Test Revision Owned",
            user=self.user,
            mei=self.mei
        )
        self.revision_unowned = Revision(
            name="Test Revision Unowned",
            user=unowned_user,
            mei=self.mei
        )

        self.revision_owned.save()
        self.revision_unowned.save()

        self.revision_owned.editions.add(self.edition)
        self.revision_unowned.editions.add(self.edition)

    def test_revision_GET(self):
        """Ensure revisions can be retrived at their appropriate endpoint."""
        response = self.authed_client.get('/revisions/1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('revision.html')

    def test_save_revision_POST(self):
        """Ensure comments can be added through a POST request.

        This endpoint is used by the 'save' button on the front end.
        """

        response = self.authed_client.post(
            '/revisions/1',
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
            '/revisions/1',
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

    def test_download_edition(self):
        # Unauthed user => 403
        response = self.client.get(f'/editions/{self.edition.id}/download')
        self.assertEquals(response.status_code, 403)

        # Authed user => 200
        response = self.authed_client.get(
            f'/editions/{self.edition.id}/download'
        )
        self.assertEquals(response.status_code, 200)

    def test_download_revision(self):
        # Unauthed user => 403
        response = self.client.get(
            f'/revisions/{self.revision_owned.id}/download'
        )
        self.assertEquals(response.status_code, 403)

        # Authed user, unowned revision => 403
        response = self.authed_client.get(
            f'/revisions/{self.revision_unowned.id}/download'
        )
        self.assertEquals(response.status_code, 403)

        # Authed user, owned revision => 200
        response = self.authed_client.get(
            f'/revisions/{self.revision_owned.id}/download'
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/xml')
