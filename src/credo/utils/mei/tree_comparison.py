from .comparison_strategy import ComparisonStrategy
import lxml.etree as et


class TreeComparison(ComparisonStrategy):

    def __init__(self):
        return

    def compare_trees(self, a: et.ElementTree, b: et.ElementTree) -> tuple:

        a = self.strip_tree(a)
        b = self.strip_tree(b)

        # TODO actual diff algorithm here
        diff = a
        return diff, a, b

    def strip_tree(self, t: et.ElementTree) -> et.ElementTree:
        # TODO Call Joel's intermediate MEI format functions here
        return t
