#!/usr/bin/env python
# coding=utf-8

import os, itertools, logging
import sqlite3 as sqlite

import xlrd


logging.basicConfig() ## NO debug, no info. But logs warnings
log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)
#log.setLevel(logging.DEBUG)


def xls2db(infile, outfile=None, column_name_start_row=0, data_start_row=1):
    """
    Convert an xls file into an sqlite db!
    """
    #Now you can pass in a workbook!
    if isinstance(infile, basestring):
        wb = xlrd.open_workbook(infile)
    elif isinstance(infile, xlrd.Book):
        wb = infile
        infile = "default"
    else:
        raise TypeError("infile must be a string or xlrd.Book")

    #Now you can pass in a sqlite connection!
    if outfile is None:
        outfile = os.path.splitext(infile)[0] + '.sqlite'

    if isinstance(outfile, basestring):
        db_conn = sqlite.connect(outfile)
        db_cursor = db_conn.cursor()
    elif isinstance(outfile, sqlite.Connection):
        db_conn = outfile
        db_cursor = db_conn.cursor()
    else:
        raise TypeError("outfile must be a string or sqlite.Connection")

    # hack, avoid plac's annotations....
    column_name_start_row = int(column_name_start_row)
    data_start_row = int(data_start_row)
    for s in wb.sheets():

        # Create the table.
        # Vulnerable to sql injection because ? is only able to handle inserts
        # I'm not sure what to do about that!
        if s.nrows > column_name_start_row:
            column_names = []
            for j in xrange(s.ncols):
                # FIXME TODO deal with embedded double quotes
                colname = s.cell(column_name_start_row, j).value
                if not colname:
                    colname = 'col%d' % (j + 1,)
                # FIXME TODO deal with embedded spaces in names
                # (requires delimited identifiers) and missing column types
                column_names.append(colname)
            
            tmp_sql = 'create table "' + s.name + '" ('+ ','.join(column_names) +");"
            log.debug('DDL %r', tmp_sql)
            db_cursor.execute(tmp_sql)
        
        if s.nrows > data_start_row:
            tmp_sql = 'insert into "' + s.name + '" values (' +','.join(itertools.repeat('?', s.ncols)) +");"
            for rownum in xrange(data_start_row, s.nrows):
                bind_params = s.row_values(rownum)
                log.debug('DML %r, %r', tmp_sql, bind_params)
                db_cursor.execute(tmp_sql, bind_params)

    db_conn.commit()
    #Only do this if we're not working on an externally-opened db
    if isinstance(outfile, basestring):
        db_cursor.close()
        db_conn.close()


def db2xls(infile, outfile):
    """
    Convert an sqlite db into an xls file. Not implemented!
    Some issues: one needs to be able to figure out what the table names are!
    """
    raise NotImplementedError


if __name__ == "__main__":
    #Apparently this thing's pretty magical.
    import plac
    plac.call(xls2db)
