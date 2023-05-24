#! /usr/bin/env python
"""
dict_parser.py
Create an sqlite3 database from a dictionary text file and parse it to an xdxf file.
Supports custom dictionaries from dict.cc with language selection settings.
"""

import sqlite3


LANGUAGES = {'EN': 'English',
             'DE': 'German',
             'BG': 'Bulgarian',
             'RU': 'Russian'}


def create_db(db_file):
    conn = sqlite3.connect(db_file)
    return conn


def parse_txt_to_db(lex_file, conn, encoding='utf-8'):
    """
    Parse the dictionary text file to an sqlite3 database
    :param lex_file: the dictionary text file 
    :param conn: the sqlite3 connection
    :param encoding: str, default 'utf-8'
    """
    cursor = conn.cursor()
    # TODO: add additional columns for other info in database if needed
    cursor.execute(f'CREATE TABLE lex ([id] INTEGER PRIMARY KEY, [source] TEXT NOT NULL, [target] TEXT NOT NULL, [part] TEXT, [ling] TEXT)')
    conn.commit()

    print("...creating database...")
    line_num = 1
    with open(lex_file, 'r', encoding=encoding) as fh:
        for line in fh:
            if not line.startswith(('#', ' ', '\n')):
                print(">> " + line)
                # separate the two languages
                # TODO: make this more efficient and check if more info could exist
                source, target = line.split('\t', 1)
                part, ling = '', ''
                # parse other info if it exists
                if "\t" in target:
                    # separate the part of speech
                    target, part = target.split('\t', 1) 
                    # separate the added linguistics info
                    if "\t" in part:
                        part, ling = part.split('\t', 1)
                
                source = source.strip()
                target = target.strip()
                part = part.strip() if part.strip() else 'NULL'
                ling = ling.strip() if ling.strip() else 'NULL'
                
                if source and target:
                    cursor.execute('INSERT INTO lex VALUES (' + str(line_num) + ', "' + source + '", "' + target + '", "' + part + '", "' + ling +'")')
                    conn.commit()
                    line_num += 1

    cursor.execute('UPDATE lex SET part = NULL WHERE part = "NULL"')
    cursor.execute('UPDATE lex SET ling = NULL WHERE ling = "NULL"')
    cursor.close()
    print("...database created successfully.")


def parse_db_to_xdxf(xdxf_file, conn, lang, encoding='utf-8'):
    """
    Parse the sqlite3 database to an xdxf file
    :param xdxf_file: the xdxf file
    :param conn: the sqlite3 connection
    :param lang: tuple of two strings (source, target), e.g. ('EN', 'DE'); follow abbreviations in LANGUAGES
    :param encoding: str, default 'utf-8'
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lex ORDER BY id ASC')
    
    print("...creating xdxf file...")
    with open(xdxf_file, 'w', encoding=encoding) as df:
        df.write(f'<?xml version="1.0" encoding="{encoding.capitalize()}" ?><!DOCTYPE xdxf SYSTEM \"https://github.com/soshial/xdxf_makedict/tree/master/format_standard\">'
                 + f'\n<xdxf revision=\"34\">\n<meta_info>\n<title>{lang[0]}-{lang[1]} dict</title>\n<full_title>{LANGUAGES[lang[0]]}-{LANGUAGES[lang[1]]} dictionary '
                 + f'based on dict.cc</full_title>\n<languages><from>{lang[0]}</from><to>{lang[1]}</to></languages></meta_info>\n<lexicon>')

        for row in cursor:
            i, source, target, part, ling = row
            part = part if part else ''
            ling = ling if ling else ''
            df.write('<ar><k>' + source + '</k><def><deftext cmt="' + ling + '">' + target + '</deftext><gr>' + part + '</gr></def></ar>\n')
            print('Processed: ' + str(i) + ' entries.')

        cursor.close()
        df.write('</lexicon></xdxf>')

    print("...xdxf file created successfully.")


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Create an sqlite3 database from a dictionary text file and parse it to an xdxf file.')
    parser.add_argument('dir', help='the dir containing the dictionary text file')
    parser.add_argument('-e', '--encoding', default='utf-8', help='the encoding of the files')
    parser.add_argument('-l', '--lang', nargs=2, default=('DE', 'BG'), help='the languages of the dictionary')
    args = parser.parse_args()

    args.txt = args.dir + 'dict.txt'
    args.db = args.dir + 'lex.db'
    args.xdxf = args.dir + 'dict.xdxf'
    connect = create_db(args.db)
    parse_txt_to_db(args.txt, connect, args.encoding)
    parse_db_to_xdxf(args.xdxf, connect, args.lang, args.encoding)

    connect.close()

