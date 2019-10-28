import lxml.etree as et
from re import match

from utils.mei.xml_namespaces import MEI_NS


def is_resolved(mei: et.ElementTree) -> bool:
    # Check all layers have IDs of the form 'm-r[0-9]+',
    layer_qry = et.XPath('//mei:layer', namespaces=MEI_NS)
    layers = layer_qry(mei)

    id_attrib = et.QName(MEI_NS['xml'], 'id').text

    resolved = True
    for layer in layers:
        if not match('m-r[0-9]+', layer.get(id_attrib)):
            resolved = False

    print('RESOLVED:', resolved)

    return resolved
