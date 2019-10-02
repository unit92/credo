#!/usr/bin/env python3

from django.test import TestCase
from credo.models import MEI
from utils.mei.mei_transformer import MeiTransformer
from django.core.files.base import ContentFile
import re
import os

class TestMEI(TestCase):
    def setUp(self):
        ...

    def test_normalize_on_save(self):
        mei = MEI()

        with open('credo/migrations/seed_mei/diffA.mei') as f:
            content = f.read()

        mei.data.save('test_file.mei', ContentFile(content))
        mei.save()

        data = mei.data.open('r').read().decode()
        self.assertIsNone(re.search('<meiHead', data))
