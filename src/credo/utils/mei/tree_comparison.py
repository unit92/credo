from xmldiff import main, actions
import lxml.etree as et
import typing as t
from pprint import pformat
from copy import deepcopy
import logging
from colorsys import rgb_to_hls

from .comparison_strategy import ComparisonStrategy
from .tracked_patcher import TrackedPatcher
from utils.mei.mei_transformer import MeiTransformer
from utils.mei.xml_namespaces import MEI_NS
from utils.mei.id_formatters import get_formatted_xml_id


class TreeComparison(ComparisonStrategy):

    DEFAULT_A_RGB = (0.400, 0.702, 1.000)
    DEFAULT_B_RGB = (1.000, 0.400, 0.529)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.set_colours(
            TreeComparison.DEFAULT_A_RGB,
            TreeComparison.DEFAULT_B_RGB
        )

    def set_colours(
            self,
            a_rgb: t.Tuple[float, float, float],
            b_rgb: t.Tuple[float, float, float]):

        try:
            self.a_colour_hls = rgb_to_hls(a_rgb[0], a_rgb[1], a_rgb[2])
            self.b_colour_hls = rgb_to_hls(b_rgb[0], b_rgb[1], b_rgb[2])
        except ValueError:
            self.a_colour_hls = rgb_to_hls(TreeComparison.DEFAULT_A_RGB)
            self.b_colour_hls = rgb_to_hls(TreeComparison.DEFAULT_B_RGB)

        self.a_colour_str = 'hsl({}, {}%, {}%)'.format(
            int(self.a_colour_hls[0]*360),
            int(self.a_colour_hls[2]*100),
            int(self.a_colour_hls[1]*100)
        )
        self.b_colour_str = 'hsl({}, {}%, {}%)'.format(
            int(self.b_colour_hls[0]*360),
            int(self.b_colour_hls[2]*100),
            int(self.b_colour_hls[1]*100)
        )

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

        # Make all nodes in b_modded invisible by default, except for layers.
        # to avoid visual layer clashes
        class_lookup = et.ElementDefaultClassLookup()
        for elem in b_modded.iter():
            # Ensure element can have attributes
            if (not isinstance(elem, class_lookup.comment_class) and
                    not isinstance(elem, class_lookup.entity_class)):
                elem.set('visible', 'false')

        # Set all layers to be visible
        for elem in b_modded.findall('//mei:layer', MEI_NS):
            elem.set('visible', 'true')

        # Apply colours to modified nodes in a_modded and b_modded trees
        node_groups = ['chord', 'beam']
        for node in patcher.nodes:
            if len(node.modifications) > 0:
                self.logger.debug('\nOriginal: {}\nModified: {}\n{}\n'.format(
                    node.original,
                    node.modified,
                    pformat(node.modifications)
                ))
                mod = node.modifications[0]
                if type(mod) in action_classes['insert']:
                    # Set colours in b_modded
                    node.modified.set('color', self.b_colour_str)
                    node.modified.set('visible', 'true')
                    # If the modified node is in a chord or beam, mark all
                    # elements in the chord/beam as modified as well.
                    self.__apply_color_to_group(
                        node.modified,
                        node_groups,
                        self.b_colour_str
                    )

                elif type(mod) in action_classes['delete']:
                    # Set colours in a_modded
                    node.original.set('color', self.a_colour_str)
                    self.__apply_color_to_group(
                        node.original,
                        node_groups,
                        self.a_colour_str
                    )
                elif type(mod) in action_classes['update']:
                    # Set colours in b_modded
                    node.modified.set('color', self.b_colour_str)
                    node.modified.set('visible', 'true')
                    # If the modified node is in a chord or beam, mark all
                    # elements in the chord/beam as modified as well.
                    self.__apply_color_to_group(
                        node.modified,
                        node_groups,
                        self.b_colour_str
                    )
                    # Set colours in a_modded
                    node.original.set('color', self.a_colour_str)
                    self.__apply_color_to_group(
                        node.original,
                        node_groups,
                        self.a_colour_str
                    )

        # Merge a_modded and b_modded into a single diff tree
        diff = self.__naive_layer_merge(a_modded, b_modded)

        self.logger.debug('\n{}:\n{}\n'.format(
            'A Original',
            et.tostring(a, pretty_print=True).decode()
        ))

        self.logger.debug('\n{}:\n{}\n'.format(
            'B Original',
            et.tostring(b, pretty_print=True).decode()
        ))

        self.logger.debug('\n{}:\n{}\n'.format(
            'A Modded',
            et.tostring(a_modded, pretty_print=True).decode()
        ))

        self.logger.debug('\n{}:\n{}\n'.format(
            'B Modded',
            et.tostring(b_modded, pretty_print=True).decode()
        ))

        self.logger.debug('\n{}:\n{}\n'.format(
            'Difference',
            et.tostring(diff, pretty_print=True).decode()
        ))

        # TEMPORARY: Strip all trill tags from the diff
        # TODO: Resolve trill IDs in __naive_layer_merge
        for elem in diff.findall('//mei:trill', MEI_NS):
            elem.getparent().remove(elem)

        return diff

    def __apply_color_to_group(self, node, group_tags, colour):
        for g in group_tags:
            g_qry = et.XPath(
                f'ancestor-or-self::mei:{g}',
                namespaces=MEI_NS
            )
            groups = g_qry(node)
            if len(groups) > 0:
                for elem in groups[0].iter():
                    elem.set('color', colour)
                    elem.set('visible', 'true')

    def __naive_layer_merge(self, a: et.ElementTree, b: et.ElementTree) \
            -> et.ElementTree:

        base = deepcopy(a)
        insert = b
        base_id_prefix = 'a'
        insert_id_prefix = 'b'

        bar_qry = et.XPath('//mei:measure', namespaces=MEI_NS)
        base_bars = bar_qry(base)
        insert_bars = bar_qry(insert)

        # Loop through all bars in the piece
        id_idx = 0
        bar_idx = 0
        while bar_idx < min(len(base_bars), len(insert_bars)):  # TODO Rethink
            base_bar = base_bars[bar_idx]
            insert_bar = insert_bars[bar_idx]

            # Loop through each staff in the bar
            staff_qry = et.XPath('child::mei:staff', namespaces=MEI_NS)
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
                layer_qry = et.XPath('child::mei:layer', namespaces=MEI_NS)
                base_layers = layer_qry(base_staff)
                insert_layers = layer_qry(insert_staff)

                if len(base_layers) != len(insert_layers):
                    raise ValueError(
                        'Unequal layer count in staff {}, bar {}'.format(
                            staff_idx,
                            bar_idx
                        )
                    )

                id_attrib = et.QName(MEI_NS['xml'], 'id')

                layer_idx = 0
                while layer_idx < len(base_layers):
                    base_layer = base_layers[layer_idx]
                    insert_layer = deepcopy(insert_layers[layer_idx])

                    # Check if all elements in the insert layer are hidden.
                    all_invisible = True
                    for elem in insert_layer.iter():
                        if elem.get('visible') == 'true' and \
                                elem != insert_layer and \
                                et.QName(elem).localname != 'space' and \
                                et.QName(elem).localname != 'pad':
                            all_invisible = False
                            break

                    if all_invisible:
                        # Only add the base layer, as there are no differences
                        base_layer.set(
                            id_attrib.text,
                            get_formatted_xml_id(id_idx, 'r')
                        )
                    else:
                        base_layer.set(
                            id_attrib.text,
                            get_formatted_xml_id(id_idx, base_id_prefix)
                        )

                        insert_layer.set(
                            id_attrib.text,
                            get_formatted_xml_id(id_idx, insert_id_prefix)
                        )
                        # Update n tag on layer to allow trills
                        # to connect properly
                        insert_layer.set(
                            'n',
                            str(len(base_layers) + layer_idx + 1)
                        )
                        base_staff.append(insert_layer)

                    id_idx += 1
                    layer_idx += 1

                staff_idx += 1

            # TODO Merge trills. This is a large job, since they require
            # specific element ids to render properly. This is more data
            # to keep track of. For now, all trills are removed.

            bar_idx += 1

        return base
