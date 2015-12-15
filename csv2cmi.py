# -*- coding: utf-8 -*-

# csv2cmi
# version 0.9.11.1
# Copyright (c) 2015 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

# needs Python3
import datetime
import csv
import logging
import os
import random
import string
import sys
import urllib.request
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, ElementTree
from xml.dom import minidom

# enter here your name and the title of your edition
fileName = 'LetterTable.csv'
projectName = 'Letters project'
editorName = 'Klaus Rettinghaus'
edition = ''
editionType = 'print'  # 'hybrid' or 'online' if appropriate

# define log output
logging.basicConfig(format='%(levelname)s: %(message)s')

# define RDF types


# simple test for file
if sys.argv[-1] != sys.argv[0]:
    fileName = sys.argv[-1]
try:
    open(fileName, 'rt')
except:
    logging.error('File not found')
    exit()

# check internet connection via DNB
try:
    urllib.request.urlopen('http://193.175.100.220', timeout=1)
    connection = True
except:
    logging.error('No internet connection')
    connection = False


def isodate(datestring):
    try:
        datetime.datetime.strptime(datestring, '%Y-%m-%d')
    except:
        try:
            datetime.datetime.strptime(datestring, '%Y-%m')
        except:
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


def createPerson(namestring):
    if letter[namestring]:
        rdf = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
        if (namestring + 'ID' in table.fieldnames) and (letter[namestring + 'ID']):
            if 'http://' not in str(letter[namestring + 'ID'].strip()):
                authID = 'http://d-nb.info/gnd/' + \
                    str(letter[namestring + 'ID'].strip())
            else:
                authID = str(letter[namestring + 'ID'].strip())
            if connection and (profileDesc.find('correspDesc/correspAction/persName[@ref="' + authID + '"]') == None):
                if 'viaf' in authID:
                    try:
                        gndrdf = ElementTree(
                            file=urllib.request.urlopen(authID + '/rdf.xml'))
                    except urllib.error.HTTPError:
                        logging.error(
                            'Authority file not found for %sID in line %s', namestring, table.line_num)
                        persName = SubElement(action, 'persName')
                        authID = ''
                    except urllib.error.URLError as argh:
                        logging.error('Failed to reach VIAF')
                        persName = SubElement(action, 'persName')
                    else:
                        gndrdf_root = gndrdf.getroot()
                        rdftype = gndrdf_root.find(
                            './rdf:Description[2]/rdf:type', rdf).get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                        if 'Organization' in rdftype:
                            persName = SubElement(action, 'orgName')
                        elif 'Person' in rdftype:
                            persName = SubElement(action, 'persName')
                        else:
                            logging.warning(
                                '%sID in line %s links to unprocessable authority file', namestring, table.line_num)
                            persName = SubElement(action, 'persName')
                            authID = ''
                elif 'gnd' in authID:
                    try:
                        gndrdf = ElementTree(
                            file=urllib.request.urlopen(authID + '/about/rdf'))
                    except urllib.error.HTTPError:
                        logging.error(
                            'Authority file not found for %sID in line %s', namestring, table.line_num)
                        persName = SubElement(action, 'persName')
                        authID = ''
                    except urllib.error.URLError as argh:
                        logging.error('Failed to reach GND')
                        persName = SubElement(action, 'persName')
                    else:
                        gndrdf_root = gndrdf.getroot()
                        rdftype = gndrdf_root.find(
                            './/rdf:type', rdf).get('rdf:resource',rdf)
                        if 'Corporate' in rdftype:
                            persName = SubElement(action, 'orgName')
                        else:
                            persName = SubElement(action, 'persName')
                        if 'UndifferentiatedPerson' in rdftype:
                            logging.warning(
                                '%sID in line %s links to undifferentiated Person', namestring, table.line_num)
                            authID = ''
                else:
                    logging.error('No proper autority record in line %s', table.line_num)
                    persName = SubElement(action, 'persName')
                    authID = ''
            else:
                persName = SubElement(action, 'persName')
            if authID:
                persName.set('ref', authID)
        else:
            persName = SubElement(action, 'persName')
        if letter[namestring].startswith('[') and letter[namestring].endswith(']'):
            persName.set('evidence', 'conjecture')
            letter[namestring] = letter[namestring][1:-1]
            logging.info('Added @evidence for <persName> in line %s',
                         table.line_num)
        persName.text = str(letter[namestring])


def createPlace(placestring):
    # function for putting the place in <correspAction>
    if letter[placestring]:
        placeName = SubElement(action, 'placeName')
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


def createEdition(biblText, biblID):
    # creates a new entry within <sourceDesc>
    bibl = SubElement(sourceDesc, 'bibl')
    bibl.text = biblText
    bibl.set('type', editionType)
    bibl.set('xml:id', biblID)


def getEditonID(editionTitle):
    editionID = ''
    for bibl in sourceDesc.findall('bibl'):
        if editionTitle == bibl.text:
            editionID = bibl.get('xml:id')
    if not editionID:
        editionID = createID('edition')
        createEdition(editionTitle, editionID)
    return editionID


def createID(id_prefix):
    fullID = id_prefix + '_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(
        8)) + '_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return fullID

# building cmi
# generating root element
root = Element('TEI')
root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
root.append(Comment('Generated from table of letters with csv2cmi'))

# teiHeader
teiHeader = SubElement(root, 'teiHeader')
# file description
fileDesc = SubElement(teiHeader, 'fileDesc')
titleStmt = SubElement(fileDesc, 'titleStmt')
title = SubElement(titleStmt, 'title')
title.text = projectName
editor = SubElement(titleStmt, 'editor')
editor.text = editorName
publicationStmt = SubElement(fileDesc, 'publicationStmt')
publisher = SubElement(publicationStmt, 'publisher')
publisher.text = editorName
idno = SubElement(publicationStmt, 'idno')
idno.set('type', 'url')
idno.text = os.path.splitext(os.path.basename(fileName))[0] + '.xml'
date = SubElement(publicationStmt, 'date')
date.set('when', str(datetime.datetime.now().isoformat()))
availability = SubElement(publicationStmt, 'availability')
licence = SubElement(availability, 'licence')
licence.set('target', 'https://creativecommons.org/licenses/by/4.0/')
licence.text = 'This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0'
sourceDesc = SubElement(fileDesc, 'sourceDesc')

# filling in correspondance meta-data
profileDesc = SubElement(teiHeader, 'profileDesc')

with open(fileName, 'rt') as letterTable:
    table = csv.DictReader(letterTable)
    logging.info('Recognized columns: %s', table.fieldnames)
    if not('edition' in table.fieldnames):
        if edition:
            createEdition(edition, createID('edition'))
        else:
            logging.warning('No edition stated. Please set manually.')
            bibl = SubElement(sourceDesc, 'bibl')
    for letter in table:
        entry = SubElement(profileDesc, 'correspDesc')
        entry.set('xml:id', createID('letter'))
        if 'edition' in table.fieldnames:
            edition = letter['edition'].strip()
        if edition:
            entry.set('source', '#' + getEditonID(edition))
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
            action.set('type', 'sent')

            createPerson('sender')
            if 'senderPlace' in table.fieldnames:
                createPlace('senderPlace')

        if isodate(letter['senderDate']) or isodate(letter['senderDate'][1:-1]):
            senderDate = SubElement(action, 'date')
            if ('[' in str(letter['senderDate'])) and (']' in str(letter['senderDate'])):
                letter['senderDate'] = letter['senderDate'][1:-1]
                senderDate.set('cert', 'medium')
                logging.info('Added @cert for <date> in line %s',
                             table.line_num)
            senderDate.set('when', str(letter['senderDate']))
        else:
            logging.warning('senderDate in line %s not set (no ISO)',
                            table.line_num)

        # addressee info block
        if letter['addressee'] or 'addresseePlace' in table.fieldnames or (('addresseeDate') in table.fieldnames and (letter['addresseeDate'])):
            action = SubElement(entry, 'correspAction')
            action.set('type', 'received')

            createPerson('addressee')
            if 'addresseePlace' in table.fieldnames:
                createPlace('addresseePlace')

letterTable.close()

# generate empty body
text = SubElement(root, 'text')
body = SubElement(text, 'body')
p = SubElement(body, 'p')

# save cmi to file
tree = ElementTree(root)
tree.write(os.path.splitext(os.path.basename(fileName))[
           0] + '.xml', encoding="utf-8", xml_declaration=True, method="xml")
