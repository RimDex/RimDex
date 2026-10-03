from lxml import etree


def safe_xml_parser(recover: bool = False) -> etree.XMLParser:
    """
    Build an lxml parser that neither resolves nor expands XML entities.

    lxml's stock parser still expands internally declared entities, so a
    document carrying a nested ``<!ENTITY>`` ladder ("billion laughs") can
    exhaust memory, and older libxml2 builds additionally follow external
    ``SYSTEM`` entities into local files and over the network.  Turning off
    entity resolution, DTD loading, and network access closes both off
    (GHSA-vfmq-68hx-4jfw).

    :param recover: Enable lxml recovery mode for malformed documents.
    :return: A parser instance safe for untrusted XML.
    """
    return etree.XMLParser(
        recover=recover,
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,
    )
