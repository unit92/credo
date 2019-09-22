from lxml import etree
from xmldiff.patch import Patcher
from copy import deepcopy


class TrackedPatcher(Patcher):

    class ModifiedNode:
        def __init__(self, node):
            self.node = node
            self.modifications = []

        def register_modification(self, action):
            self.modifications.append(action)

    def __init__(self):
        self.modfications = []

    def patch(self, actions, tree, copy=True):
        result = deepcopy(tree) if copy else tree

        for action in actions:
            print(action)
            self.handle_action(action, result)

        for mod in self.modfications:
            print(mod.node, mod.modifications)

        return result

    def register_action(self, action, tree, node):
        modified_nodes = [x.node for x in self.modfications]
        if node in modified_nodes:
            i = modified_nodes.index(node)
            self.modfications[i].register_modification(action)
        else:
            modified_node = TrackedPatcher.ModifiedNode(node)
            modified_node.register_modification(action)
            self.modfications.append(modified_node)

    def handle_action(self, action, tree):
        super().handle_action(action, tree)

    def _handle_DeleteNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.getparent().remove(node)
        self.register_action(action, tree, node)

    def _handle_InsertNode(self, action, tree):
        target = tree.xpath(action.target)[0]
        node = target.makeelement(action.tag)
        target.insert(action.position, node)
        self.register_action(action, tree, node)

    def _handle_RenameNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.tag = action.tag
        self.register_action(action, tree, node)

    def _handle_MoveNode(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.getparent().remove(node)
        target = tree.xpath(action.target)[0]
        target.insert(action.position, node)
        self.register_action(action, tree, node)

    def _handle_UpdateTextIn(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.text = action.text
        self.register_action(action, tree, node)

    def _handle_UpdateTextAfter(self, action, tree):
        node = tree.xpath(action.node)[0]
        node.tail = action.text
        self.register_action(action, tree, node)

    def _handle_UpdateAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        # This should not be used to insert new attributes.
        assert action.name in node.attrib
        node.attrib[action.name] = action.value
        self.register_action(action, tree, node)

    def _handle_DeleteAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        del node.attrib[action.name]
        self.register_action(action, tree, node)

    def _handle_InsertAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        # This should not be used to update existing attributes.
        assert action.name not in node.attrib
        node.attrib[action.name] = action.value
        self.register_action(action, tree, node)

    def _handle_RenameAttrib(self, action, tree):
        node = tree.xpath(action.node)[0]
        assert action.oldname in node.attrib
        assert action.newname not in node.attrib
        node.attrib[action.newname] = node.attrib[action.oldname]
        del node.attrib[action.oldname]
        self.register_action(action, tree, node)

    def _handle_InsertComment(self, action, tree):
        target = tree.xpath(action.target)[0]
        node = etree.Comment(action.text)
        target.insert(action.position, node)
        self.register_action(action, tree, node)
