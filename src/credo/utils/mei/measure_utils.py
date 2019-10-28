import lxml.etree as et
from utils.mei.xml_namespaces import MEI_NS
from copy import deepcopy
from pprint import pprint


def merge_measure_layers(measure: et.ElementTree):
    id_attrib = et.QName(MEI_NS['xml'], 'id')
    # print(et.tostring(measure, pretty_print=True).decode())

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
    # print(et.tostring(measure, pretty_print=True).decode())
    return measure


def _merge_layers(layers):
    # Merge layers by determining positions of elements
    # in the measure across all layers.

    if len(layers) != 2:
        raise ValueError(
            'Merging more than two layers is not currently supported.'
        )

    # Define tags that take up time in a bar, refer to
    # https://music-encoding.org/guidelines/v4/model-classes/model.eventlike.html
    event_names = ['mei:note', 'mei:rest', 'mei:space']

    for layer in layers:
        print(et.tostring(layer, pretty_print=True).decode())

    for layer in layers:
        start_ends = _get_event_start_ends(layer, event_names)
        pprint(start_ends)

    return deepcopy(layers[0])


def _get_event_start_ends(layer, event_names):
    events = []
    for e_name in event_names:
        e_qry = et.XPath(f'.//{e_name}', namespaces=MEI_NS)
        events += e_qry(layer)

    # Events that are returned first re displayed first,
    # so assume the first event in the list occurs first etc.

    start_ends = []
    start = 0
    for e in events:
        duration = _get_duration(e)
        end = start + duration
        start_ends.append((start, end, e))
        start = end

    return start_ends


def _get_duration(event):
    """
    Returns the duration of a note, as a fraction.
    e.g. a crotchet will return 0.25, a minim 0.5 etc.
    """
    # Get relevant attributes
    dur = event.get('dur')
    dots = event.get('dots')

    if dur is None:
        return None

    try:
        dur = int(dur)
    except ValueError:
        return None

    if dots is None:
        return 1/dur
    else:
        dots = int(dots)
        length = 1/dur
        mod = 1
        for i in range(dots):
            mod /= 2
            length += mod*length
        return length
