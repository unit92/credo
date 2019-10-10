from lxml import etree
from xmldiff.patch import Patcher
from copy import deepcopy


class TrackedPatcher(Patcher):

    class TrackedNode:
        def __init__(self, original, modified):
            self.original = original
            self.modified = modified
            self.modifications = []

        def register_modification(self, action):
            self.modifications.append(action)

    def __init__(self):
        self.nodes = []

    def patch(self, actions, tree):

        result = deepcopy(tree)

        original_iter = tree.iter()
        result_iter = result.iter()

        # Associate each node in tree with each node in result
        while True:
            try:
                original_node = original_iter.__next__()
                result_node = result_iter.__next__()
                self.nodes.append(
                    TrackedPatcher.TrackedNode(original_node, result_node)
                )
            except StopIteration:
                break

        for action in actions:
            self.handle_action(action, result)

        return result

    def register_modification(self, action, tree, node):
        modified_nodes = [x.modified for x in self.nodes]
        if node in modified_nodes:
            i = modified_nodes.index(node)
            self.nodes[i].register_modification(action)
        else:
            modified_node = TrackedPatcher.TrackedNode(None, node)
            modified_node.register_modification(action)
            self.nodes.append(modified_node)

    def handle_action(self, action, tree):
        super().handle_action(action, tree)

    def _handle_DeleteNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.getparent().remove(node)
        self.register_modification(action, tree, node)

    def _handle_InsertNode(self, action, tree):
        target = tree.xpath(action.target)[0]
        node = target.makeelement(action.tag)
        target.insert(action.position, node)
        self.register_modification(action, tree, node)

    def _handle_RenameNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.tag = action.tag
        self.register_modification(action, tree, node)

    def _handle_MoveNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.getparent().remove(node)
        target = tree.xpath(action.target)[0]
        target.insert(action.position, node)
        self.register_modification(action, tree, node)

    def _handle_UpdateTextIn(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.text = action.text
        self.register_modification(action, tree, node)

    def _handle_UpdateTextAfter(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.tail = action.text
        self.register_modification(action, tree, node)

    def _handle_UpdateAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        # This should not be used to insert new attributes.
        assert action.name in node.attrib
        node.attrib[action.name] = action.value
        self.register_modification(action, tree, node)

    def _handle_DeleteAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        del node.attrib[action.name]
        self.register_modification(action, tree, node)

    def _handle_InsertAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        # This should not be used to update existing attributes.
        assert action.name not in node.attrib
        node.attrib[action.name] = action.value
        self.register_modification(action, tree, node)

    def _handle_RenameAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        assert action.oldname in node.attrib
        assert action.newname not in node.attrib
        node.attrib[action.newname] = node.attrib[action.oldname]
        del node.attrib[action.oldname]
        self.register_modification(action, tree, node)

    def _handle_InsertComment(self, action, tree):
        target = tree.xpath(action.target)[0]
        node = etree.Comment(action.text)
        target.insert(action.position, node)
        self.register_modification(action, tree, node)
