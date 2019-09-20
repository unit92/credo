#! /usr/bin/env python3

# This script is indented to be a command line utility and a library for the
# project

from __future__ import annotations
from copy import deepcopy
from sys import argv, exit, stderr

from lxml import etree
from lxml.etree import ElementTree

# Shorthand XML namespaces
ns = {'mei': 'http://www.music-encoding.org/ns/mei',
      'xml': 'http://www.w3.org/1999/xlink'}


class MeiTransformer:
    _tree: ElementTree

    def __init__(self, tree: ElementTree):
        self._tree = tree

    @classmethod
    def from_xml_file(cls, filename: str) -> MeiTransformer:
        """
        Construct an MeiTransformer from a file existing on disk
        """
        tree = ElementTree()
        tree.parse(filename)
        return cls(tree)

    @classmethod
    def from_xml_string(cls, xml_string: str) -> MeiTransformer:
        """
        Construct an MeiTransformer from a string
        """
        root = etree.fromstring(xml_string)
        tree = ElementTree(root)
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
        return self._tree.find('.//mei:note[@octname]', ns) is not None

    def normalise(self) -> None:
        """
        Normalise the MEI file. All MEI files must be normalised before saving

        At the moment MEI normalisation consists of the following steps:
            1. Removing the MEI header
            2. Removing any MIDI metadata

        In the future more tasks may be added to the normalisation process
        """
        self._remove_meiHead()
        self._remove_MIDI_data()

    def to_intermediate(self) -> None:
        if self.is_intermediate:
            raise ValueError('MEI is already in intermediate representation')
        for elem in self._tree.findall('.//mei:note[@oct][@pname]', ns):
            pname = elem.attrib.pop('pname')
            octave = elem.attrib.pop('oct')
            octname = f'{octave}:{pname}'
            elem.set('octname', octname)

    def to_plain_mei(self) -> None:
        if not self.is_intermediate:
            raise ValueError('MEI is not in intermediate representation')
        for elem in self._tree.findall('.//mei:note[@octname]', ns):
            octname = elem.attrib.pop('octname')
            pname, octave = octname.split(':')
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
        for elem in self._tree.findall('mei:meiHead', ns):
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
        for elem in self._tree.findall('.//mei:note[@pnum]', ns):
            elem.attrib.pop('pnum')
        for elem in self._tree.findall('.//mei:instrDef', ns):
            elem.getparent().remove(elem)


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
