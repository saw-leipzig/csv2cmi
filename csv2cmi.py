"""
CSV2CMI

Copyright (c) 2015-2025 Klaus Rettinghaus
programmed by Klaus Rettinghaus
licensed under MIT license
"""

import argparse
import configparser
import logging
import random
import string
import sys
import urllib.request
from csv import DictReader
from datetime import datetime
from email.utils import parseaddr
from pathlib import Path
from secrets import token_hex
from typing import Optional
from uuid import UUID
from xml.etree.ElementTree import Comment, Element, ElementTree, SubElement, tostring

__license__ = "MIT"
__version__ = "3.0.0-beta"
__author__ = "Klaus Rettinghaus"

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum

# define log output
logging.basicConfig(format="%(levelname)s: %(message)s")
logs = logging.getLogger()

# define namespace
RDF_NS = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}

# define licenses
LICENSES = {
    "CC-BY-4.0": {
        "url": "https://creativecommons.org/licenses/by/4.0/",
        "text": "This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0.",
    },
    "CC0-1.0": {
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "text": "This file has been marked as dedicated to the public domain.",
    },
}

# define arguments
parser = argparse.ArgumentParser(description="convert tables of letters to CMI")
parser.add_argument("filename", help="input file (.csv)")
parser.add_argument("-a", "--all", help="include unedited letters", action="store_true")
parser.add_argument("-n", "--notes", help="transfer notes", action="store_true")
parser.add_argument("-o", "--output", metavar="FILE", help="output file name")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("--cc0", help="mark as public domain", action="store_true")
parser.add_argument("--line-numbers", help="add line numbers", action="store_true")
parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
parser.add_argument("--extra-delimiter", help="delimiter for different values within cells")


def is_datable_iso(date_string) -> bool:
    """Check if a string is from datatype teidata.temporal.iso."""
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        try:
            datetime.strptime(date_string, "%Y-%m")
            return True
        except ValueError:
            try:
                datetime.strptime(date_string, "%Y")
                return True
            except ValueError:
                return False


def is_datable_w3c(date_string) -> bool:
    """Check if a string is from datatype teidata.temporal.w3c."""
    # handle negative dates
    if date_string.startswith("-") and len(date_string) > 4 and date_string[1].isdigit():
        date_string = date_string[1:]
    if is_datable_iso(date_string):
        return True
    # handle dates without year
    try:
        datetime.strptime(date_string, "--%m-%d")
        return True
    except ValueError:
        try:
            datetime.strptime(date_string, "--%m")
            return True
        except ValueError:
            try:
                datetime.strptime(date_string, "---%d")
                return True
            except ValueError:
                return False


class Correspondents(StrEnum):
    SENDER = "sender"
    ADDRESSEE = "addressee"


class CMI:
    """Transform a table of letters into the CMI format."""

    def __init__(self):
        """Create an empty TEI file."""
        self.cmi = Element("TEI")
        self.cmi.set("xmlns", "http://www.tei-c.org/ns/1.0")
        self.cmi.append(Comment(f" Generated with CSV2CMI {__version__} "))
        # TEI header
        tei_header = SubElement(self.cmi, "teiHeader")
        self.file_desc = SubElement(tei_header, "fileDesc")
        SubElement(self.file_desc, "titleStmt")
        SubElement(self.file_desc, "publicationStmt")
        self.source_desc = SubElement(self.file_desc, "sourceDesc")
        self.profile_desc = SubElement(tei_header, "profileDesc")
        # TEI body
        text = SubElement(self.cmi, "text")
        tei_body = SubElement(text, "body")
        SubElement(tei_body, "p")

    def __str__(self) -> str:
        return tostring(self.cmi, method="xml").decode("utf-8")

    def create_file_desc(self, project: configparser) -> None:
        """Create a TEI file description from config file."""
        # title statement
        tei_title_stmt = self.file_desc.find("titleStmt")
        tei_title = SubElement(tei_title_stmt, "title")
        tei_title.text = project.get("Project", "title", fallback="untitled letters project")
        random.seed(tei_title.text)
        tei_title.set("xml:id", self.generate_id("title"))
        for entity in project.get("Project", "editor", fallback="").splitlines():
            mailbox = parseaddr(entity)
            if "@" in entity and any(mailbox):
                tei_editor = SubElement(tei_title_stmt, "editor")
                if mailbox[0]:
                    tei_editor.text = mailbox[0]
                if mailbox[-1]:
                    SubElement(tei_editor, "email").text = mailbox[-1]
            else:
                SubElement(tei_title_stmt, "editor").text = entity
        if len(list(tei_title_stmt)) == 1:
            logging.warning("Editor missing")
            SubElement(tei_title_stmt, "editor")
        # publication statement
        tei_publication_stmt = self.file_desc.find("publicationStmt")
        for entity in project.get("Project", "publisher", fallback="").splitlines():
            SubElement(tei_publication_stmt, "publisher").text = entity
        if not list(tei_publication_stmt):
            for editor in tei_title_stmt.findall("editor"):
                SubElement(tei_publication_stmt, "publisher").text = editor.text
        tei_idno = SubElement(tei_publication_stmt, "idno")
        tei_idno.set("type", "url")
        tei_idno.text = project.get("Project", "fileURL", fallback="www.example.com")
        SubElement(tei_publication_stmt, "date").set("when", str(datetime.now().isoformat()))
        availability = SubElement(tei_publication_stmt, "availability")
        tei_licence = SubElement(availability, "licence")
        chosen_license = LICENSES.get(project.get("Project", "license", fallback="CC-BY-4.0"))
        tei_licence.set("target", chosen_license.get("url"))
        tei_licence.text = chosen_license["text"]

    def add_edition(self, bibl_text: str, bibl_type: str = "print") -> str:
        """Create a new bibliographic entry and return its ID."""
        tei_bibl = Element("bibl")
        tei_bibl.text = bibl_text
        tei_bibl.set("type", bibl_type)
        tei_bibl.set("xml:id", self.generate_uuid())
        self.source_desc.append(tei_bibl)
        return tei_bibl.get("xml:id")

    def get_id_by_title(self, title: str) -> Optional[str]:
        """Get the ID for an edition by title."""
        for bibliographic_entry in self.source_desc.findall("bibl"):
            if title == bibliographic_entry.text:
                return bibliographic_entry.get("xml:id")
        return None

    def create_correspondent(self, name_string: str) -> list:
        """Create a correspondent."""
        if letter[name_string]:
            correspondent_list: list = []
            # Turning the cells of correspondent names and their IDs into lists since cells
            # can contain various correspondents split by an extra delimiter.
            # In that case it is essential to be able to call each by their index.
            if subdlm:
                persons = letter[name_string].split(subdlm)
                try:
                    person_ids = letter[name_string + "ID"].split(subdlm)
                except KeyError:
                    person_ids = []
            else:
                persons = [letter[name_string]]
                try:
                    person_ids = [letter[name_string + "ID"]]
                except KeyError:
                    person_ids = []
            for index, person in enumerate(persons):
                correspondent = Element("persName")
                person = str(person).strip()
                # assigning authority file IDs to their correspondents if provided
                if (index < len(person_ids)) and person_ids[index]:
                    # by default complete GND-IDNs to full URI
                    if (
                        not str(person_ids[index].strip()).startswith("http")
                        and str(person_ids[index].strip())[:-2].isdigit()
                    ):
                        logging.debug("Assigning ID %s to GND", str(person_ids[index].strip()))
                        authority_file_uri = "https://d-nb.info/gnd/" + str(person_ids[index].strip())
                    else:
                        authority_file_uri = str(person_ids[index].strip())
                    processed_correspondent = self.profile_desc.find(
                        f'correspDesc/correspAction/*[@ref="{authority_file_uri}"]'
                    )
                    if processed_correspondent is not None:
                        correspondent = Element(processed_correspondent.tag)
                    else:
                        if "viaf" in authority_file_uri:
                            try:
                                viafrdf = ElementTree(file=urllib.request.urlopen(authority_file_uri + "/rdf.xml"))
                            except urllib.error.HTTPError:
                                logging.error(
                                    "Authority file not found for %sID in line %s", name_string, table.line_num
                                )
                            except urllib.error.URLError as connection_issue:
                                logging.error("Failed to reach VIAF (%s)", str(connection_issue.reason))
                            else:
                                viafrdf_root = viafrdf.getroot()
                                if (
                                    viafrdf_root.find(
                                        './rdf:Description/rdf:type[@rdf:resource="http://schema.org/Organization"]',
                                        RDF_NS,
                                    )
                                    is not None
                                ):
                                    correspondent = Element("orgName")
                                elif (
                                    viafrdf_root.find(
                                        './rdf:Description/rdf:type[@rdf:resource="http://schema.org/Person"]', RDF_NS
                                    )
                                    is not None
                                ):
                                    correspondent = Element("persName")
                                else:
                                    logging.warning(
                                        "%sID in line %s links to unprocessable authority file",
                                        name_string,
                                        table.line_num,
                                    )
                        elif "gnd" in authority_file_uri:
                            try:
                                gndrdf = ElementTree(file=urllib.request.urlopen(authority_file_uri + "/about/rdf"))
                            except urllib.error.HTTPError:
                                logging.error(
                                    "Authority file not found for %sID in line %s", name_string, table.line_num
                                )
                            except urllib.error.URLError as connection_issue:
                                logging.error("Failed to reach GND (%s)", str(connection_issue.reason))
                            except UnicodeEncodeError:
                                logging.error("Failed to encode %s", authority_file_uri)
                            else:
                                corporatelike = ("Corporate", "Company", "ReligiousAdministrativeUnit")
                                personlike = ("DifferentiatedPerson", "Royal", "Family", "Legendary")
                                gndrdf_root = gndrdf.getroot()
                                current_id = gndrdf_root[0].get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
                                if (
                                    urllib.parse.urlparse(authority_file_uri).path
                                    != urllib.parse.urlparse(current_id).path
                                ):
                                    logging.info("%s returns new ID %s", authority_file_uri, current_id)
                                rdftype = gndrdf_root.find(".//rdf:type", RDF_NS).get(
                                    "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"
                                )
                                if any(entity in rdftype for entity in corporatelike):
                                    correspondent = Element("orgName")
                                elif any(entity in rdftype for entity in personlike):
                                    correspondent = Element("persName")
                                else:
                                    authority_file_uri = ""
                                    if "UndifferentiatedPerson" in rdftype:
                                        logging.warning(
                                            "%sID in line %s links to undifferentiated Person",
                                            name_string,
                                            table.line_num,
                                        )
                                    else:
                                        logging.error("%sID in line %s has wrong rdf:type", name_string, table.line_num)
                        elif "loc" in authority_file_uri:
                            try:
                                locrdf = ElementTree(file=urllib.request.urlopen(authority_file_uri + ".rdf"))
                            except urllib.error.HTTPError:
                                logging.error(
                                    "Authority file not found for %sID in line %s", name_string, table.line_num
                                )
                            except urllib.error.URLError as connection_issue:
                                logging.error("Failed to reach LOC (%s)", str(connection_issue.reason))
                            else:
                                locrdf_root = locrdf.getroot()
                                if (
                                    locrdf_root.find(
                                        './/rdf:type[@rdf:resource="http://id.loc.gov/ontologies/bibframe/Organization"]',
                                        RDF_NS,
                                    )
                                    is not None
                                ):
                                    correspondent = Element("orgName")
                                elif (
                                    locrdf_root.find(
                                        './/rdf:type[@rdf:resource="http://id.loc.gov/ontologies/bibframe/Person"]',
                                        RDF_NS,
                                    )
                                    is not None
                                ):
                                    correspondent = Element("persName")
                                else:
                                    logging.warning(
                                        "%sID in line %s links to unprocessable authority file",
                                        name_string,
                                        table.line_num,
                                    )
                        else:
                            authority_file_uri = ""
                            logging.error("No proper authority record in line %s for %s", table.line_num, name_string)
                    if authority_file_uri:
                        correspondent.set("ref", authority_file_uri)
                else:
                    logging.debug('ID for "%s" missing in line %s', person, table.line_num)
                if person.startswith("[") and person.endswith("]"):
                    correspondent.set("evidence", "conjecture")
                    person = person[1:-1]
                    logging.info("Added @evidence to <%s> from line %s", correspondent.tag, table.line_num)
                correspondent.text = person
                correspondent_list.append(correspondent)
        return correspondent_list

    @staticmethod
    def create_corresp_action(letter: dict, correnspondent: Correspondents) -> Element:
        """Create a correspondence action."""
        action = Element("correspAction")
        action.set("xml:id", cmi_object.generate_id(correnspondent))
        action_type: str = "sent" if correnspondent == Correspondents.SENDER else "received"
        action.set("type", action_type)

        # add name of sender
        if letter[correnspondent]:
            correspondents = cmi_object.create_correspondent(correnspondent)
            for sender in correspondents:
                action.append(sender)
        # add place_name
        senderPlace = cmi_object.process_place(letter, correnspondent)
        if senderPlace.attrib or senderPlace.text:
            action.append(senderPlace)
        # add date
        senderDate = cmi_object.process_date(letter, correnspondent)
        if senderDate.attrib or senderDate.text:
            action.append(senderDate)

        return action

    @staticmethod
    def create_date(date_string: Optional[str]) -> Optional[Element]:
        """Convert an EDTF date into a proper TEI element."""
        # normalize date
        normalized_date = date_string.translate(date_string.maketrans("", "", "?~%"))
        if not normalized_date:
            return None
        tei_date = Element("date")
        if len(normalized_date) > 4 and normalized_date[-1] == "X":
            # remove day and month with unspecified digits
            normalized_date = normalized_date[0:-3]
            if normalized_date[-1] == "X":
                normalized_date = normalized_date[0:-3]
        if normalized_date[-1] == "X":
            # convert year with unspecified digits into interval
            normalized_date = normalized_date.replace("X", "0") + "/" + normalized_date.replace("X", "9")
        if normalized_date.startswith("[") and normalized_date.endswith("]"):
            # One of a set
            date_list = normalized_date[1:-1].split(",")
            date_first = date_list[0].split(".")[0]
            date_last = date_list[-1].split(".")[-1]
            if is_datable_w3c(date_first):
                tei_date.set("notBefore", str(date_first))
            if is_datable_w3c(date_last):
                tei_date.set("notAfter", str(date_last))
        elif normalized_date.startswith("{") and normalized_date.endswith("}"):
            # All Members
            date_list = normalized_date[1:-1].split(",")
            date_first = date_list[0].split(".")[0]
            date_last = date_list[-1].split(".")[-1]
            if is_datable_w3c(date_first):
                tei_date.set("from", str(date_first))
            if is_datable_w3c(date_last):
                tei_date.set("to", str(date_last))
        elif normalized_date.count("/") == 1:
            # Time Interval
            date_first, date_last = normalized_date.split("/")
            if is_datable_w3c(date_first):
                tei_date.set("from", str(date_first))
            if is_datable_w3c(date_last):
                tei_date.set("to", str(date_last))
        elif is_datable_w3c(normalized_date):
            tei_date.set("when", str(normalized_date))
        if tei_date.attrib:
            if normalized_date != date_string:
                tei_date.set("cert", "low")
                logging.info("Added @cert to <date> from line %s", table.line_num)
            return tei_date
        raise ValueError(f'unable to parse "{date_string}" as TEI date')

    @staticmethod
    def create_place_name(place_name_text: str, geonames_uri: str | None = None) -> Element:
        """Create a placeName element."""
        place_name = Element("placeName")
        place_name_text = place_name_text.strip()
        if place_name_text.startswith("[") and place_name_text.endswith("]"):
            place_name.set("evidence", "conjecture")
            place_name_text = place_name_text[1:-1]
            logging.info("Added @evidence to <placeName> from line %s", table.line_num)
        place_name.text = str(place_name_text)
        if geonames_uri:
            geonames_uri = geonames_uri.strip()
            if "www.geonames.org" in geonames_uri:
                place_name.set("ref", str(geonames_uri))
            else:
                logging.warning('"%s" is a non-standard GeoNames ID', geonames_uri)
        return place_name

    @staticmethod
    def generate_id(id_prefix: str) -> str:
        """Generate a prefixed ID of type xs:ID."""
        if id_prefix.strip() == "":
            id_prefix = "".join(random.choice(string.ascii_lowercase) for _ in range(8))
        generated_id = f"{id_prefix.strip()}-{token_hex(4)}"
        return generated_id

    def generate_uuid(self) -> str:
        """Generate a UUID of type xs:ID."""
        generated_uuid = str(UUID(bytes=bytes(random.getrandbits(8) for _ in range(16)), version=4))
        if generated_uuid[0].isdigit():
            return self.generate_uuid()
        return generated_uuid

    def process_date(self, letter: dict, correspondent: Correspondents) -> Optional[Element]:
        """Process date."""
        correspDate = Element("date")
        try:
            correspDate = self.create_date(letter[correspondent + "Date"])
        except (KeyError, TypeError):
            pass
        except ValueError:
            logging.warning("Could not parse %sDate in line %s", correspondent, table.line_num)
        else:
            if correspDate is None:
                correspDate = Element("date")
        try:
            correspDate.text = letter[correspondent + "DateText"].strip()
        except (KeyError, TypeError):
            pass
        return correspDate

    def process_place(self, letter: dict, correspondent: Correspondents) -> Element:
        """Process place."""
        place_name = letter.get(correspondent + "Place", "")
        place_id = letter.get(correspondent + "PlaceID")
        return self.create_place_name(place_name, place_id)

    def replace_short_titles(self, project: configparser) -> None:
        """Replace short titles by full title defined in config file."""
        for bibl in self.source_desc.findall("bibl"):
            # Try to use bibliographic text as key for section in config file
            editionKey = bibl.text
            try:
                edition_title = project.get(editionKey, "title")
                try:
                    edition_type = project.get(editionKey, "type")
                except configparser.NoOptionError:
                    # if type is not set, use the default one
                    pass
                bibl.text = edition_title
                bibl.set("type", edition_type)
            except configparser.NoOptionError:
                logging.warning("Incomplete section %s in ini file. Title and type option must be set.", editionKey)
            except configparser.NoSectionError:
                # if there is no matching section, we assume that there shouldn't be one
                pass

    def save_to_file(self, file_name: Path) -> None:
        """Save CMI to file."""
        tree = ElementTree(self.cmi)
        try:
            tree.write(file_name, encoding="utf-8", xml_declaration=True, method="xml")
            print(f"CMI file written to {file_name}")
        except PermissionError:
            logging.error("Could not save the file due to insufficient permission")
            sys.exit(1)


if __name__ == "__main__":
    args = parser.parse_args()

    # set verbosity
    if args.verbose:
        logs.setLevel("INFO")

    # set extra delimiter
    if args.extra_delimiter:
        if len(args.extra_delimiter) == 1:
            subdlm = args.extra_delimiter
        else:
            logging.error("Delimiter has to be a single character")
            sys.exit(1)
    else:
        subdlm = None

    # simple test for file
    letters_csv = Path(args.filename)
    if not letters_csv.exists():
        logging.error("File not found")
        sys.exit(1)

    cmi_object = CMI()

    # read config file
    config = configparser.ConfigParser()
    # set default values
    config["Project"] = {"fileURL": letters_csv.with_suffix(".xml")}
    if args.cc0:
        config["Project"]["license"] = "CC0-1.0"

    INI_FILE = "csv2cmi.ini"
    try:
        config.read_file(open(Path(letters_csv.parent, INI_FILE), encoding="utf-8"))
    except IOError:
        try:
            config.read_file(open(INI_FILE, encoding="utf-8"))
        except IOError:
            logging.error("No configuration file found")

    # set type of edition
    edition_type = "print"
    if ("Edition" in config) and ("type" in config["Edition"]):
        if config.get("Edition", "type") in ["print", "hybrid", "online"]:
            edition_type = config.get("Edition", "type")

    # set extra delimiter
    if not subdlm:
        try:
            subdlm = config.get("Project", "extra-delimiter")
            if len(subdlm) > 1:
                logging.error("Delimiter has to be a single character")
                sys.exit(1)
        except configparser.NoOptionError:
            pass

    # building cmi
    # create a file description from config file
    cmi_object.create_file_desc(config)

    with open(letters_csv, "rt", encoding="utf-8") as letters_table:
        # global table
        table = DictReader(letters_table)
        logging.debug("Recognized columns: %s", table.fieldnames)
        if not ("sender" in table.fieldnames and "addressee" in table.fieldnames):
            logging.error("No sender/addressee field in table")
            sys.exit(1)
        editions = []
        edition_ids = []
        if "edition" not in table.fieldnames:
            try:
                edition = config.get("Edition", "title")
            except configparser.Error:
                edition = ""
                logging.warning("No edition stated. Please set manually.")
            finally:
                random.seed(edition)
                edition_id = cmi_object.add_edition(edition, bibl_type=edition_type)
                editions.append(edition)
                edition_ids.append(edition_id)
        for letter in table:
            if "edition" in table.fieldnames:
                del editions[:]
                del edition_ids[:]
                if not (letter["edition"] or args.all):
                    continue
                edition_values = letter["edition"].split(subdlm) if subdlm else [letter["edition"]]
                for edition in edition_values:
                    # By default use edition value as is
                    edition = edition.strip()
                    edition_id = cmi_object.get_id_by_title(edition)
                    if edition and not edition_id:
                        random.seed(edition)
                        edition_id = cmi_object.add_edition(edition, bibl_type=edition_type)
                    editions.append(edition)
                    edition_ids.append(edition_id)
            entry = Element("correspDesc")
            if args.line_numbers:
                entry.set("n", str(table.line_num))
            if any(edition_ids):
                # multiple entries needs te be separated by whitespace
                # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-att.global.source.html
                entry.set("source", "#" + " #".join(edition_ids))
            if "key" in table.fieldnames and letter["key"]:
                if not edition:
                    logging.error("Key without edition in line %s", table.line_num)
                else:
                    if str(letter["key"]).startswith("http"):
                        entry.set("ref", str(letter["key"]).strip())
                    else:
                        entry.set("key", str(letter["key"]).strip())

            for correnspondent in Correspondents:
                if (
                    letter[correnspondent]
                    or (correnspondent + "Place" in table.fieldnames and letter[correnspondent + "Place"])
                    or (correnspondent + "Date" in table.fieldnames and letter[correnspondent + "Date"])
                ):
                    action = cmi_object.create_corresp_action(correnspondent=correnspondent, letter=letter)
                    entry.append(action)
                else:
                    logging.info("No information on %s in line %s", correnspondent, table.line_num)

            entry.set("xml:id", cmi_object.generate_id("letter"))
            if args.notes:
                if ("note" in table.fieldnames) and letter["note"]:
                    note = SubElement(entry, "note")
                    note.set("xml:id", cmi_object.generate_id("note"))
                    note.text = str(letter["note"])
            if entry.find("*") is not None:
                cmi_object.profile_desc.append(entry)

    cmi_object.replace_short_titles(config)

    # save cmi to file
    if args.output:
        letters_xml = Path(args.output)
    else:
        letters_xml = letters_csv.with_suffix(".xml")

    cmi_object.save_to_file(letters_xml)
