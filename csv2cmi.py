# -*- coding: utf-8 -*-

# csv2cmi
# version 0.9
# Copyright (c) 2015 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

# needs Python3
import datetime
import csv
import os
import random
import string
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, ElementTree
from xml.dom import minidom

# enter here your name and the title of your edition
fileName = 'LetterTable.csv'
projectName = 'Letters project'
editorName = 'Klaus Rettinghaus'
edition = ''
editionType = 'print'  # 'hybrid' or 'online' if appropriate


class bcolors:
    # blender colors
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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
        persName = SubElement(action, 'persName')
        if letter[namestring].startswith('[') and letter[namestring].endswith(']'):
            persName.set('evidence', 'conjecture')
            letter[namestring] = letter[namestring][1:-1]
            print ("Info: Added @evidence for <persName> in line",
                   table.line_num)
        persName.text = str(letter[namestring])
        if (namestring + 'ID' in table.fieldnames) and (letter[namestring + 'ID']):
            persName.set('ref', 'http://d-nb.info/gnd/' +
                         str(letter['senderID']))


def createPlace(placestring):
    # function for putting the place in <correspAction>
    if letter[placestring]:
        placeName = SubElement(action, 'placeName')
        if letter[placestring].startswith('[') and letter[placestring].endswith(']'):
            placeName.set('evidence', 'conjecture')
            letter[placestring] = letter[placestring][1:-1]
            print ("Info: Added @evidence for <placeName> in line",
                   table.line_num)
        placeName.text = str(letter[placestring])
        if (placestring + 'ID' in table.fieldnames) and (letter[placestring + 'ID']):
            if 'http://www.geonames.org/' in letter[placestring + 'ID']:
                placeName.set('ref', str(letter[placestring + 'ID']))
            else:
                print (bcolors.WARNING + "Warning: No standardized ID in line",
                       table.line_num, bcolors.ENDC)
        else:
            print (bcolors.WARNING + "Warning: Missing ID for", letter[
                   placestring], "in line", table.line_num, bcolors.ENDC)


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
        editionID = 'edition_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(
            8)) + '_' + ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        createEdition(editionTitle, editionID)
    return editionID

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
    print('Recognized columns:', table.fieldnames)
    if not('edition' in table.fieldnames) or (edition == ''):
        print (bcolors.WARNING +
               "Warning: No edition stated. Please set manually." + bcolors.ENDC)
    for letter in table:
        entry = SubElement(profileDesc, 'correspDesc')
        if ('edition' in table.fieldnames) and (str(letter['edition']) != ''):
            entry.set('source', '#' + getEditonID(letter['edition']))
            if 'key' in table.fieldnames:
                try:
                    letterNumber = int(letter['key'])
                    entry.set('key', str(letterNumber))
                except:
                    if 'html://' in str(letter['key']):
                        entry.set('ref', str(letter['key']))
        elif ('key' in table.fieldnames) and (letter['key']):
            print (bcolors.FAIL + "Error: Key without edition in line",
                   table.line_num, bcolors.ENDC)

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
                print ("Info: Added @cert for <date> in line", table.line_num)
            senderDate.set('when', str(letter['senderDate']))
        else:
            print (bcolors.WARNING + "Warning: Couldn't set <date> for <correspAction> in line",
                   table.line_num, "(no ISO format)", bcolors.ENDC)

        # addressee info block
        if (letter['addressee']) or (('addresseePlace' in table.fieldnames) and (letter['addresseePlace'])) or (('addresseeDate') in table.fieldnames and (letter['addresseeDate'])):
            action = SubElement(entry, 'correspAction')
            action.set('type', 'received')

            createPerson('addressee')
            if 'addresseePlace' in table.fieldnames:
                createPlace('addresseePlace')

# generate empty body
text = SubElement(root, 'text')
body = SubElement(text, 'body')
p = SubElement(body, 'p')

# save cmi to file
tree = ElementTree(root)
tree.write(os.path.splitext(os.path.basename(fileName))[
           0] + '.xml', encoding="utf-8", xml_declaration=True, method="xml")
