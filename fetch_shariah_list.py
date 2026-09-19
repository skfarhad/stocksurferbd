#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Download the Shariah-compliant company list and its latest revision.

CSE (CSI index) is the only source that publishes its constituents free; DSE
sells the DSES list. Run ``ShariahData.list_sources()`` to see every registered
source and whether it is available.
"""

from stocksurferbd_pkg import ShariahData


LIST_FILE_NAME = 'cse_shariah_list.xlsx'
REVISION_FILE_NAME = 'cse_shariah_revision.xlsx'
SOURCE = 'CSE'


loader = ShariahData()


def fetch_shariah_data():
    print(loader.list_sources()[['SOURCE', 'INDEX', 'AVAILABLE', 'ACCESS']])
    info = loader.get_shariah_list_info(source=SOURCE)
    print(
        f"{info['index']} constituents: {info['constituent_count']} "
        f"(table as of {info['as_of_date']}; list revised "
        f"{info['list_revised_date']}, effective {info['list_effective_date']})"
    )
    print(f"Added: {info['added']}")
    print(f"Excluded: {info['excluded']}")
    loader.save_shariah_list(file_name=LIST_FILE_NAME, source=SOURCE)
    loader.save_shariah_revision(file_name=REVISION_FILE_NAME, source=SOURCE)


if __name__ == "__main__":
    fetch_shariah_data()
