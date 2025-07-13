import pytest

import csv2cmi


@pytest.fixture
def table():
    table


def test_create_date_valid():
    assert csv2cmi.CMI.create_date("2016-04-01").attrib["when"] == "2016-04-01"
    assert csv2cmi.CMI.create_date("1673-05").attrib["when"] == "1673-05"
    assert csv2cmi.CMI.create_date("[..1760-12-03]").attrib["notAfter"] == "1760-12-03"
    assert csv2cmi.CMI.create_date("[1760-12..]").attrib["notBefore"] == "1760-12-01"
    assert csv2cmi.CMI.create_date("1979-10-12/").attrib["from"] == "1979-10-12"
    assert csv2cmi.CMI.create_date("/1985-04-12").attrib["to"] == "1985-04-12"
    assert csv2cmi.CMI.create_date("{-0400,-0390,-0370}") is not None


def test_create_date_invalid():
    with pytest.raises(ValueError):
        csv2cmi.CMI.create_date("not-a-date")


def test_create_place_name():
    tei_placename = csv2cmi.CMI.create_place_name("Berlin")
    assert tei_placename.tag == "placeName"
    assert tei_placename.text == "Berlin"


def test_create_place_name_with_uri():
    tei_placename = csv2cmi.CMI.create_place_name("Mokhdān", "https://www.geonames.org/123456")
    assert tei_placename.tag == "placeName"
    assert tei_placename.attrib["ref"] == "https://www.geonames.org/123456"
    assert tei_placename.text == "Mokhdān"


def test_generate_id_and_uuid():
    id1 = csv2cmi.CMI.generate_id("test")
    id2 = csv2cmi.CMI.generate_id("test")
    assert id1 != id2
    cmi = csv2cmi.CMI()
    uuid1 = cmi.generate_uuid()
    uuid2 = cmi.generate_uuid()
    assert uuid1 != uuid2
