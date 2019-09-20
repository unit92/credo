#!/usr/bin/env python3

from unittest import TestCase, main
from utils.mei.mei_transformer import MeiTransformer, ns


class TestMeiTransformer(TestCase):
    meiTransformer: MeiTransformer

    def setUp(self):
        # Set up the MEI file
        self.meiTransformer = MeiTransformer.\
            from_xml_file("./tests/utils/mei/data/test.mei")

    def test_normalise_removes_header(self):
        """
        Asserts that normalisation removes the mei head by querying the tree
        for the head before normalisation and after and asserting that it
        exists beforehand and doesn't afterwards
        """
        before = self.meiTransformer.tree.find('.//mei:meiHead', ns)
        self.meiTransformer.normalise()
        headers = self.meiTransformer.tree.find('.//mei:meiHead', ns)
        self.assertIsNotNone(before)
        self.assertIsNone(headers)
        self.assertFalse(self.meiTransformer.is_intermediate)

    def test_normalise_removes_MIDI_data(self):
        """
        Asserts that normalisation removes the midi information by querying
        the tree for the relevant tags before normalisation and after and
        asserting that it exists beforehand and doesn't afterwards
        """
        before_midi_notes = self.meiTransformer.tree.find(
            './/mei:note[@pnum]', ns)
        before_midi_instrument = self.meiTransformer.tree.find(
            './/mei:instrDef', ns)
        self.meiTransformer.normalise()
        midi_notes = self.meiTransformer.tree.find('.//mei:note[@pnum]', ns)
        midi_instrument = self.meiTransformer.tree.find('.//mei:instrDef', ns)
        self.assertIsNotNone(before_midi_notes)
        self.assertIsNotNone(before_midi_instrument)
        self.assertIsNone(midi_notes)
        self.assertIsNone(midi_instrument)
        self.assertFalse(self.meiTransformer.is_intermediate)

    def test_is_intermediate(self):
        """
        Tests various cases that the is_intermediate property works as expected
        even if it is constructed from another tree
        """
        self.assertFalse(self.meiTransformer.is_intermediate)
        self.meiTransformer.normalise()
        self.assertFalse(self.meiTransformer.is_intermediate)
        self.meiTransformer.to_intermediate()
        self.assertTrue(self.meiTransformer.is_intermediate)
        self.meiTransformer.to_plain_mei()
        self.assertFalse(self.meiTransformer.is_intermediate)
        self.meiTransformer.to_intermediate()
        mt1 = MeiTransformer(self.meiTransformer.tree)
        self.assertTrue(self.meiTransformer.is_intermediate)
        self.assertTrue(mt1.is_intermediate)
        mt1.to_plain_mei()
        self.assertTrue(self.meiTransformer.is_intermediate)
        self.assertFalse(mt1.is_intermediate)

    def test_property_tree_returns_copy(self):
        """
        Asserts that the tree returned from MeiTransformer.tree is a copy and
        not the original tree
        """
        self.assertIsNot(self.meiTransformer.tree, self.meiTransformer.tree)
        self.assertIs(self.meiTransformer._tree, self.meiTransformer._tree)


if __name__ == '__main__':
    main()
