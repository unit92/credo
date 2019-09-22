from xmldiff import main
import lxml.etree as et
import typing as t

from .comparison_strategy import ComparisonStrategy
from .tracked_patcher import TrackedPatcher
from utils.mei.mei_transformer import MeiTransformer


# Preconditions for MEI files
# - The file is actually an MEI, not just XML that uses MEI tags
# - MEI must have been normalised first
# - The ElementTrees don't contain any text nodes.
#   this can be achieved when parsing.
# - <note> tags must be contained within a <layer> tag (Enforced by MEI)

class TreeComparison(ComparisonStrategy):

    # Shorthand XML namespaces
    ns = {
        'xml': 'http://www.w3.org/XML/1998/namespace',
        'mei': 'http://www.music-encoding.org/ns/mei',
        'xlink': 'http://www.w3.org/1999/xlink'
    }

    A_COLOR = 'hsl(195, 100%, 47%)'
    B_COLOR = 'hsl(274, 100%, 56%)'
    DELETE_COLOR = 'hsl(12, 100%, 53%)'
    INSERT_COLOR = 'hsl(12, 100%, 53%)'

    def __init__(self):
        return

    def compare_trees(self, a: et.ElementTree, b: et.ElementTree) \
            -> t.Tuple[et.ElementTree, et.ElementTree, et.ElementTree]:

        a_transformer = MeiTransformer(a)
        b_transformer = MeiTransformer(b)

        a_transformer.normalise()  # TODO Normalise on add to database instead
        b_transformer.normalise()  # TODO Normalise on add to database instead

        a_transformer.to_intermediate()
        b_transformer.to_intermediate()

        diff = self.__get_diff_tree(a_transformer.tree, b_transformer.tree)

        diff_transformer = MeiTransformer(diff)

        diff_transformer.to_plain_mei()
        a_transformer.to_plain_mei()
        b_transformer.to_plain_mei()

        return diff_transformer.tree, a_transformer.tree, b_transformer.tree

    def __get_diff_tree(self, a: et.ElementTree, b: et.ElementTree, ):
        # Get a list of actions to apply to tree a that
        # when applied transform it into tree b
        diff_actions = main.diff_trees(
            a,
            b,
            diff_options={
                'F': 0.5,
                'ratio_mode': 'accurate',
                'uniqueattrs': []  # Ignore xml:id attributes
            }
        )

        patcher = TrackedPatcher()
        diff = patcher.patch(diff_actions, a, copy=True)

        print('A:\n', et.tostring(a, pretty_print=True).decode(), '\n')
        print('B:\n', et.tostring(b, pretty_print=True).decode(), '\n')
        print('Diff:\n', et.tostring(diff, pretty_print=True).decode(), '\n')

        return diff

    # def __get_diff_layers(self, diff: et.ElementTree, layer_id: str):
    #     # Find the corresponding layer in the diff tree
    #     diff_layer_query = et.XPath(
    #         '//mei:layer[@xml:id={}]'.format(layer_id),
    #         namespaces=TreeComparison.ns
    #     )
    #     diff_common_layer = diff_layer_query(diff)[0]

    #     # Check for existing sibling layers describing content specific to
    #     # the a and b trees
    #     layer_qry_str = 'following-sibling::mei:layer[@xml:id=$layer_id]|\
    #         preceding-sibling::mei:layer[@xml:id=$layer_id]'

    #     layer_id_suffixes = ['a', 'b']

    #     diff_a_layer = diff_common_layer.xpath(
    #         layer_qry_str,
    #         namespaces=TreeComparison.ns,
    #         layer_id=layer_id + layer_id_suffixes[0]
    #     )
    #     diff_b_layer = diff_common_layer.xpath(
    #         layer_qry_str,
    #         namespaces=TreeComparison.ns,
    #         layer_id=layer_id + layer_id_suffixes[1]
    #     )
    #     layers = [diff_a_layer, diff_b_layer]

    #     # Create layers for storing content specific to
    #     # the a and b trees if not already created
    #     XML_ID = et.QName(TreeComparison.ns['xml'], 'id')

    #     i = 0
    #     for i in range(len(layers)):
    #         if len(layers[i]) == 0:
    #             layers[i] = deepcopy(diff_common_layer)
    #             layers[i].set(
    #                 XML_ID.text,
    #                 '{}{}'.format(layer_id, layer_id_suffixes[i])
    #             )
    #             for elem in layers[i].iter():
    #                 elem.set('visible', 'false')
    #             diff_common_layer.getparent().append(layers[i])
    #         else:
    #             layers[i] = layers[i][0]
    #         i += 1
    #     layers.insert(0, diff_common_layer)
    #     return layers

    # def __get_containing_layer(self, node: et.Element):

    #     layer_query = et.XPath(
    #         'ancestor::mei:layer',
    #         namespaces=TreeComparison.ns
    #     )
    #     #There will only ever be one containing layer per node in a valid MEI
    #     containing_layer = layer_query(node)
    #     return containing_layer[0]

    # def __pad_after_node(self, node: et.Element, duration: float):
    #     parent = node.getparent()
    #     if len(parent) == 0:
    #         raise ValueError('Supplied node must have a parent element.')
    #     idx = parent.index(node)
    #     print(idx)

    #     pad_elem = et.SubElement(parent, 'space')
    #     pad_elem.set('dur', str(int(1/duration)))

    #     parent.insert(idx + 1, pad_elem)

    # def __process_update(
    #         self,
    #         diff: et.ElementTree,
    #         a: et.ElementTree,
    #         b: et.ElementTree,
    #         action: actions.UpdateAttrib,
    #         a_color=A_COLOR,
    #         b_color=B_COLOR):

    #     # Define tags supported by this action
    #     supported_tags = (et.QName(TreeComparison.ns['mei'], 'note'),)
    #     supported_tags = [tag.text for tag in supported_tags]

    #     node_query = et.XPath(action.node)

    #     XML_ID = et.QName(TreeComparison.ns['xml'], 'id')

    #     # Query returns list, just want the first element (single node)
    #     nodes = node_query(a)
    #     if len(nodes) != 1:
    #         return
    #     node = nodes[0]
    #     node_id = node.get(XML_ID.text)

    #     if node.tag in supported_tags:

    #         containing_layer = self.__get_containing_layer(node)
    #         containing_layer_id = containing_layer.get(XML_ID.text)

    #         layers = self.__get_diff_layers(diff, containing_layer_id)
    #         common_layer, a_layer, b_layer = layers

    #         diff_node_query = et.XPath(
    #             'descendant::*[@xml:id={}]'.format(node_id),
    #             namespaces=TreeComparison.ns
    #         )
    #         diff_common_node = diff_node_query(common_layer)[0]
    #         diff_a_node = diff_node_query(a_layer)[0]
    #         diff_b_node = diff_node_query(b_layer)[0]

    #         # TODO Think about spacing when updated attribute
    #         # is dur or dots attribute. Group actions?

    #         # Apply attribute update to b
    #         if isinstance(action, actions.DeleteAttrib):
    #             diff_b_node.attrib.pop(action.name)
    #         else:
    #             diff_b_node.set(action.name, action.value)

    #         # Change colors
    #         if action.name != XML_ID:
    #             # Update implies the change is not common to
    #             # source a and b, hence make this node invisible.
    #             diff_common_node.set('visible', 'false')
    #             diff_a_node.set('color', a_color)
    #             diff_a_node.set('visible', 'true')
    #             diff_b_node.set('color', b_color)
    #             diff_b_node.set('visible', 'true')

    # def __process_insertion(
    #         self,
    #         diff: et.ElementTree,
    #         a: et.ElementTree,
    #         b: et.ElementTree,
    #         action: actions.InsertNode,
    #         a_color=A_COLOR,
    #         b_color=B_COLOR):
    #     return

    # def __process_deletion(
    #         self,
    #         diff: et.ElementTree,
    #         a: et.ElementTree,
    #         b: et.ElementTree,
    #         action: actions.DeleteNode,
    #         a_color=A_COLOR,
    #         b_color=B_COLOR):

    #     # Define tags supported by this action
    #     supported_tags = (et.QName(TreeComparison.ns['mei'], 'note'),)
    #     supported_tags = [tag.text for tag in supported_tags]

    #     node_query = et.XPath(action.node)

    #     XML_ID = et.QName(TreeComparison.ns['xml'], 'id')

    #     # Query returns list, just want the first element (single node)
    #     nodes = node_query(a)
    #     if len(nodes) != 1:
    #         return
    #     node = nodes[0]
    #     node_id = node.get(XML_ID.text)

    #     if node.tag in supported_tags:

    #         containing_layer = self.__get_containing_layer(node)
    #         containing_layer_id = containing_layer.get(XML_ID.text)

    #         layers = self.__get_diff_layers(diff, containing_layer_id)
    #         common_layer, a_layer, b_layer = layers

    #         diff_node_query = et.XPath(
    #             'descendant::*[@xml:id={}]'.format(node_id),
    #             namespaces=TreeComparison.ns
    #         )
    #         diff_common_node = diff_node_query(common_layer)[0]
    #         diff_a_node = diff_node_query(a_layer)[0]
    #         diff_b_node = diff_node_query(b_layer)[0]

    #         # Update implies the change is not common to source a and b
    #         # hence make this node invisible
    #         diff_common_node.set('visible', 'false')

    #         diff_a_node.set('color', a_color)
    #         diff_a_node.set('visible', 'true')

    #         # Apply update to b
    #         b_layer.remove(diff_b_node)
