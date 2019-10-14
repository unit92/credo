from unittest import TestCase, main
from credo.utils.mei.comparison_strategy import ComparisonStrategy


class TestComparisonStrategy(TestCase):

    def setUp(self):
        return

    def test_is_abstract(self):
        """Ensure the ComparisonStrategy class is abstract

        Assert that trying to create an instance of the ComparisonStrategy
        class raises an error.
        """
        with self.assertRaises(TypeError):
            ComparisonStrategy()


if __name__ == '__main__':
    main()
