#! /usr/bin/env python3

# This script is indented to be a command line utility and a library for the
# project

from __future__ import annotations
from copy import deepcopy
from sys import argv, exit, stderr

import typing as t

from lxml import etree
from lxml.etree import ElementTree

from .xml_namespaces import MEI_NS
from .id_formatters import get_formatted_xml_id


class MeiTransformer:
    _tree: ElementTree
    _id_map: t.Dict[str, str]

    def __init__(self, tree: ElementTree):
        self._tree = tree
        self._id_map = {}

    @classmethod
    def from_xml_file(cls, filename: str) -> MeiTransformer:
        """
        Construct an MeiTransformer from a file existing on disk
        """
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(filename, parser=parser)
        return cls(tree)

    @classmethod
    def from_xml_string(cls, xml_string: str) -> MeiTransformer:
        """
        Construct an MeiTransformer from a string
        """
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_string, parser=parser)
        return cls(tree)

    @property
    def tree(self) -> ElementTree:
        """
        Return a copy of the internal ElementTree
        """
        return deepcopy(self._tree)

    @property
    def is_intermediate(self) -> bool:
        """
        Determine if we're an intermediate representation of the MEI file or if
        we're a plain MEI file by checking if any note tags have the octname
        attribute, which is specific to the intermediate MEI format
        """
        return self._tree.find('.//mei:note[@octname]', MEI_NS) is not None

    def remove_metadata(self) -> None:
        """
        Remove metadata from the MEI file.

        At the moment MEI normalisation consists of the following steps:
            1. Removing the MEI header
            2. Removing any MIDI metadata

        In the future more tasks may be added to the normalisation process
        """
        self._remove_meiHead()
        self._remove_MIDI_data()

    def normalise(self) -> None:
        """
        Normalise the MEI file. All MEI files must be normalised before saving
        if we wish to be able to compare them

        At the moment MEI normalisation consists of the following steps:
            1. Removing appropriate metadata (MEI header, MIDI etc.)
            2. Strip existing colour attributes
            3. Regenerating IDs

        In the future more tasks may be added to the normalisation process
        """
        self.remove_metadata()
        self.strip_attribs(['color', 'visible'])
        self.generate_ids()

    def to_intermediate(self) -> None:
        if self.is_intermediate:
            raise ValueError('MEI is already in intermediate representation')
        for elem in self._tree.findall('.//mei:note[@oct][@pname]', MEI_NS):
            pname = elem.attrib.pop('pname')
            octave = elem.attrib.pop('oct')
            octname = f'{octave}:{pname}'
            elem.set('octname', octname)
        self._strip_ids()

    def to_plain_mei(self) -> None:
        if not self.is_intermediate:
            raise ValueError('MEI is not in intermediate representation')
        for elem in self._tree.findall('.//mei:note[@octname]', MEI_NS):
            octname = elem.attrib.pop('octname')
            octave, pname = octname.split(':')
            elem.set('pname', pname)
            elem.set('oct', octave)

    def save_xml_file(self, filename: str, encoding='UTF-8') -> None:
        """
        Save the current MEI file to disk
        """
        self._tree.write(filename, encoding=encoding)

    def _remove_meiHead(self) -> None:
        """
        Removes the meiHead tag that has metadata about where the MEI came from
        and other useless information
        """
        # There should only be one meiHead tag, but just to be sure
        for elem in self._tree.findall('mei:meiHead', MEI_NS):
            elem.getparent().remove(elem)

    def _remove_MIDI_data(self) -> None:
        """
        Removes any MIDI related tags and attributes from the MEI file. As this
        tool does not support playing MEI files, it reduces the diff sizes if
        we remove information like this. In addition the MIDI information may
        be able to be reconstructed from a combination of the note, octave, key
        and any alterations to that key (eg sharps, naturals, etc)
        """
        # This is an xpath to find any note tags in the MEI namespace with the
        # pnum attribute
        for elem in self._tree.findall('.//mei:note[@pnum]', MEI_NS):
            elem.attrib.pop('pnum')
        for elem in self._tree.findall('.//mei:instrDef', MEI_NS):
            elem.getparent().remove(elem)

    def _strip_ids(self) -> None:
        """
        Strip xml:id attributes for all elements in the tree to
        ensure they don't affect the diff algorithm.
        """
        class_lookup = etree.ElementDefaultClassLookup()

        for elem in self._tree.iter():
            class_lookup.entity_class
            # Ensure element can have attributes
            if (not isinstance(elem, class_lookup.comment_class) and
                    not isinstance(elem, class_lookup.entity_class)):
                id_attrib = etree.QName(MEI_NS['xml'], 'id')
                if elem.attrib.get(id_attrib.text) is not None:
                    elem.attrib.pop(id_attrib.text)

    def strip_attribs(self, attribs: t.List[str]) -> None:
        """
        Strip given attributes for all elements in the tree to
        ensure they don't affect the diff algorithm.
        """
        class_lookup = etree.ElementDefaultClassLookup()

        for elem in self._tree.iter():
            class_lookup.entity_class
            # Ensure element can have attributes
            if (not isinstance(elem, class_lookup.comment_class) and
                    not isinstance(elem, class_lookup.entity_class)):
                for attrib in attribs:
                    if elem.attrib.get(attrib) is not None:
                        elem.attrib.pop(attrib)

    def generate_ids(self, keep_existing=False) -> None:
        """
        Create/recreate xml:id attributes for all elements in the tree to
        ensure they are all unique, and that every elements has an id.
        """
        class_lookup = etree.ElementDefaultClassLookup()

        self._id_map = {}

        # Find all trills in the MEI, as they reference other IDs
        trill_id_map = dict()
        for elem in self._tree.findall('//mei:trill', MEI_NS):
            referenced_id = elem.get('startid')
            if referenced_id is not None:
                trill_id_map[referenced_id] = elem

        # Regenerate IDs, replacing IDs referenced by trills with new IDs
        index = 0
        for elem in self._tree.iter():
            class_lookup.entity_class
            # Ensure element can have attributes
            if (not isinstance(elem, class_lookup.comment_class) and
                    not isinstance(elem, class_lookup.entity_class)):
                id_attrib = etree.QName(MEI_NS['xml'], 'id')
                id_val = elem.get(id_attrib.text)

                if keep_existing and id_val is not None:
                    continue

                new_id = get_formatted_xml_id(index)
                # Update trill reference
                if id_val is not None:
                    self._id_map[id_val] = new_id
                    if '#' + id_val in trill_id_map.keys():
                        trill_id_map['#' + id_val].set('startid', new_id)

                # Set new ID
                elem.set(id_attrib.text, new_id)
            index += 1

    def get_id_map(self):
        """
        Return the mapping of old MEI IDs to new MEI IDs.
        """
        return self._id_map


def main():
    argc = len(argv)
    if argc >= 3:
        input_path = argv[1]
        output_path = argv[2]
        mt = MeiTransformer.from_xml_file(input_path)
        mt.normalise()
        mt.save_xml_file(output_path)
        return mt
    else:
        print(f'Usage: {argv[0]} input_file output_file', file=stderr)
        exit(1)


if __name__ == '__main__':
    main()
