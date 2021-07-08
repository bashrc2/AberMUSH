__filename__ = "mmp.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski", "Mark Frimston"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "Client"


def _getRegions(rooms: {}) -> {}:
    """Gets regions and their index numbers as a dict
    """
    index = 1
    regions = {}
    for roomId, item in rooms.items():
        if not item.get('region'):
            continue
        if not regions.get(item['region']):
            regions[item['region']] = index
            index += 1
    return regions


def _getMMP(rooms: {}, environments: {}) -> str:
    """Exports rooms in MMP format for use by MUD client mapping systems
    See https://wiki.mudlet.org/w/Standards:MMP
    """
    regions = _getRegions(rooms)
    xmlStr = "<?xml version=\"1.0\"?>\n"
    xmlStr += "<map>\n"
    xmlStr += "  <areas>\n"
    for regionName, regionId in regions.items():
        xmlStr += \
            "    <area id=\"" + str(regionId) + "\" " + \
            "name=\"" + regionName + "\" />\n"
    xmlStr += "  </areas>\n"
    xmlStr += "  <rooms>\n"
    for roomId, item in rooms.items():
        roomId = roomId.split('=')[1].replace('$', '')
        environmentStr = ''
        if item.get('environmentId'):
            environmentId = item['environmentId']
            environmentStr = "environment=\"" + str(environmentId) + "\""
        x = y = z = 999999
        if item.get('coords'):
            if len(item['coords']) >= 3:
                # east
                x = item['coords'][1]
                # north
                y = item['coords'][0]
                # vertical
                z = item['coords'][2]
        regionId = 0
        areaStr = ''
        if item.get('region'):
            if regions.get(item['region']):
                regionId = regions[item['region']]
                areaStr = "area=\"" + str(regionId) + "\" "
        xmlStr += \
            "    <room id=\"" + roomId + "\" " + areaStr + \
            "title=\"" + item['name'].replace('"', "'") + "\" " + \
            environmentStr + ">\n"
        if x != 999999:
            xmlStr += \
                "      <coord x=\"" + str(x) + "\" " + \
                "y=\"" + str(y) + "\" z=\"" + str(z) + "\"/>\n"
        for direction, exitRoomId in item['exits'].items():
            exitRoomId = exitRoomId.split('=')[1].replace('$', '')
            xmlStr += \
                "      <exit direction=\"" + direction + "\" " + \
                "target=\"" + exitRoomId + "\"/>\n"
        xmlStr += \
            "    </room>\n"
    xmlStr += "  </rooms>\n"
    xmlStr += "  <environments>\n"
    for environmentId, item in environments.items():
        xmlStr += \
            "    <environment id=\"" + str(environmentId) + "\" " + \
            "name=\"" + item['name'] + "\" " + \
            "color=\"" + str(item['color']) + "\" />\n"
    xmlStr += "  </environments>\n"
    xmlStr += "</map>\n"
    return xmlStr


def exportMMP(rooms: {}, environments: {}, filename: str) -> None:
    """Exports rooms in MMP format for use by MUD clients
    See https://wiki.mudlet.org/w/Standards:MMP
    """
    xmlStr = _getMMP(rooms, environments)
    with open(filename, "w+") as fp:
        fp.write(xmlStr)
