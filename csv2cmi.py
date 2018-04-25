#!/usr/bin/env python3
# csv2cmi
#
# Copyright (c) 2015-2018 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

# needs Python3
import argparse
import configparser
import csv
import datetime
import logging
import os
import random
import string
import urllib.request
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree

__license__ = "MIT"
__version__ = '1.5.0'

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
parser.add_argument('--line-numbers',
                    help='add line numbers', action='store_true')
parser.add_argument('-v', '--verbose',
                    help='increase output verbosity', action='store_true')
parser.add_argument('--version', action='version',
                    version='%(prog)s ' + __version__)
args = parser.parse_args()

# set verbosity
if args.verbose:
    logs.setLevel('INFO')


def isodate(datestring):
    try:
        datetime.datetime.strptime(datestring, '%Y-%m-%d')
    except ValueError:
        try:
            datetime.datetime.strptime(datestring, '%Y-%m')
        except ValueError:
            try:
                datetime.datetime.strptime(datestring, '%Y')
            except ValueError:
                return False
            else:
                return True
        else:
            return True
    else:
        return True


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
    date.set('when', str(datetime.datetime.now().isoformat()))
    availability = SubElement(publicationStmt, 'availability')
    licence = SubElement(availability, 'licence')
    licence.set('target', 'https://creativecommons.org/licenses/by/4.0/')
    licence.text = 'This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0'
    return fileDesc


def createCorrespondent(namestring):
    # creates an element for a correspondent
    if letter[namestring]:
        if (namestring + 'ID' in table.fieldnames) and (letter[namestring + 'ID']):
            if 'http://' not in str(letter[namestring + 'ID'].strip()):
                logging.debug('Assigning ID %s to GND', str(
                    letter[namestring + 'ID'].strip()))
                authID = 'http://d-nb.info/gnd/' + \
                    str(letter[namestring + 'ID'].strip())
            else:
                authID = str(letter[namestring + 'ID'].strip())
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
                    else:
                        gndrdf_root = gndrdf.getroot()
                        rdftype = gndrdf_root.find(
                            './/rdf:type', rdf).get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                        if 'Corporate' in rdftype:
                            correspondent = Element('orgName')
                        else:
                            correspondent = Element('persName')
                        if 'UndifferentiatedPerson' in rdftype:
                            logging.warning(
                                '%sID in line %s links to undifferentiated Person', namestring, table.line_num)
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
            correspondent = Element('persName')
        if letter[namestring].startswith('[') and letter[namestring].endswith(']'):
            correspondent.set('evidence', 'conjecture')
            letter[namestring] = letter[namestring][1:-1]
            logging.info('Added @evidence for <persName> in line %s',
                         table.line_num)
        correspondent.text = str(letter[namestring])
        return correspondent


def createPlaceName(placestring):
    # creates a placeName element
    placeName = Element('placeName')
    letter[placestring] = letter[placestring].strip()
    if letter[placestring].startswith('[') and letter[placestring].endswith(']'):
        placeName.set('evidence', 'conjecture')
        letter[placestring] = letter[placestring][1:-1]
        logging.info('Added @evidence for <placeName> in line %s',
                     table.line_num)
    placeName.text = str(letter[placestring])
    if (placestring + 'ID' in table.fieldnames) and (letter[placestring + 'ID']):
        letter[placestring + 'ID'] = letter[placestring + 'ID'].strip()
        if 'http://www.geonames.org/' in letter[placestring + 'ID']:
            placeName.set('ref', str(letter[placestring + 'ID']))
        else:
            logging.warning("no standardized %sID in line %s",
                            placestring, table.line_num)
    else:
        logging.warning('ID for %s missing in line %s', letter[
            placestring], table.line_num)
    return placeName


def createEdition(editionTitle, biblID):
    # creates a new bibliographic entry
    editionType = 'print'
    if ('Edition' in config) and ('type' in config['Edition']):
        if config.get('Edition', 'type') in ['print', 'hybrid', 'online']:
            editionType = config.get('Edition', 'type')
    bibl = Element('bibl')
    bibl.text = editionTitle
    bibl.set('type', editionType)
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
config['Project'] = {'editor': '', 'publisher': '', 'fileURL': os.path.splitext(
    os.path.basename(args.filename))[0] + '.xml'}
try:
    config.read_file(open('csv2cmi.ini'))
except IOError:
    logging.error('No configuration file found')


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
global table

with open(args.filename, 'rt') as letterTable:
    table = csv.DictReader(letterTable)
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
        sourceDesc.append(createEdition(edition, createID('edition')))
    for letter in table:
        if ('edition' in table.fieldnames):
            edition = letter['edition'].strip()
            editionID = getEditonID(edition)
            if not(edition or args.all):
                continue
            if edition and not editionID:
                editionID = createID('edition')
                sourceDesc.append(createEdition(edition, editionID))
        entry = SubElement(profileDesc, 'correspDesc')
        if (args.line_numbers):
            entry.set('n', str(table.line_num))
        entry.set('xml:id', createID('letter'))
        if edition:
            entry.set('source', '#' + editionID)
        if 'key' in table.fieldnames and letter['key']:
            if not(edition):
                logging.error("Key without edition in line %s", table.line_num)
            else:
                if 'http://' in str(letter['key']):
                    entry.set('ref', str(letter['key']).strip())
                else:
                    entry.set('key', str(letter['key']).strip())

        # sender info block
        if (letter['sender']) or (('senderPlace' in table.fieldnames) and (letter['senderPlace'])) or (letter['senderDate']):
            action = SubElement(entry, 'correspAction')
            action.set('xml:id', createID('sender'))
            action.set('type', 'sent')

            # add persName or orgName
            if letter['sender']:
                action.append(createCorrespondent('sender'))
            # add placeName
            if ('senderPlace' in table.fieldnames) and letter['senderPlace']:
                action.append(createPlaceName('senderPlace'))
            # add date
            if 'senderDate' in table.fieldnames:
                if isodate(letter['senderDate']) or isodate(letter['senderDate'][1:-1]):
                    senderDate = SubElement(action, 'date')
                    if letter['senderDate'].startswith('[') and letter['senderDate'].endswith(']'):
                        senderDate.set('cert', 'medium')
                        letter['senderDate'] = letter['senderDate'][1:-1]
                        logging.info(
                            'Added @cert for <date> in line %s', table.line_num)
                    senderDate.set('when', str(letter['senderDate']))
                else:
                    logging.warning(
                        'senderDate in line %s not set (no ISO)', table.line_num)

        # addressee info block
        if letter['addressee'] or 'addresseePlace' in table.fieldnames or (('addresseeDate') in table.fieldnames and (letter['addresseeDate'])):
            action = SubElement(entry, 'correspAction')
            action.set('xml:id', createID('addressee'))
            action.set('type', 'received')

            # add persName or orgName
            if letter['addressee']:
                action.append(createCorrespondent('addressee'))
            # add placeName
            if ('addresseePlace' in table.fieldnames) and letter['addresseePlace']:
                action.append(createPlaceName('addresseePlace'))
            # add date
            if 'addresseeDate' in table.fieldnames:
                if isodate(letter['addresseeDate']) or isodate(letter['addresseeDate'][1:-1]):
                    addresseeDate = SubElement(action, 'date')
                    if letter['addresseeDate'].startswith('[') and letter['addresseeDate'].endswith(']'):
                        senderDate.set('cert', 'medium')
                        letter['addresseeDate'] = letter['addresseeDate'][1:-1]
                        logging.info(
                            'Added @cert for <date> in line %s', table.line_num)
                    senderDate.set('when', str(letter['addresseeDate']))
                else:
                    logging.warning(
                        'addresseeDate in line %s not set (no ISO)', table.line_num)

# generate empty body
root.append(createTextstructure())

# save cmi to file
tree = ElementTree(root)
tree.write(os.path.splitext(os.path.basename(args.filename))[
           0] + '.xml', encoding="utf-8", xml_declaration=True, method="xml")
