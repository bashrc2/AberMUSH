__filename__ = "mmp.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Map"


def _get_regions(rooms: {}) -> {}:
    """Gets regions and their index numbers as a dict
    """
    index = 1
    regions = {}
    for _, item in rooms.items():
        if not item.get('region'):
            continue
        if not regions.get(item['region']):
            regions[item['region']] = index
            index += 1
    return regions


def _get_mmp(rooms: {}, environments: {}) -> str:
    """Exports rooms in MMP format for use by MUD client mapping systems
    See https://wiki.mudlet.org/w/Standards:MMP
    """
    regions = _get_regions(rooms)
    xml_str = "<?xml version=\"1.0\"?>\n"
    xml_str += "<map>\n"
    xml_str += "  <areas>\n"
    for region_name, region_id in regions.items():
        xml_str += \
            "    <area id=\"" + str(region_id) + "\" " + \
            "name=\"" + region_name + "\" />\n"
    xml_str += "  </areas>\n"
    xml_str += "  <rooms>\n"
    for room_id, item in rooms.items():
        room_id = room_id.split('=')[1].replace('$', '')
        environment_str = ''
        if item.get('environmentId'):
            environment_id = item['environmentId']
            environment_str = "environment=\"" + str(environment_id) + "\""
        x_co = y_co = z_co = 999999
        if item.get('coords'):
            if len(item['coords']) >= 3:
                # east
                x_co = item['coords'][1]
                # north
                y_co = item['coords'][0]
                # vertical
                z_co = item['coords'][2]
        region_id = 0
        area_str = ''
        if item.get('region'):
            if regions.get(item['region']):
                region_id = regions[item['region']]
                area_str = "area=\"" + str(region_id) + "\" "
        xml_str += \
            "    <room id=\"" + room_id + "\" " + area_str + \
            "title=\"" + item['name'].replace('"', "'") + "\" " + \
            environment_str + ">\n"
        if x_co != 999999:
            xml_str += \
                "      <coord x=\"" + str(x_co) + "\" " + \
                "y=\"" + str(y_co) + "\" z=\"" + str(z_co) + "\"/>\n"
        for direction, exit_room_id in item['exits'].items():
            exit_room_id = exit_room_id.split('=')[1].replace('$', '')
            xml_str += \
                "      <exit direction=\"" + direction + "\" " + \
                "target=\"" + exit_room_id + "\"/>\n"
        xml_str += \
            "    </room>\n"
    xml_str += "  </rooms>\n"
    xml_str += "  <environments>\n"
    for environment_id, item in environments.items():
        xml_str += \
            "    <environment id=\"" + str(environment_id) + "\" " + \
            "name=\"" + item['name'] + "\" " + \
            "color=\"" + str(item['color']) + "\" />\n"
    xml_str += "  </environments>\n"
    xml_str += "</map>\n"
    return xml_str


def export_mmp(rooms: {}, environments: {}, filename: str) -> None:
    """Exports rooms in MMP format for use by MUD clients
    See https://wiki.mudlet.org/w/Standards:MMP
    """
    xml_str = _get_mmp(rooms, environments)
    with open(filename, "w+") as fp_mmp:
        fp_mmp.write(xml_str)
