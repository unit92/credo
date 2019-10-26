import lxml.etree as et
from utils.mei.xml_namespaces import MEI_NS
from copy import deepcopy


def merge_measure_layers(measure: et.ElementTree):
    id_attrib = et.QName(MEI_NS['xml'], 'id')
    print(et.tostring(measure, pretty_print=True).decode())

    # Loop through all staves, merging layers for each
    staff_qry = et.XPath('child::mei:staff', namespaces=MEI_NS)
    staves = staff_qry(measure)
    for staff in staves:
        layer_qry = et.XPath('child::mei:layer', namespaces=MEI_NS)
        layers = layer_qry(staff)

        # Split layers into corresponding pairs/groups and try to merge each
        layer_groups = {}
        for layer in layers:
            xml_id = layer.get(id_attrib.text)
            num_id = ''.join([s for s in xml_id if s.isdigit()])
            if num_id in layer_groups.keys():
                layer_groups[num_id].append(layer)
            else:
                layer_groups[num_id] = [layer]

        # Merge layer groups
        merged_layers = []
        for layer_group in layer_groups.values():
            merged = _merge_layers(layer_group)
            if isinstance(merged, list):
                for m in merged():
                    merged_layers.append(m)
            else:
                merged_layers.append(merged)

        # Remove all existing layers and replace with merged layers
        for layer in layers:
            staff.remove(layer)
        for layer in merged_layers:
            print(layer)
            staff.append(layer)
    print(et.tostring(measure, pretty_print=True).decode())
    return measure


def _merge_layers(layers):
    return deepcopy(layers[0])
