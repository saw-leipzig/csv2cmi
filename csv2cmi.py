#!/usr/bin/env python3
# csv2cmi
#
# Copyright (c) 2015-2018 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

# needs Python3
import argparse
import configparser
import logging
import os
import random
import string
import urllib.request
from csv import DictReader
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree

__license__ = "MIT"
__version__ = '2.0.0-alpha'

# define log output
logging.basicConfig(format='%(levelname)s: %(message)s')
logs = logging.getLogger()

# define RDF namespace
rdf = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

# define arguments
parser = argparse.ArgumentParser(
    description='convert tables of letters to CMI')
parser.add_argument('filename', help='input file (.csv)')
parser.add_argument('-a', '--all',
                    help='include unedited letters', action='store_true')
parser.add_argument('-n', '--notes', help='transfer notes',
                    action='store_true')
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
    if checkIsodate(dateString):
        return True
    else:
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
    # creates an empty TEI text body
    text = Element('text')
    body = SubElement(text, 'body')
    SubElement(body, 'p')
    return text


def createFileDesc(config):
    # creates a file description from config file
    fileDesc = Element('fileDesc')
    # title statement
    titleStmt = SubElement(fileDesc, 'titleStmt')
    title = SubElement(titleStmt, 'title')
    title.set('xml:id', createID('title'))
    title.text = config.get(
        'Project', 'title', fallback='untitled letters project')
    editor = SubElement(titleStmt, 'editor')
    editor.text = config.get('Project', 'editor')
    # publication statement
    publicationStmt = SubElement(fileDesc, 'publicationStmt')
    publisher = SubElement(publicationStmt, 'publisher')
    if (config.get('Project', 'publisher')):
        publisher.text = config.get('Project', 'publisher')
    else:
        publisher.text = config.get('Project', 'editor')
    idno = SubElement(publicationStmt, 'idno')
    idno.set('type', 'url')
    idno.text = config.get('Project', 'fileURL')
    date = SubElement(publicationStmt, 'date')
    date.set('when', str(datetime.now().isoformat()))
    availability = SubElement(publicationStmt, 'availability')
    licence = SubElement(availability, 'licence')
    licence.set('target', 'https://creativecommons.org/licenses/by/4.0/')
    licence.text = 'This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0'
    return fileDesc


def createCorrespondent(namestring):
    if letter[namestring]:
        correspondents = []
        # Turning the cells of correspondent names and their IDs into lists since cells
        # can contain various correspondents split by an extra delimiter.
        # In that case it is essential to be able to call each by their index.
        if subdlm:
            persons = letter[namestring].split(subdlm)
            personIDs = letter[namestring + "ID"].split(subdlm)
        else:
            persons = []
            persons.append(letter[namestring].strip())
            personIDs = []
            personIDs.append(letter[namestring + "ID"])

        for index, person in enumerate(persons):
            person = str(person).strip()
            # assigning authority file IDs to their correspondents if provided
            if personIDs[index] and (index < len(personIDs)):
                if 'http://' not in str(personIDs[index].strip()):
                    logging.debug('Assigning ID %s to GND', str(
                        personIDs[index].strip()))
                    authID = 'http://d-nb.info/gnd/' + \
                        str(personIDs[index].strip())
                else:
                    authID = str(personIDs[index].strip())
                if connection and (profileDesc.find('correspDesc/correspAction/persName[@ref="' + authID + '"]') == None):
                    if 'viaf' in authID:
                        try:
                            viafrdf = ElementTree(
                                file=urllib.request.urlopen(authID + '/rdf.xml'))
                        except urllib.error.HTTPError:
                            logging.error(
                                'Authority file not found for %sID in line %s', namestring, table.line_num)
                            correspondent = Element('persName')
                            authID = ''
                        except urllib.error.URLError:
                            logging.error('Failed to reach VIAF')
                            correspondent = Element('persName')
                        else:
                            viafrdf_root = viafrdf.getroot()
                            if viafrdf_root.find('./rdf:Description/rdf:type[@rdf:resource="http://schema.org/Organization"]', rdf) is not None:
                                correspondent = Element('orgName')
                            elif viafrdf_root.find('./rdf:Description/rdf:type[@rdf:resource="http://schema.org/Person"]', rdf) is not None:
                                correspondent = Element('persName')
                            else:
                                logging.warning(
                                    '%sID in line %s links to unprocessable authority file', namestring, table.line_num)
                                correspondent = Element('persName')
                                authID = ''
                    elif 'gnd' in authID:
                        try:
                            gndrdf = ElementTree(
                                file=urllib.request.urlopen(authID + '/about/rdf'))
                        except urllib.error.HTTPError:
                            logging.error(
                                'Authority file not found for %sID in line %s', namestring, table.line_num)
                            correspondent = Element('persName')
                            authID = ''
                        except urllib.error.URLError:
                            logging.error('Failed to reach GND')
                            correspondent = Element('persName')
                        except UnicodeEncodeError:
                            print(authID)
                        else:
                            gndrdf_root = gndrdf.getroot()
                            rdftype = gndrdf_root.find(
                                './/rdf:type', rdf).get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                            if 'Corporate' in rdftype:
                                correspondent = Element('orgName')
                            elif 'DifferentiatedPerson' in rdftype:
                                correspondent = Element('persName')
                            else:
                                correspondent = Element('persName')
                                logging.error(
                                    '%sID in line %s has wrong rdf:type', namestring, table.line_num)
                            if 'UndifferentiatedPerson' in rdftype:
                                logging.warning(
                                    '%sID in line %s links to undifferentiated Person', namestring, table.line_num)
                                authID = ''
                    elif 'loc' in authID:
                        try:
                            locrdf = ElementTree(
                                file=urllib.request.urlopen(authID + '.rdf'))
                        except urllib.error.HTTPError:
                            logging.error(
                                'Authority file not found for %sID in line %s', namestring, table.line_num)
                            correspondent = Element('persName')
                            authID = ''
                        except urllib.error.URLError:
                            logging.error('Failed to reach LOC')
                            correspondent = Element('persName')
                        else:
                            locrdf_root = locrdf.getroot()
                            if locrdf_root.find('.//rdf:type[@rdf:resource="http://id.loc.gov/ontologies/bibframe/Organization"]', rdf) is not None:
                                correspondent = Element('orgName')
                            elif locrdf_root.find('.//rdf:type[@rdf:resource="http://id.loc.gov/ontologies/bibframe/Person"]', rdf) is not None:
                                correspondent = Element('persName')
                            else:
                                logging.warning(
                                    '%sID in line %s links to unprocessable authority file', namestring, table.line_num)
                                correspondent = Element('persName')
                                authID = ''
                    else:
                        logging.error(
                            'No proper authority record in line %s for %s', table.line_num, namestring)
                        correspondent = Element(action, 'persName')
                        authID = ''
                else:
                    correspondent = Element('persName')
                if authID:
                    correspondent.set('ref', authID)
            else:
                logging.debug('ID for "%s" missing in line %s',
                              person, table.line_num)
                correspondent = Element('persName')
            if person.startswith('[') and person.endswith(']'):
                correspondent.set('evidence', 'conjecture')
                person = person[1:-1]
                logging.info('Added @evidence to <%s> from line %s', correspondent.tag,
                             table.line_num)
            correspondent.text = person
            correspondents.append(correspondent)
    return(correspondents)


def createDate(dateString):
    date = Element('date')
    # normalize date
    normalizedDate = dateString.translate(dateString.maketrans('', '', '?~%'))
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
        return None


def createPlaceName(placeString):
    """Create a placeName element."""
    placeName = Element('placeName')
    letter[placeString] = letter[placeString].strip()
    if letter[placeString].startswith('[') and letter[placeString].endswith(']'):
        placeName.set('evidence', 'conjecture')
        letter[placeString] = letter[placeString][1:-1]
        logging.info('Added @evidence to <placeName> from line %s',
                     table.line_num)
    placeName.text = str(letter[placeString])
    if (placeString + 'ID' in table.fieldnames) and (letter[placeString + 'ID']):
        letter[placeString + 'ID'] = letter[placeString + 'ID'].strip()
        if 'www.geonames.org' in letter[placeString + 'ID']:
            placeName.set('ref', str(letter[placeString + 'ID']))
        else:
            logging.warning('No standardized %sID in line %s',
                            placeString, table.line_num)
    else:
        logging.debug('ID for "%s" missing in line %s', letter[
            placeString], table.line_num)
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


def createID(id_prefix):
    if (id_prefix.strip() == ''):
        id_prefix = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(8))
    fullID = id_prefix.strip() + '_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(
        8)) + '_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return fullID


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
config['Project'] = {'editor': '', 'publisher': '', 'fileURL': os.path.splitext(
    os.path.basename(args.filename))[0] + '.xml'}
try:
    config.read_file(open('csv2cmi.ini'))
except IOError:
    logging.error('No configuration file found')

# set type of edition
editionType = 'print'
if ('Edition' in config) and ('type' in config['Edition']):
    if config.get('Edition', 'type') in ['print', 'hybrid', 'online']:
        editionType = config.get('Edition', 'type')

# building cmi
# generating root element
root = Element('TEI')
root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
root.append(
    Comment(' Generated from table of letters with csv2cmi ' + __version__ + ' '))

# teiHeader
teiHeader = SubElement(root, 'teiHeader')
# create a file description from config file
fileDesc = createFileDesc(config)
teiHeader.append(fileDesc)
# container for bibliographic data
global sourceDesc
sourceDesc = SubElement(fileDesc, 'sourceDesc')
# filling in correspondance meta-data
profileDesc = SubElement(teiHeader, 'profileDesc')

with open(args.filename, 'rt') as letterTable:
    global table
    table = DictReader(letterTable)
    logging.debug('Recognized columns: %s', table.fieldnames)
    if not ('sender' in table.fieldnames and 'addressee' in table.fieldnames):
        logging.error('No sender/addressee field in table')
        exit()
    edition = ''
    if not('edition' in table.fieldnames):
        try:
            edition = config.get('Edition', 'title')
        except configparser.Error:
            logging.warning('No edition stated. Please set manually.')
        sourceDesc.append(createEdition(edition, editionType, createID('edition')))
    for letter in table:
        if ('edition' in table.fieldnames):
            edition = letter['edition'].strip()
            editionID = getEditonID(edition)
            if not(edition or args.all):
                continue
            if edition and not editionID:
                editionID = createID('edition')
                sourceDesc.append(createEdition(edition, editionType, editionID))
        entry = Element('correspDesc')
        if args.line_numbers:
            entry.set('n', str(table.line_num))
        entry.set('xml:id', createID('letter'))
        if edition:
            entry.set('source', '#' + editionID)
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
            action.set('xml:id', createID('sender'))
            action.set('type', 'sent')

            # add persName or orgName
            if letter['sender']:
                correspondents = createCorrespondent('sender')
                for sender in correspondents:
                    action.append(sender)
            # add placeName
            if ('senderPlace' in table.fieldnames) and letter['senderPlace']:
                action.append(createPlaceName('senderPlace'))
            # add date
            if 'senderDate' in table.fieldnames and letter['senderDate']:
                try:
                    action.append(createDate(letter['senderDate']))
                except TypeError:
                    logging.warning(
                        'Could not parse senderDate in line %s', table.line_num)
        else:
            logging.info('No information on sender in line %s', table.line_num)

        # addressee info block
        if letter['addressee'] or ('addresseePlace' in table.fieldnames and letter['addresseePlace']) or ('addresseeDate' in table.fieldnames and letter['addresseeDate']):
            action = SubElement(entry, 'correspAction')
            action.set('xml:id', createID('addressee'))
            action.set('type', 'received')

            # add persName or orgName
            if letter['addressee']:
                correspondents = createCorrespondent('addressee')
                for addressee in correspondents:
                    action.append(addressee)
            # add placeName
            if ('addresseePlace' in table.fieldnames) and letter['addresseePlace']:
                action.append(createPlaceName('addresseePlace'))
            # add date
            if 'addresseeDate' in table.fieldnames and letter['addresseeDate']:
                try:
                    action.append(createDate(letter['addresseeDate']))
                except TypeError:
                    logging.warning(
                        'Could not parse addresseeDate in line %s', table.line_num)
        else:
            logging.info('No information on addressee in line %s',
                         table.line_num)
        if args.notes:
            if ('note' in table.fieldnames) and letter['note']:
                note = SubElement(entry, 'note')
                note.set('xml:id', createID('note'))
                note.text = str(letter['note'])
        if entry.find('*'):
            profileDesc.append(entry)

# generate empty body
root.append(createTextstructure())

# save cmi to file
tree = ElementTree(root)
tree.write(os.path.splitext(os.path.basename(args.filename))[
           0] + '.xml', encoding="utf-8", xml_declaration=True, method="xml")
