import re
import xml.etree.ElementTree as ET


def remove_namespaces_and_ids(element):
    """Remove namespaces from the tags and filter out elements with long IDs in attributes."""
    for elem in element.iter():
        # Remove namespace from tag
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

        # Remove attributes that are long IDs or GUID-like
        elem.attrib = {
            k: v
            for k, v in elem.attrib.items()
            if not (
                re.match(r".*[a-fA-F0-9-]{36}.*", v)  # GUID-like patterns
                or re.match(r".*\{[a-fA-F0-9-]+\}.*", v)  # Curly-braced GUID
                or k in ["fmtid", "pid", "type"]  # Specific attribute names to remove
            )
        }


def remove_elements_with_guid_text(element):
    """Recursively remove elements whose text content matches a GUID pattern."""
    for child in list(element):
        # Recursively clean the child elements first
        remove_elements_with_guid_text(child)

        # If the child element's text matches a GUID-like pattern, remove the element
        if child.text and re.match(r"^[a-fA-F0-9-]{36}$", child.text.strip()):
            element.remove(child)


def remove_elements_with_unwanted_attributes(element):
    """Remove elements that have unwanted attributes."""
    for child in list(element):
        remove_elements_with_unwanted_attributes(child)
        # If the element has any attributes related to GUIDs, remove it
        if any(re.match(r"^[a-fA-F0-9-]{36}$", v) for v in child.attrib.values()) or "fmtid" in child.attrib:
            element.remove(child)


def remove_empty_elements(element):
    """Recursively remove empty elements from the XML tree."""
    for child in list(element):
        remove_empty_elements(child)
        # If the child element is empty or only contains an empty child, remove it
        if (not child.text or not child.text.strip()) and len(child) == 0:
            element.remove(child)


def clean_xml(xml_content):
    # Parse the XML content from a string
    root = ET.fromstring(xml_content)

    # Remove namespaces and attributes with long IDs
    remove_namespaces_and_ids(root)

    # Remove elements with GUID-like text
    remove_elements_with_guid_text(root)

    # Remove elements that have attributes like fmtid or GUID patterns
    remove_elements_with_unwanted_attributes(root)

    # Remove elements that are now empty
    remove_empty_elements(root)

    # Convert cleaned XML tree back to a string
    cleaned_xml = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    return cleaned_xml
