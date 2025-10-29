import pytest

from csv2cmi import CMI


def test_create_date_valid():
    assert CMI.create_date("2016-04-01").attrib["when"] == "2016-04-01"
    assert CMI.create_date("1673-05").attrib["when"] == "1673-05"
    assert CMI.create_date("~1348-01-29").attrib["when"] == "1348-01-29"
    assert CMI.create_date("[1760-12..]").attrib["notBefore"] == "1760-12-01"
    assert CMI.create_date("[1804,1807,1809]").attrib["notBefore"] == "1804-01-01"
    assert CMI.create_date("[1999..2002]").attrib["notAfter"] == "2002-12-31"
    assert CMI.create_date("[..1760-12-03]").attrib["notAfter"] == "1760-12-03"
    assert CMI.create_date("1979-10-12/").attrib["from"] == "1979-10-12"
    assert CMI.create_date("/1985-04-12").attrib["to"] == "1985-04-12"
    assert CMI.create_date("1708-03~/1710-02").attrib["cert"] == "low"
    assert CMI.create_date("?1689-07-03").attrib["cert"] == "low"


def test_create_date_invalid():
    with pytest.raises(ValueError):
        CMI.create_date("not-a-date")


def test_create_place_name():
    tei_placename = CMI.create_place_name("Berlin")
    assert tei_placename.tag == "placeName"
    assert tei_placename.text == "Berlin"


def test_create_place_name_with_uri():
    tei_placename = CMI.create_place_name("Mokhdān", "https://www.geonames.org/123456")
    assert tei_placename.tag == "placeName"
    assert tei_placename.attrib["ref"] == "https://www.geonames.org/123456"
    assert tei_placename.text == "Mokhdān"


def test_generate_id_and_uuid():
    id1 = CMI.generate_id("test")
    id2 = CMI.generate_id("test")
    assert id1 != id2
    uuid1 = CMI.generate_uuid()
    uuid2 = CMI.generate_uuid()
    assert uuid1 != uuid2
