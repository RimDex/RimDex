from pathlib import Path

from lxml import etree

from app.io.safe_xml import safe_xml_parser


def test_recovers_malformed_document_when_requested() -> None:
    root = etree.fromstring(
        b"<root><version>1.2.3</version>", parser=safe_xml_parser(recover=True)
    )
    assert root.findtext("version") == "1.2.3"


def test_parses_well_formed_document() -> None:
    root = etree.fromstring(b"<root><a>1</a></root>", parser=safe_xml_parser())
    assert root.findtext("a") == "1"


def test_external_entity_does_not_leak_local_file(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP_SECRET_VALUE", encoding="utf-8")

    payload = (
        '<?xml version="1.0"?>'
        f'<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///{secret.as_posix()}">]>'
        "<root>&xxe;</root>"
    ).encode()

    root = etree.fromstring(payload, parser=safe_xml_parser())
    assert "TOP_SECRET_VALUE" not in (root.text or "")


def test_external_dtd_is_not_loaded(tmp_path: Path) -> None:
    dtd = tmp_path / "evil.dtd"
    dtd.write_text('<!ENTITY xxe SYSTEM "file:///etc/passwd">', encoding="utf-8")

    payload = (
        "<?xml version='1.0'?>"
        f'<!DOCTYPE root SYSTEM "file:///{dtd.as_posix()}">'
        "<root/>"
    ).encode()

    root = etree.fromstring(payload, parser=safe_xml_parser())
    assert root.tag == "root"


def test_internal_entity_expansion_is_neutralised() -> None:
    payload = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE root [<!ENTITY a "aaaaaaaaaa">]>'
        b"<root>&a;</root>"
    )
    root = etree.fromstring(payload, parser=safe_xml_parser())
    assert "aaaaaaaaaa" not in (root.text or "")


def test_billion_laughs_is_not_expanded() -> None:
    lol = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE r [<!ENTITY a "aaaaaaaaaa">'
        b'<!ENTITY b "&a;&a;&a;&a;&a;">'
        b'<!ENTITY c "&b;&b;&b;&b;&b;">'
        b'<!ENTITY d "&c;&c;&c;&c;&c;">'
        b'<!ENTITY e "&d;&d;&d;&d;&d;">]>'
        b"<r>&e;</r>"
    )
    root = etree.fromstring(lol, parser=safe_xml_parser())
    assert len(root.text or "") < 1000


def test_network_dtd_reference_is_not_followed() -> None:
    payload = (
        b"<?xml version='1.0'?>"
        b"<!DOCTYPE root SYSTEM 'http://127.0.0.1:1/evil.dtd'>"
        b"<root/>"
    )
    root = etree.fromstring(payload, parser=safe_xml_parser())
    assert root.tag == "root"


def test_returns_usable_parse_from_file(tmp_path: Path) -> None:
    target = tmp_path / "doc.xml"
    target.write_text("<root><version>9.9.9</version></root>", encoding="utf-8")

    tree = etree.parse(str(target), parser=safe_xml_parser())
    assert tree.getroot().findtext("version") == "9.9.9"
