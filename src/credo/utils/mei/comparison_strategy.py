from abc import ABC, abstractmethod
import lxml.etree as et
from credo.models import MEI
import typing as t


class ComparisonStrategy(ABC):

    def __init__(self):
        return

    def compare_meis(self, a: MEI, b: MEI) \
            -> t.Tuple[et.ElementTree, et.ElementTree, et.ElementTree]:

        parser = et.XMLParser(remove_blank_text=True)

        with a.data.open() as f:
            tree_a = et.parse(f, parser)

        with b.data.open() as f:
            tree_b = et.parse(f, parser)

        return self.compare_trees(tree_a, tree_b)

    @abstractmethod
    def compare_trees(self, a: et.ElementTree, b: et.ElementTree) \
            -> t.Tuple[et.ElementTree, et.ElementTree, et.ElementTree]:
        pass
