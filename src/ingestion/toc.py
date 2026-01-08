import math
import logging
import pandas as pd
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_table_of_contents(chunk_obj: Any, match_pct: float = 0.3) -> pd.DataFrame:
    """
    Identify a table-of-contents table in a chunked document by sampling
    the top portion of items and looking for them inside tables.
    Returns an empty DataFrame if no TOC table is found.
    """
    def is_table(table, all_items):
        q_items = all_items[: math.ceil(len(all_items) * match_pct)]
        table_text = table.get_text().lower()
        for item in q_items:
            if item.lower() not in table_text:
                return False
        return True

    all_items = chunk_obj.list_items()
    table_of_contents = pd.DataFrame()
    MAX_ITEMS = -1
    ITEM_COLUMN_INDEX = -1

    for table in chunk_obj.tables():
        try:
            if is_table(table, all_items):
                table_of_contents = table.to_dataframe()
                # choose column that contains most 'item' occurrences
                for i in range(table_of_contents.shape[1]):
                    NUM_ITEMS = sum("item" in str(x).lower() for x in table_of_contents.iloc[:, i])
                    if NUM_ITEMS > MAX_ITEMS:
                        ITEM_COLUMN_INDEX = i
                        MAX_ITEMS = NUM_ITEMS

                columns = [""] * table_of_contents.shape[1]
                # guard if table is malformed
                if ITEM_COLUMN_INDEX + 1 < len(columns):
                    columns[ITEM_COLUMN_INDEX] = "Index"
                    columns[ITEM_COLUMN_INDEX + 1] = "Headings"
                table_of_contents.columns = columns
                if "Index" in table_of_contents.columns:
                    table_of_contents = table_of_contents.set_index("Index")
                return table_of_contents
        except Exception:
            logger.exception("Error processing a table when searching for TOC; skipping table.")
    # return empty df if not found
    return pd.DataFrame()