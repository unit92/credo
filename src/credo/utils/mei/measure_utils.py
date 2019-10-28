import lxml.etree as et
from typing import List
from math import inf
from copy import deepcopy

from utils.mei.xml_namespaces import MEI_NS


def merge_measure_layers(measure: et.ElementTree):
    id_attrib = et.QName(MEI_NS['xml'], 'id')

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
    event_names = [
        'note',
        'rest',
        'space'
    ]

    event_group_names = [
        'beam',
        'chord'
    ]

    for layer in layers:
        print(et.tostring(layer, pretty_print=True).decode())

    event_dur_infos = []
    for layer in layers:
        duration_info = _get_duration_info(
            layer,
            event_names,
            event_group_names
        )
        event_dur_infos += duration_info

    # Filter layer_duration_infos by visibility
    vis_event_dur_infos = []
    for duration_info in event_dur_infos:

        # Visibility tag
        visible_tag = duration_info.event.get('visible')
        visible = visible_tag is None or visible_tag == 'true'

        # 'space' events are regarded as invisible
        if et.QName(duration_info.event).localname == 'space' \
                and et.QName(duration_info.event).namespace == MEI_NS['mei']:
            visible = False

        if visible:
            vis_event_dur_infos.append(duration_info)

    # Perform merge, ensuring that start and ends for
    # visible elements do not overlap. This is done using a greedy
    # interval scheduling approach, so we can see which
    # elements are stopping the layers from merging if needed
    mergeable_events = get_max_subset_compatible_events(vis_event_dur_infos)

    if len(mergeable_events) == len(vis_event_dur_infos):
        # All events mergeable, sort by start times and add copies to
        # a new layer and return.
        mergeable_events = sorted(mergeable_events, key=lambda e: e.start)
        new_layer = et.Element(et.QName(MEI_NS['mei'], 'layer'))

        for event_info in mergeable_events:
            new_layer.append(deepcopy(event_info.event))

        return new_layer

    raise ValueError('Could not merge layers, since they had overlaps.')


class MEIEventDurationInfo:
    def __init__(self, event, start, duration):
        self.event = event
        self.start = start
        self.duration = duration

    @property
    def finish(self):
        return self.start + self.duration


def get_max_subset_compatible_events(events: List[MEIEventDurationInfo]):
    sorted_events = sorted(events, key=lambda e: e.finish)
    selected = []
    selected_finish = -inf
    for i in range(len(sorted_events)):
        if sorted_events[i].start >= selected_finish:
            # Event is compatible
            selected.append(sorted_events[i])
            selected_finish = sorted_events[i].finish

    return selected


def _get_duration_info(
        layer: et.Element,
        event_names: list,
        event_group_names: list
        ) -> List[MEIEventDurationInfo]:

    events = []
    for e_name in event_names:
        e_qry = et.XPath(f'.//mei:{e_name}', namespaces=MEI_NS)
        events_result = e_qry(layer)
        for event in events_result:
            part_of_group = False
            # Check if elem has ancestor in event_group
            for group_name in event_group_names:
                group_qry = et.XPath(
                    f'ancestor::mei:{group_name}',
                    namespaces=MEI_NS
                )
                group = group_qry(event)
                if len(group) > 0:
                    if group[0] not in events:
                        events.append(group[0])
                    part_of_group = True
                    break
            if not part_of_group:
                events.append(event)

    # Events that are returned first re displayed first,
    # so assume the first event in the list occurs first etc.
    dur_info = []
    start = 0
    for e in events:
        duration = _get_duration(e)
        dur_info.append(MEIEventDurationInfo(e, start, duration))
        start = start + duration

    return dur_info


def _get_duration(event):
    """
    Returns the duration of an event, as a fraction.
    e.g. a crotchet will return 0.25, a minim 0.5 etc.
    """

    event_names = [
        'note',
        'rest',
        'space',
        'chord'
    ]

    event_group_names = [
        'beam'
    ]

    # Check if we are getting the duration of a grouped element
    if et.QName(event).localname in event_group_names and \
            et.QName(event).namespace == MEI_NS['mei']:
        sub_events = []
        for e_name in event_names:
            e_qry = et.XPath(f'child::mei:{e_name}', namespaces=MEI_NS)
            sub_events += e_qry(event)

        # Duration is sum of contained elements
        return sum([_get_duration(e) for e in sub_events])

    elif et.QName(event).localname in event_names and \
            et.QName(event).namespace == MEI_NS['mei']:
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

    else:
        return None
