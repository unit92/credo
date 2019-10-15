def get_formatted_xml_id(num: int, prefix=''):
    BASE = 'm-{}{}'
    return BASE.format(prefix, num)
