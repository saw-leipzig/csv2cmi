#!/usr/bin/env python3
# csv2cmi
#
# Copyright (c) 2015-2019 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

import argparse
import configparser
import logging
import random
import string
import uuid
import urllib.request
from csv import DictReader
from datetime import datetime
from os import path
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree

__license__ = "MIT"
__version__ = '2.1.0-beta'

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
        exit()
else:
    subdlm = None


def checkIsodate(dateString):
    """Check if a string is from datatype teidata.temporal.iso."""
    try:
        datetime.strptime(dateString, '%Y-%m-%d')
        return True
    except ValueError:
        try:
            datetime.strptime(dateString, '%Y-%m')
            return True
        except ValueError:
            try:
                datetime.strptime(dateString, '%Y')
                return True
            except ValueError:
                return False


def checkDatableW3C(dateString):
    """Check if a string is from datatype teidata.temporal.w3c."""
    # handle negative dates
    if dateString.startswith('-') and len(dateString) > 4 and dateString[1].isdigit():
        dateString = dateString[1:]
    if checkIsodate(dateString):
        return True
    else:
        # handle dates without year
        try:
            datetime.strptime(dateString, '--%m-%d')
            return True
        except ValueError:
            try:
                datetime.strptime(dateString, '--%m')
                return True
            except ValueError:
                try:
                    datetime.strptime(dateString, '---%d')
                    return True
                except ValueError:
                    return False


def checkConnectivity():
    try:
        urllib.request.urlopen('http://193.175.100.220', timeout=1)
        return True
    except urllib.error.URLError:
        logging.error('No internet connection')
        return False


def createTextstructure():
    """Create an empty TEI text body."""
    text = Element('text')
    body = SubElement(text, 'body')
    SubElement(body, 'p')
    return text


def createFileDesc(config):
    """Create a TEI file description from config file."""
    fileDesc = Element('fileDesc')
    # title statement
    titleStmt = SubElement(fileDesc, 'titleStmt')
    title = SubElement(titleStmt, 'title')
    title.text = config.get(
        'Project', 'title', fallback='untitled letters project')
    random.seed(title.text)
    title.set('xml:id', generateID('title'))
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
    if not(list(publicationStmt)):
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
    return fileDesc


def createCorrespondent(nameString):
    if letter[nameString]:
        correspondents = []
        # Turning the cells of correspondent names and their IDs into lists since cells
        # can contain various correspondents split by an extra delimiter.
        # In that case it is essential to be able to call each by their index.
        if subdlm:
            persons = letter[nameString].split(subdlm)
            try:
                personIDs = letter[nameString + "ID"].split(subdlm)
            except KeyError:
                personIDs = []
        else:
            persons = [letter[nameString]]
            try:
                personIDs = [letter[nameString + "ID"]]
            except KeyError:
                personIDs = []
        for index, person in enumerate(persons):
            correspondent = Element('persName')
            person = str(person).strip()
            # assigning authority file IDs to their correspondents if provided
            if (index < len(personIDs)) and personIDs[index]:
                # by default complete GND-IDNs to full URI
                if 'http://' not in str(personIDs[index].strip()) and str(personIDs[index].strip())[:-2].isdigit():
                    logging.debug('Assigning ID %s to GND', str(
                        personIDs[index].strip()))
                    authID = 'https://d-nb.info/gnd/' + \
                        str(personIDs[index].strip())
                else:
                    authID = str(personIDs[index].strip())
                if profileDesc.findall('correspDesc/correspAction/persName[@ref="' + authID + '"]'):
                    correspondent = Element('persName')
                elif profileDesc.findall('correspDesc/correspAction/orgName[@ref="' + authID + '"]'):
                    correspondent = Element('orgName')
                elif connection:
                    if 'viaf' in authID:
                        try:
                            viafrdf = ElementTree(
                                file=urllib.request.urlopen(authID + '/rdf.xml'))
                        except urllib.error.HTTPError:
                            logging.error(
                                'Authority file not found for %sID in line %s', nameString, table.line_num)
                        except urllib.error.URLError:
                            logging.error('Failed to reach VIAF')
                        else:
                            viafrdf_root = viafrdf.getroot()
                            if viafrdf_root.find('./rdf:Description/rdf:type[@rdf:resource="http://schema.org/Organization"]', ns) is not None:
                                correspondent = Element('orgName')
                            elif viafrdf_root.find('./rdf:Description/rdf:type[@rdf:resource="http://schema.org/Person"]', ns) is not None:
                                correspondent = Element('persName')
                            else:
                                logging.warning(
                                    '%sID in line %s links to unprocessable authority file', nameString, table.line_num)
                    elif 'gnd' in authID:
                        try:
                            gndrdf = ElementTree(
                                file=urllib.request.urlopen(authID + '/about/rdf'))
                        except urllib.error.HTTPError:
                            logging.error(
                                'Authority file not found for %sID in line %s', nameString, table.line_num)
                        except urllib.error.URLError:
                            logging.error('Failed to reach GND')
                        except UnicodeEncodeError:
                            logging.error('Failed to encode %s', authID)
                        else:
                            corporatelike = (
                                'Corporate', 'Company', 'ReligiousAdministrativeUnit')
                            personlike = ('DifferentiatedPerson',
                                          'Royal', 'Family', 'Legendary')
                            gndrdf_root = gndrdf.getroot()
                            latestID = gndrdf_root[0].get(
                                '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                            if urllib.parse.urlparse(authID).path != urllib.parse.urlparse(latestID).path:
                                logging.info(
                                    '%s returns new ID %s', authID, latestID)
                            rdftype = gndrdf_root.find(
                                './/rdf:type', ns).get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                            if any(entity in rdftype for entity in corporatelike):
                                correspondent = Element('orgName')
                            elif any(entity in rdftype for entity in personlike):
                                correspondent = Element('persName')
                            else:
                                authID = ''
                                if 'UndifferentiatedPerson' in rdftype:
                                    logging.warning(
                                        '%sID in line %s links to undifferentiated Person', nameString, table.line_num)
                                else:
                                    logging.error(
                                        '%sID in line %s has wrong rdf:type', nameString, table.line_num)
                    elif 'loc' in authID:
                        try:
                            locrdf = ElementTree(
                                file=urllib.request.urlopen(authID + '.rdf'))
                        except urllib.error.HTTPError:
                            logging.error(
                                'Authority file not found for %sID in line %s', nameString, table.line_num)
                        except urllib.error.URLError:
                            logging.error('Failed to reach LOC')
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
                        authID = ''
                        logging.error(
                            'No proper authority record in line %s for %s', table.line_num, nameString)
                if authID:
                    correspondent.set('ref', authID)
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
    return(correspondents)


def createDate(dateString):
    """Convert an extended ISO date into a proper TEI element."""
    if not(dateString):
        return None
    date = Element('date')
    # normalize date
    normalizedDate = dateString.translate(dateString.maketrans('', '', '?~%'))
    if normalizedDate[-1] == 'X':
        normalizedDate = normalizedDate[0:-3]
        if normalizedDate[-1] == 'X':
            normalizedDate = normalizedDate[0:-3]
    if checkDatableW3C(normalizedDate):
        date.set('when', str(normalizedDate))
    elif normalizedDate.startswith('[') and normalizedDate.endswith(']'):
        # one of set
        dateList = normalizedDate[1:-1].split(",")
        dateFirst = dateList[0].split(".")[0]
        dateLast = dateList[-1].split(".")[-1]
        if dateFirst or dateLast:
            if checkDatableW3C(dateFirst):
                date.set('notBefore', str(dateFirst))
            if checkDatableW3C(dateLast):
                date.set('notAfter', str(dateLast))
    else:
        # time interval
        dateList = normalizedDate.split('/')
        if len(dateList) == 2 and (dateList[0] or dateList[1]):
            if checkDatableW3C(dateList[0]):
                date.set('from', str(dateList[0]))
            if checkDatableW3C(dateList[1]):
                date.set('to', str(dateList[1]))
    if date.attrib:
        if normalizedDate != dateString:
            date.set('cert', 'medium')
            logging.info(
                'Added @cert to <date> from line %s', table.line_num)
        return date
    else:
        raise ValueError('unable to parse \'%s\' as TEI date' % dateString)


def createPlaceName(placeNameText, placeNameRef):
    """Create a placeName element."""
    placeName = Element('placeName')
    placeNameText = placeNameText.strip()
    if placeNameText.startswith('[') and placeNameText.endswith(']'):
        placeName.set('evidence', 'conjecture')
        placeNameText = placeNameText[1:-1]
        logging.info('Added @evidence to <placeName> from line %s',
                     table.line_num)
    placeName.text = str(placeNameText)
    if placeNameRef:
        placeNameRef = placeNameRef.strip()
        if 'www.geonames.org' in placeNameRef:
            placeName.set('ref', str(placeNameRef))
        else:
            logging.warning('"%s" is no standardized GeoNames ID', placeNameRef)
    return placeName


def createEdition(biblText, biblType, biblID):
    """Create a new bibliographic entry."""
    bibl = Element('bibl')
    bibl.text = biblText
    bibl.set('type', biblType)
    bibl.set('xml:id', biblID)
    return bibl


def getEditonID(editionTitle):
    editionID = ''
    for bibl in sourceDesc.findall('bibl'):
        if editionTitle == bibl.text:
            editionID = bibl.get('xml:id')
            break
    return editionID


def generateID(id_prefix):
    if (id_prefix.strip() == ''):
        id_prefix = ''.join(random.choice(
            string.ascii_lowercase) for _ in range(8))
    fullID = id_prefix.strip() + '-' + ''.join(random.sample('0123456789abcdef', 4)) + '-' + \
        ''.join(random.sample('0123456789abcdef', 4)) + \
        '-' + ''.join(random.sample('0123456789abcdef', 10))
    return fullID


def generateUUID():
    """Generate a UUID."""
    UUID = str(uuid.UUID(bytes=bytes(random.getrandbits(8)
                                     for _ in range(16)), version=4))
    if UUID[0].isdigit():
        UUID = generateUUID()
    return UUID


def processDate(letter, correspondent):
    correspDate = Element('date')
    try:
        correspDate = createDate(letter[correspondent + 'Date'])
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


def processPlace(letter, correspondent):
    place, placeID = '', ''
    try:
        place = letter[correspondent + 'Place']
    except KeyError:
        pass
    else:
        try:
            placeID = letter[correspondent + 'PlaceID']
        except KeyError:
            pass
    return createPlaceName(place, placeID)


# simple test for file
try:
    open(args.filename, 'rt').close()
except FileNotFoundError:
    logging.error('File not found')
    exit()

# check internet connection via DNB
connection = checkConnectivity()

# read config file
config = configparser.ConfigParser()
# set default values
config['Project'] = {'editor': '', 'publisher': '', 'fileURL': path.splitext(
    path.basename(args.filename))[0] + '.xml'}

iniFilename = 'csv2cmi.ini'
try:
    config.read_file(open(path.join(path.dirname(args.filename), iniFilename)))
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
            exit()
    except configparser.NoOptionError:
        pass

# building cmi
# generating root element
root = Element('TEI')
root.set('xmlns', ns.get('tei'))
root.append(
    Comment(' Generated from table of letters with csv2cmi ' + __version__ + ' '))

# teiHeader
teiHeader = SubElement(root, 'teiHeader')
# create a file description from config file
fileDesc = createFileDesc(config)
teiHeader.append(fileDesc)
# container for bibliographic data
# global sourceDesc
sourceDesc = SubElement(fileDesc, 'sourceDesc')
# filling in correspondance meta-data
profileDesc = SubElement(teiHeader, 'profileDesc')

with open(args.filename, 'rt', encoding='utf-8') as letterTable:
    # global table
    table = DictReader(letterTable)
    logging.debug('Recognized columns: %s', table.fieldnames)
    if not ('sender' in table.fieldnames and 'addressee' in table.fieldnames):
        logging.error('No sender/addressee field in table')
        exit()
    editions = []
    editionIDs = []
    if not('edition' in table.fieldnames):
        try:
            edition = config.get('Edition', 'title')
        except configparser.Error:
            edition = ""
            logging.warning('No edition stated. Please set manually.')
        finally:
            random.seed(edition)
            editionID = generateUUID()
            sourceDesc.append(createEdition(edition, editionType, editionID))
            editions.append(edition)
            editionIDs.append(editionID)
    for letter in table:
        if ('edition' in table.fieldnames):
            del editions[:]
            del editionIDs[:]
            if subdlm:
                edition_values = letter['edition'].split(subdlm)
            else:
                edition_values = [letter['edition']]
            for edition in edition_values:
                # By default use edition value as is
                edition = edition.strip()
                editionID = getEditonID(edition)
                if not(edition or args.all):
                    continue
                if edition and not editionID:
                    random.seed(edition)
                    editionID = generateUUID()
                    sourceDesc.append(createEdition(
                        edition, editionType, editionID))
                editions.append(edition)
                editionIDs.append(editionID)
        entry = Element('correspDesc')
        if args.line_numbers:
            entry.set('n', str(table.line_num))
        if any(editionIDs):
            # multiple entries needs te be seperated by whitespace
            # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-att.global.source.html
            entry.set('source', '#' + ' #'.join(editionIDs))
        if 'key' in table.fieldnames and letter['key']:
            if not(edition):
                logging.error('Key without edition in line %s', table.line_num)
            else:
                if 'http://' in str(letter['key']):
                    entry.set('ref', str(letter['key']).strip())
                else:
                    entry.set('key', str(letter['key']).strip())

        # sender info block
        if letter['sender'] or ('senderPlace' in table.fieldnames and letter['senderPlace']) or letter['senderDate']:
            action = SubElement(entry, 'correspAction')
            action.set('xml:id', generateID('sender'))
            action.set('type', 'sent')

            # add name of sender
            if letter['sender']:
                correspondents = createCorrespondent('sender')
                for sender in correspondents:
                    action.append(sender)
            # add placeName
            senderPlace = processPlace(letter, "sender")
            if senderPlace.attrib or senderPlace.text:
                action.append(senderPlace)
            # add date
            senderDate = processDate(letter, "sender")
            if senderDate.attrib or senderDate.text:
                action.append(senderDate)
        else:
            logging.info('No information on sender in line %s', table.line_num)

        # addressee info block
        if letter['addressee'] or ('addresseePlace' in table.fieldnames and letter['addresseePlace']) or ('addresseeDate' in table.fieldnames and letter['addresseeDate']):
            action = SubElement(entry, 'correspAction')
            action.set('xml:id', generateID('addressee'))
            action.set('type', 'received')

            # add name of addressee
            if letter['addressee']:
                correspondents = createCorrespondent('addressee')
                for addressee in correspondents:
                    action.append(addressee)
            # add placeName
            addresseePlace = processPlace(letter, "addressee")
            if addresseePlace.attrib or addresseePlace.text:
                action.append(addresseePlace)
            # add date
            addresseeDate = processDate(letter, "addressee")
            if addresseeDate.attrib or addresseeDate.text:
                action.append(addresseeDate)
        else:
            logging.info('No information on addressee in line %s',
                         table.line_num)
        entry.set('xml:id', generateID('letter'))
        if args.notes:
            if ('note' in table.fieldnames) and letter['note']:
                note = SubElement(entry, 'note')
                note.set('xml:id', generateID('note'))
                note.text = str(letter['note'])
        if entry.find('*'):
            profileDesc.append(entry)

# replace short titles if configured
for bibl in sourceDesc.findall('bibl'):
    # Try to use bibliographic text as key for section in config file
    editionKey = bibl.text
    try:
        editionTitle = config.get(editionKey, 'title')
        try:
            editionType = config.get(editionKey, 'type')
        except configparser.NoOptionError:
            # if type is not set, use the default one
            pass
        bibl.text = editionTitle
        bibl.set('type', editionType)
    except configparser.NoOptionError:
        logging.warning(
            'Incomplete section %s in ini file. Title and type option must be set.', editionKey)
    except configparser.NoSectionError:
        # if there is no matching section, we assume that there shouldn't one
        pass


# generate empty body
root.append(createTextstructure())

# save cmi to file
tree = ElementTree(root)
if args.output:
    outFile = args.output
else:
    outFile = path.join(path.dirname(args.filename), path.splitext(
        path.basename(args.filename))[0] + '.xml')

try:
    tree.write(outFile, encoding="utf-8", xml_declaration=True, method="xml")
    print('CMI file written to', outFile)
except PermissionError:
    logging.error('Could not save the file due to insufficient permission')
