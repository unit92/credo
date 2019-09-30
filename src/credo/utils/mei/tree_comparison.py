from xmldiff import main, actions
import lxml.etree as et
import typing as t
from pprint import pprint
from copy import deepcopy

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
    INSERT_COLOR = 'hsl(95, 100%, 42%)'

    def __init__(self):
        return

    def compare_trees(self, a: et.ElementTree, b: et.ElementTree) \
            -> t.Tuple[et.ElementTree, et.ElementTree, et.ElementTree]:

        a_transformer = MeiTransformer(a)
        b_transformer = MeiTransformer(b)

        a_transformer.to_intermediate()
        b_transformer.to_intermediate()

        diff = self.__get_diff_tree(a_transformer.tree, b_transformer.tree)

        diff_transformer = MeiTransformer(diff)

        diff_transformer.to_plain_mei()
        a_transformer.to_plain_mei()
        b_transformer.to_plain_mei()

        diff_transformer.generate_ids(keep_existing=True)
        a_transformer.generate_ids(keep_existing=False)
        b_transformer.generate_ids(keep_existing=False)

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
        a_modded = deepcopy(a)
        b_modded = patcher.patch(diff_actions, a_modded)

        # Make all nodes in b_modded invisible by default
        # to avoid visual layer clashes
        class_lookup = et.ElementDefaultClassLookup()
        for elem in b_modded.iter():
            # Ensure element can have attributes
            if (not isinstance(elem, class_lookup.comment_class) and
                    not isinstance(elem, class_lookup.entity_class)):
                elem.set('visible', 'false')

        action_classes = {
            'insert': [
                actions.InsertNode,
                actions.InsertComment
            ],
            'delete': [
                actions.DeleteNode
            ],
            'update': [
                actions.RenameNode,
                actions.MoveNode,
                actions.UpdateTextIn,
                actions.UpdateTextAfter,
                actions.UpdateAttrib,
                actions.DeleteAttrib,
                actions.InsertAttrib,
                actions.RenameAttrib
            ]
        }

        # Apply colours to modified nodes in a_modded and b_modded trees
        for node in patcher.nodes:
            if len(node.modifications) > 0:
                print()
                print('Original:', node.original)
                print('Modified:', node.modified)
                pprint(node.modifications)
                mod = node.modifications[0]
                if type(mod) in action_classes['insert']:
                    # Set colours in b_modded
                    node.modified.set('color', TreeComparison.INSERT_COLOR)
                    node.modified.set('visible', 'true')
                elif type(mod) in action_classes['delete']:
                    # Set colours in a_modded
                    node.original.set('color', TreeComparison.DELETE_COLOR)
                elif type(mod) in action_classes['update']:
                    # Set colours in b_modded
                    node.modified.set('color', TreeComparison.B_COLOR)
                    node.modified.set('visible', 'true')
                    # Set colours in a_modded
                    node.original.set('color', TreeComparison.A_COLOR)

        # Merge a_modded and b_modded into a single diff tree
        diff = self.__naive_layer_merge(a_modded, b_modded)

        print()
        print()

        print('A:\n', et.tostring(a, pretty_print=True).decode(), '\n')
        print('B:\n', et.tostring(b, pretty_print=True).decode(), '\n')
        print(
            'A Modded:\n',
            et.tostring(a_modded, pretty_print=True).decode(),
            '\n'
        )
        print(
            'B Modded:\n',
            et.tostring(b_modded, pretty_print=True).decode(),
            '\n'
        )

        print(
            'Diff:\n',
            et.tostring(diff, pretty_print=True).decode(),
            '\n'
        )

        return diff

    def __naive_layer_merge(self, a: et.ElementTree, b: et.ElementTree) \
            -> et.ElementTree:

        base = deepcopy(a)
        insert = b
        base_id_prefix = 'a'
        insert_id_prefix = 'b'

        bar_qry = et.XPath('//mei:measure', namespaces=self.ns)
        base_bars = bar_qry(base)
        insert_bars = bar_qry(insert)

        # Loop through all bars in the piece
        id_idx = 0
        bar_idx = 0
        while bar_idx < min(len(base_bars), len(insert_bars)):  # TODO Rethink
            base_bar = base_bars[bar_idx]
            insert_bar = insert_bars[bar_idx]

            # Loop through each staff in the bar
            staff_qry = et.XPath('child::mei:staff', namespaces=self.ns)
            base_staffs = staff_qry(base_bar)
            insert_staffs = staff_qry(insert_bar)

            if len(base_staffs) != len(insert_staffs):
                raise ValueError(
                    'Unequal staff count in bar {}'.format(bar_idx)
                )

            staff_idx = 0
            while staff_idx < len(base_staffs):
                base_staff = base_staffs[staff_idx]
                insert_staff = insert_staffs[staff_idx]

                # Loop through each layer in the staff

                layer_qry = et.XPath('child::mei:layer', namespaces=self.ns)
                base_layers = layer_qry(base_staff)
                insert_layers = layer_qry(insert_staff)

                if len(base_layers) != len(insert_layers):
                    raise ValueError(
                        'Unequal layer count in staff {}, bar {}'.format(
                            staff_idx,
                            bar_idx
                        )
                    )

                id_attrib = et.QName(self.ns['xml'], 'id')

                layer_idx = 0
                while layer_idx < len(base_layers):
                    base_layer = base_layers[layer_idx]
                    insert_layer = deepcopy(insert_layers[layer_idx])

                    base_layer.set(
                        id_attrib.text,
                        base_id_prefix + str(id_idx)
                    )

                    insert_layer.set(
                        id_attrib.text,
                        insert_id_prefix + str(id_idx)
                    )
                    # Update n tag on layer to allow trills to connect properly
                    insert_layer.set(
                        'n',
                        str(len(base_layers) + layer_idx + 1)
                    )

                    id_idx += 1
                    base_staff.append(insert_layer)
                    layer_idx += 1

                staff_idx += 1

            # TODO Merge trills

            bar_idx += 1

        return base

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
