#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Setup db for a public advisory queue. Replaces db.
"""

import sqlite3
import logging
import os

DB_NAME = 'public_advisory.db'
TABLE_MESSAGE = 'public_advisory'
TABLE_AGENCY = 'agency'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    # create table for storing message
    cur.execute(f"create table {TABLE_MESSAGE} (kampong, agency, message);")
    logger.info(f'Table: {TABLE_MESSAGE} created in DB: {DB_NAME}')

    # create table for name and agency
    cur.execute(f"create table {TABLE_AGENCY} (telegram_handle, agency, kampong);")
    logger.info(f'Table: {TABLE_AGENCY} created in DB: {DB_NAME}')

    ## add mock data
    mock_data = [('quanxue', 'GovTech', 'Kolam Ayer'), ('quanxue', 'GovTech', 'Jalan Besar')]
    cur.executemany(f"INSERT into {TABLE_AGENCY} (telegram_handle, agency, kampong) values (?, ?, ?);", mock_data)
    logger.info(f'Inserted data')

    con.commit()

    con.close()


if __name__ == '__main__':
    main()
    logger.info(f'DONE')
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    # show mock data
    for r in cur.execute(f"select * from agency;").fetchall():
        logger.info(r)
    con.close()
