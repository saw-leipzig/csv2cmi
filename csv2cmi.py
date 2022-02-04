#!/usr/bin/env python3
# CSV2CMI
#
# Copyright (c) 2015-2020 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

import argparse
import configparser
import logging
import random
import string
import sys
import urllib.request
import uuid
from csv import DictReader
from datetime import datetime
from os import path
from xml.etree.ElementTree import Comment, Element, ElementTree, SubElement

__license__ = "MIT"
__version__ = '2.5.0'

# define log output
logging.basicConfig(format='%(levelname)s: %(message)s')
logs = logging.getLogger()

# define namespaces
ns = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
      'tei': 'http://www.tei-c.org/ns/1.0'}

# define arguments
parser = argparse.ArgumentParser(
    description='convert tables of letters to CMI')
parser.add_argument('filename', help='input file (.csv)')
parser.add_argument('-a', '--all',
                    help='include unedited letters', action='store_true')
parser.add_argument('-n', '--notes', help='transfer notes',
                    action='store_true')
parser.add_argument('-o', '--output', metavar="FILE", help='output file name')
parser.add_argument('-v', '--verbose',
                    help='increase output verbosity', action='store_true')
parser.add_argument('--line-numbers',
                    help='add line numbers', action='store_true')
parser.add_argument('--version', action='version',
                    version='%(prog)s ' + __version__)
parser.add_argument('--extra-delimiter',
                    help='delimiter for different values within cells')


def check_connectivity() -> bool:
    try:
        urllib.request.urlopen('http://193.175.100.220', timeout=1)
        return True
    except urllib.error.URLError:
        logging.error('No internet connection')
        return False


def check_isodate(date_string):
    """Check if a string is from datatype teidata.temporal.iso."""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        try:
            datetime.strptime(date_string, '%Y-%m')
            return True
        except ValueError:
            try:
                datetime.strptime(date_string, '%Y')
                return True
            except ValueError:
                return False


def check_datable_w3c(date_string):
    """Check if a string is from datatype teidata.temporal.w3c."""
    # handle negative dates
    if date_string.startswith('-') and len(date_string) > 4 and date_string[1].isdigit():
        date_string = date_string[1:]
    if check_isodate(date_string):
        return True
    # handle dates without year
    try:
        datetime.strptime(date_string, '--%m-%d')
        return True
    except ValueError:
        try:
            datetime.strptime(date_string, '--%m')
            return True
        except ValueError:
            try:
                datetime.strptime(date_string, '---%d')
                return True
            except ValueError:
                return False


def create_date(date_string: str) -> Element:
    """Convert an EDTF date into a proper TEI element."""
    if not date_string:
        return None
    tei_date = Element('date')
    # normalize date
    normalized_date = date_string.translate(
        date_string.maketrans('', '', '?~%'))
    if len(normalized_date) > 4 and normalized_date[-1] == 'X':
        # remove day and month with unspecified digits
        normalized_date = normalized_date[0:-3]
        if normalized_date[-1] == 'X':
            normalized_date = normalized_date[0:-3]
    if normalized_date[-1] == 'X':
        # change year with unspecified digits to interval
        normalized_date = normalized_date.replace(
            'X', '0') + '/' + normalized_date.replace('X', '9')
    if check_datable_w3c(normalized_date):
        tei_date.set('when', str(normalized_date))
    elif normalized_date.startswith('[') and normalized_date.endswith(']'):
        # one of set
        date_list = normalized_date[1:-1].split(",")
        date_first = date_list[0].split(".")[0]
        date_last = date_list[-1].split(".")[-1]
        if date_first or date_last:
            if check_datable_w3c(date_first):
                tei_date.set('notBefore', str(date_first))
            if check_datable_w3c(date_last):
                tei_date.set('notAfter', str(date_last))
    else:
        # time interval
        date_list = normalized_date.split('/')
        if len(date_list) == 2 and (date_list[0] or date_list[1]):
            if check_datable_w3c(date_list[0]):
                tei_date.set('from', str(date_list[0]))
            if check_datable_w3c(date_list[1]):
                tei_date.set('to', str(date_list[1]))
    if tei_date.attrib:
        if normalized_date != date_string:
            tei_date.set('cert', 'medium')
            logging.info(
                'Added @cert to <date> from line %s', table.line_num)
        return tei_date
    raise ValueError('unable to parse \'%s\' as TEI date' % date_string)


class CSV2CMI():
    """Transform a table of letters into the CMI format."""

    def __init__(self):
        """Create an empty TEI file."""
        self.cmi = Element('TEI')
        self.cmi.set('xmlns', ns.get('tei'))
        self.cmi.append(
            Comment(' Generated from table of letters with CSV2CMI ' + __version__ + ' '))
        # TEI header
        tei_header = SubElement(self.cmi, 'teiHeader')
        self.file_desc = SubElement(tei_header, 'fileDesc')
        self.profile_desc = SubElement(tei_header, 'profileDesc')
        # TEI body
        text = SubElement(self.cmi, 'text')
        tei_body = SubElement(text, 'body')
        SubElement(tei_body, 'p')

    def create_file_desc(self, config):
        """Create a TEI file description from config file."""
        fileDesc = cmi_object.file_desc
        # title statement
        titleStmt = SubElement(fileDesc, 'titleStmt')
        title = SubElement(titleStmt, 'title')
        title.text = config.get(
            'Project', 'title', fallback='untitled letters project')
        random.seed(title.text)
        title.set('xml:id', self.generate_id('title'))
        editors = ['']
        editors = config.get('Project', 'editor').splitlines()
        for entity in editors:
            SubElement(titleStmt, 'editor').text = entity
        if len(list(titleStmt)) == 1:
            logging.warning('Editor missing')
            SubElement(titleStmt, 'editor')
        # publication statement
        publicationStmt = SubElement(fileDesc, 'publicationStmt')
        publishers = config.get('Project', 'publisher').splitlines()
        for entity in publishers:
            SubElement(publicationStmt, 'publisher').text = entity
        if not list(publicationStmt):
            for editor in titleStmt.findall('editor'):
                SubElement(publicationStmt, 'publisher').text = editor.text
        idno = SubElement(publicationStmt, 'idno')
        idno.set('type', 'url')
        idno.text = config.get('Project', 'fileURL')
        SubElement(publicationStmt, 'date').set(
            'when', str(datetime.now().isoformat()))
        availability = SubElement(publicationStmt, 'availability')
        licence = SubElement(availability, 'licence')
        licence.set('target', 'https://creativecommons.org/licenses/by/4.0/')
        licence.text = 'This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0'
        # The CC-BY licence may not apply to the final CMI file
        #licence.set('target', 'https://creativecommons.org/publicdomain/zero/1.0/')
        #licence.text = 'This file is licensed under a Creative Commons Zero 1.0 License.'
        return

    def create_correspondent(self, nameString):
        if letter[nameString]:
            correspondents = []
            # Turning the cells of correspondent names and their IDs into lists since cells
            # can contain various correspondents split by an extra delimiter.
            # In that case it is essential to be able to call each by their index.
            if subdlm:
                persons = letter[nameString].split(subdlm)
                try:
                    person_ids = letter[nameString + "ID"].split(subdlm)
                except KeyError:
                    person_ids = []
            else:
                persons = [letter[nameString]]
                try:
                    person_ids = [letter[nameString + "ID"]]
                except KeyError:
                    person_ids = []
            for index, person in enumerate(persons):
                correspondent = Element('persName')
                person = str(person).strip()
                # assigning authority file IDs to their correspondents if provided
                if (index < len(person_ids)) and person_ids[index]:
                    # by default complete GND-IDNs to full URI
                    if not str(person_ids[index].strip()).startswith('http') and str(person_ids[index].strip())[:-2].isdigit():
                        logging.debug('Assigning ID %s to GND', str(
                            person_ids[index].strip()))
                        authority_file_uri = 'https://d-nb.info/gnd/' + \
                            str(person_ids[index].strip())
                    else:
                        authority_file_uri = str(person_ids[index].strip())
                    if cmi_object.profile_desc.findall('correspDesc/correspAction/persName[@ref="' + authority_file_uri + '"]'):
                        correspondent = Element('persName')
                    elif cmi_object.profile_desc.findall('correspDesc/correspAction/orgName[@ref="' + authority_file_uri + '"]'):
                        correspondent = Element('orgName')
                    elif connection:
                        if 'viaf' in authority_file_uri:
                            try:
                                viafrdf = ElementTree(
                                    file=urllib.request.urlopen(authority_file_uri + '/rdf.xml'))
                            except urllib.error.HTTPError:
                                logging.error(
                                    'Authority file not found for %sID in line %s', nameString, table.line_num)
                            except urllib.error.URLError as e:
                                logging.error(
                                    'Failed to reach VIAF (%s)', str(e.reason))
                            else:
                                viafrdf_root = viafrdf.getroot()
                                if viafrdf_root.find('./rdf:Description/rdf:type[@rdf:resource="http://schema.org/Organization"]', ns) is not None:
                                    correspondent = Element('orgName')
                                elif viafrdf_root.find('./rdf:Description/rdf:type[@rdf:resource="http://schema.org/Person"]', ns) is not None:
                                    correspondent = Element('persName')
                                else:
                                    logging.warning(
                                        '%sID in line %s links to unprocessable authority file', nameString, table.line_num)
                        elif 'gnd' in authority_file_uri:
                            try:
                                gndrdf = ElementTree(
                                    file=urllib.request.urlopen(authority_file_uri + '/about/rdf'))
                            except urllib.error.HTTPError:
                                logging.error(
                                    'Authority file not found for %sID in line %s', nameString, table.line_num)
                            except urllib.error.URLError as e:
                                logging.error(
                                    'Failed to reach GND (%s)', str(e.reason))
                            except UnicodeEncodeError:
                                logging.error(
                                    'Failed to encode %s', authority_file_uri)
                            else:
                                corporatelike = (
                                    'Corporate', 'Company', 'ReligiousAdministrativeUnit')
                                personlike = ('DifferentiatedPerson',
                                              'Royal', 'Family', 'Legendary')
                                gndrdf_root = gndrdf.getroot()
                                latestID = gndrdf_root[0].get(
                                    '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                                if urllib.parse.urlparse(authority_file_uri).path != urllib.parse.urlparse(latestID).path:
                                    logging.info(
                                        '%s returns new ID %s', authority_file_uri, latestID)
                                rdftype = gndrdf_root.find(
                                    './/rdf:type', ns).get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                                if any(entity in rdftype for entity in corporatelike):
                                    correspondent = Element('orgName')
                                elif any(entity in rdftype for entity in personlike):
                                    correspondent = Element('persName')
                                else:
                                    authority_file_uri = ''
                                    if 'UndifferentiatedPerson' in rdftype:
                                        logging.warning(
                                            '%sID in line %s links to undifferentiated Person', nameString, table.line_num)
                                    else:
                                        logging.error(
                                            '%sID in line %s has wrong rdf:type', nameString, table.line_num)
                        elif 'loc' in authority_file_uri:
                            try:
                                locrdf = ElementTree(
                                    file=urllib.request.urlopen(authority_file_uri + '.rdf'))
                            except urllib.error.HTTPError:
                                logging.error(
                                    'Authority file not found for %sID in line %s', nameString, table.line_num)
                            except urllib.error.URLError as e:
                                logging.error(
                                    'Failed to reach LOC (%s)', str(e.reason))
                            else:
                                locrdf_root = locrdf.getroot()
                                if locrdf_root.find('.//rdf:type[@rdf:resource="http://id.loc.gov/ontologies/bibframe/Organization"]', ns) is not None:
                                    correspondent = Element('orgName')
                                elif locrdf_root.find('.//rdf:type[@rdf:resource="http://id.loc.gov/ontologies/bibframe/Person"]', ns) is not None:
                                    correspondent = Element('persName')
                                else:
                                    logging.warning(
                                        '%sID in line %s links to unprocessable authority file', nameString, table.line_num)
                        else:
                            authority_file_uri = ''
                            logging.error(
                                'No proper authority record in line %s for %s', table.line_num, nameString)
                    if authority_file_uri:
                        correspondent.set('ref', authority_file_uri)
                else:
                    logging.debug('ID for "%s" missing in line %s',
                                  person, table.line_num)
                if person.startswith('[') and person.endswith(']'):
                    correspondent.set('evidence', 'conjecture')
                    person = person[1:-1]
                    logging.info('Added @evidence to <%s> from line %s', correspondent.tag,
                                 table.line_num)
                correspondent.text = person
                correspondents.append(correspondent)
        return correspondents

    def create_place_name(self, place_name_text: str, geonames_uri: str) -> Element:
        """Create a placeName element."""
        place_name = Element('placeName')
        place_name_text = place_name_text.strip()
        if place_name_text.startswith('[') and place_name_text.endswith(']'):
            place_name.set('evidence', 'conjecture')
            place_name_text = place_name_text[1:-1]
            logging.info('Added @evidence to <placeName> from line %s',
                         table.line_num)
        place_name.text = str(place_name_text)
        if geonames_uri:
            geonames_uri = geonames_uri.strip()
            if 'www.geonames.org' in geonames_uri:
                place_name.set('ref', str(geonames_uri))
            else:
                logging.warning(
                    '"%s" is no GeoNames URI', geonames_uri)
        return place_name

    def createEdition(self, biblText: str, biblType: str, biblID: str) -> Element:
        """Create a new bibliographic entry."""
        tei_bibl = Element('bibl')
        tei_bibl.text = biblText
        tei_bibl.set('type', biblType)
        tei_bibl.set('xml:id', biblID)
        return tei_bibl

    def getEditonID(self, edition_title: str) -> str:
        """Get the ID for an edition by title."""
        edition_id = ''
        for bibl in sourceDesc.findall('bibl'):
            if edition_title == bibl.text:
                edition_id = bibl.get('xml:id')
                break
        return edition_id

    def generate_id(self, id_prefix: str) -> str:
        if id_prefix.strip() == '':
            id_prefix = ''.join(random.choice(
                string.ascii_lowercase) for _ in range(8))
        generated_id = id_prefix.strip() + '-' + ''.join(random.sample('0123456789abcdef', 4)) + '-' + \
            ''.join(random.sample('0123456789abcdef', 4)) + \
            '-' + ''.join(random.sample('0123456789abcdef', 10))
        return generated_id

    def generate_uuid(self) -> str:
        """Generate a UUID of type xs:ID."""
        generated_uuid = str(uuid.UUID(bytes=bytes(random.getrandbits(8)
                                                   for _ in range(16)), version=4))
        if generated_uuid[0].isdigit():
            generated_uuid = self.generate_uuid()
        return generated_uuid

    def process_date(self, letter, correspondent):
        correspDate = Element('date')
        try:
            correspDate = create_date(letter[correspondent + 'Date'])
        except (KeyError, TypeError):
            pass
        except ValueError:
            logging.warning(
                'Could not parse %sDate in line %s', correspondent, table.line_num)
        else:
            if correspDate is None:
                correspDate = Element('date')
        try:
            correspDate.text = letter[correspondent + 'DateText'].strip()
        except (KeyError, TypeError):
            pass
        return correspDate

    def process_place(self, letter, correspondent_type: str):
        """Process place."""
        place, placeID = '', ''
        try:
            place = letter[correspondent_type + 'Place']
        except KeyError:
            pass
        else:
            try:
                placeID = letter[correspondent_type + 'PlaceID']
            except KeyError:
                pass
        return self.create_place_name(place, placeID)


if __name__ == "__main__":
    args = parser.parse_args()

    # set verbosity
    if args.verbose:
        logs.setLevel('INFO')

    # set extra delimiter
    if args.extra_delimiter:
        if len(args.extra_delimiter) == 1:
            subdlm = args.extra_delimiter
        else:
            logging.error('Delimiter has to be a single character')
            sys.exit(1)
    else:
        subdlm = None

    # simple test for file
    try:
        open(args.filename, 'rt').close()
    except FileNotFoundError:
        logging.error('File not found')
        sys.exit(1)

    cmi_object = CSV2CMI()

    # check internet connection via DNB
    connection = check_connectivity()

    # read config file
    config = configparser.ConfigParser()
    # set default values
    config['Project'] = {'editor': '', 'publisher': '', 'fileURL': path.splitext(
        path.basename(args.filename))[0] + '.xml'}

    iniFilename = 'csv2cmi.ini'
    try:
        config.read_file(
            open(path.join(path.dirname(args.filename), iniFilename)))
    except IOError:
        try:
            config.read_file(open(iniFilename))
        except IOError:
            logging.error('No configuration file found')

    # set type of edition
    editionType = 'print'
    if ('Edition' in config) and ('type' in config['Edition']):
        if config.get('Edition', 'type') in ['print', 'hybrid', 'online']:
            editionType = config.get('Edition', 'type')

    # set extra delimiter
    if not subdlm:
        try:
            subdlm = config.get('Project', 'extra-delimiter')
            if len(subdlm) > 1:
                logging.error('Delimiter has to be a single character')
                sys.exit(1)
        except configparser.NoOptionError:
            pass

    # building cmi
    # create a file description from config file
    cmi_object.create_file_desc(config)
    sourceDesc = SubElement(CSV2CMI.file_desc, 'sourceDesc')

    with open(args.filename, 'rt', encoding='utf-8') as letterTable:
        # global table
        table = DictReader(letterTable)
        logging.debug('Recognized columns: %s', table.fieldnames)
        if not ('sender' in table.fieldnames and 'addressee' in table.fieldnames):
            logging.error('No sender/addressee field in table')
            sys.exit(1)
        editions = []
        edition_ids = []
        if 'edition' not in table.fieldnames:
            try:
                edition = config.get('Edition', 'title')
            except configparser.Error:
                edition = ""
                logging.warning('No edition stated. Please set manually.')
            finally:
                random.seed(edition)
                edition_id = cmi_object.generate_uuid()
                sourceDesc.append(cmi_object.createEdition(
                    edition, editionType, edition_id))
                editions.append(edition)
                edition_ids.append(edition_id)
        for letter in table:
            if 'edition' in table.fieldnames:
                del editions[:]
                del edition_ids[:]
                if subdlm:
                    edition_values = letter['edition'].split(subdlm)
                else:
                    edition_values = [letter['edition']]
                for edition in edition_values:
                    # By default use edition value as is
                    edition = edition.strip()
                    edition_id = cmi_object.getEditonID(edition)
                    if not(edition or args.all):
                        continue
                    if edition and not edition_id:
                        random.seed(edition)
                        edition_id = cmi_object.generate_uuid()
                        sourceDesc.append(cmi_object.createEdition(
                            edition, editionType, edition_id))
                    editions.append(edition)
                    edition_ids.append(edition_id)
            entry = Element('correspDesc')
            if args.line_numbers:
                entry.set('n', str(table.line_num))
            if any(edition_ids):
                # multiple entries needs te be seperated by whitespace
                # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-att.global.source.html
                entry.set('source', '#' + ' #'.join(edition_ids))
            if 'key' in table.fieldnames and letter['key']:
                if not edition:
                    logging.error(
                        'Key without edition in line %s', table.line_num)
                else:
                    if str(letter['key']).startswith('http'):
                        entry.set('ref', str(letter['key']).strip())
                    else:
                        entry.set('key', str(letter['key']).strip())

            # sender info block
            if letter['sender'] or ('senderPlace' in table.fieldnames and letter['senderPlace']) or letter['senderDate']:
                action = SubElement(entry, 'correspAction')
                action.set('xml:id', cmi_object.generate_id('sender'))
                action.set('type', 'sent')

                # add name of sender
                if letter['sender']:
                    correspondents = cmi_object.create_correspondent('sender')
                    for sender in correspondents:
                        action.append(sender)
                # add place_name
                senderPlace = cmi_object.process_place(letter, "sender")
                if senderPlace.attrib or senderPlace.text:
                    action.append(senderPlace)
                # add date
                senderDate = cmi_object.process_date(letter, "sender")
                if senderDate.attrib or senderDate.text:
                    action.append(senderDate)
            else:
                logging.info(
                    'No information on sender in line %s', table.line_num)

            # addressee info block
            if letter['addressee'] or ('addresseePlace' in table.fieldnames and letter['addresseePlace']) or ('addresseeDate' in table.fieldnames and letter['addresseeDate']):
                action = SubElement(entry, 'correspAction')
                action.set('xml:id', cmi_object.generate_id('addressee'))
                action.set('type', 'received')

                # add name of addressee
                if letter['addressee']:
                    correspondents = cmi_object.create_correspondent('addressee')
                    for addressee in correspondents:
                        action.append(addressee)
                # add place_name
                addresseePlace = cmi_object.process_place(letter, "addressee")
                if addresseePlace.attrib or addresseePlace.text:
                    action.append(addresseePlace)
                # add date
                addresseeDate = cmi_object.process_date(letter, "addressee")
                if addresseeDate.attrib or addresseeDate.text:
                    action.append(addresseeDate)
            else:
                logging.info('No information on addressee in line %s',
                             table.line_num)
            entry.set('xml:id', cmi_object.generate_id('letter'))
            if args.notes:
                if ('note' in table.fieldnames) and letter['note']:
                    note = SubElement(entry, 'note')
                    note.set('xml:id', cmi_object.generate_id('note'))
                    note.text = str(letter['note'])
            if entry.find('*'):
                cmi_object.profile_desc.append(entry)

    # replace short titles, if configured
    for bibl in sourceDesc.findall('bibl'):
        # Try to use bibliographic text as key for section in config file
        editionKey = bibl.text
        try:
            edition_title = config.get(editionKey, 'title')
            try:
                editionType = config.get(editionKey, 'type')
            except configparser.NoOptionError:
                # if type is not set, use the default one
                pass
            bibl.text = edition_title
            bibl.set('type', editionType)
        except configparser.NoOptionError:
            logging.warning(
                'Incomplete section %s in ini file. Title and type option must be set.', editionKey)
        except configparser.NoSectionError:
            # if there is no matching section, we assume that there shouldn't be one
            pass

    # save cmi to file
    tree = ElementTree(CSV2CMI.cmi)
    if args.output:
        outFile = args.output
    else:
        outFile = path.join(path.dirname(args.filename), path.splitext(
            path.basename(args.filename))[0] + '.xml')

    try:
        tree.write(outFile, encoding="utf-8",
                   xml_declaration=True, method="xml")
        print('CMI file written to', outFile)
        sys.exit(0)
    except PermissionError:
        logging.error('Could not save the file due to insufficient permission')
        sys.exit(1)
