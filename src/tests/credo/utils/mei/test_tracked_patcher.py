from unittest import TestCase, main, skip
from xmldiff import main as xmldiff_main

from credo.utils.mei.tracked_patcher import TrackedPatcher
from utils.mei.mei_transformer import MeiTransformer


class TestTrackedPatcher(TestCase):

    def setUp(self):
        mei_transformer_a = MeiTransformer.from_xml_file(
            './tests/credo/utils/mei/data/test_a.mei'
        )
        mei_transformer_b = MeiTransformer.from_xml_file(
            './tests/credo/utils/mei/data/test_b.mei'
        )
        mei_transformer_a.normalise()
        mei_transformer_b.normalise()

        mei_transformer_a.to_intermediate()
        mei_transformer_b.to_intermediate()

        self.tree_a = mei_transformer_a.tree
        self.tree_b = mei_transformer_b.tree

        self.diff_actions = xmldiff_main.diff_trees(
            self.tree_a,
            self.tree_b,
            diff_options={
                'F': 0.5,
                'ratio_mode': 'fast',
                'uniqueattrs': []  # Ignore xml:id attributes
            }
        )

    @skip('No current method of determining tree equality')
    def test_tree_recovery(self):
        """Ensure the patcher reconstructs the second tree using the diff."""

        patcher = TrackedPatcher()
        result = patcher.patch(self.diff_actions, self.tree_a)
        # TODO Implement a method of determining tree equality
        self.assertEqual(result, self.tree_b)
        self.assertIsNot(result, self.tree_b)


if __name__ == '__main__':
    main()
