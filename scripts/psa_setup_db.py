#!/usr/bin/env python
# pylint: disable=C0116,W0613

"""
Setup db for a public advisory queue.
"""

import sqlite3
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    if os.path.exists(os.getenv('PUBLIC_ADVISORY_DB_PATH')):
        os.remove(os.getenv('PUBLIC_ADVISORY_DB_PATH'))
    con = sqlite3.connect(os.getenv('PUBLIC_ADVISORY_DB_PATH'))
    cur = con.cursor()
    # create table for storing message
    cur.execute(f"create table {os.getenv('PUBLIC_ADVISORY_TABLE_MESSAGE')} (kampong, agency, message);")
    logger.info(f"Table: {os.getenv('PUBLIC_ADVISORY_TABLE_MESSAGE')} created in DB: {os.getenv('PUBLIC_ADVISORY_DB_PATH')}")

    # create table for name and agency
    cur.execute(f"create table {os.getenv('PUBLIC_ADVISORY_AGENCY')} (telegram_handle, agency, kampong);")
    logger.info(f"Table: {os.getenv('PUBLIC_ADVISORY_AGENCY')} created in DB: {os.getenv('PUBLIC_ADVISORY_DB_PATH')}")

    ## add mock data
    mock_data = [
        ('quanxue', 'GovTech', 'Kolam Ayer'),
        ('quanxue', 'GovTech', 'Jalan Besar'),
        ('xtrntr', 'GovTech', 'Kolam Ayer'),
        ('xtrntr', 'GovTech', 'Jalan Besar'),
        ('kjunwei', 'GovTech', 'Kolam Ayer'),
        ('kjunwei', 'GovTech', 'Jalan Besar'),
        ('mindylim', 'GovTech', 'Kolam Ayer'),
        ('mindylim', 'GovTech', 'Jalan Besar'),
        ('wp', 'GovTech', 'Kolam Ayer'),
        ('wp', 'GovTech', 'Jalan Besar'),
    ]
    cur.executemany(f"INSERT into {os.getenv('PUBLIC_ADVISORY_AGENCY')} (telegram_handle, agency, kampong) values (?, ?, ?);", mock_data)
    logger.info(f'Inserted data')

    con.commit()

    con.close()


if __name__ == '__main__':
    main()
    logger.info(f'DONE')
    con = sqlite3.connect(os.getenv('PUBLIC_ADVISORY_DB_PATH'))
    cur = con.cursor()
    # show mock data
    for r in cur.execute(f"select * from agency;").fetchall():
        logger.info("Rows inserted: %s ", r)
    con.close()
