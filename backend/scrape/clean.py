"""
"""

# Standard library imports
import re
import string
from typing import Any, List


def parse_stock_manager_field(manager_field: str) -> List[Any]:
    """"""
    # Return empty list if field is null or has decimal point,
    # which indicates that a share value was entered instead
    if not manager_field or "." in manager_field:
        return []

    # Otherwise, initialize final result set
    cleaned_managers = []

    # Determine characters to split field on
    is_word = any(letter in manager_field for letter in string.ascii_letters)
    split_chars = "," if is_word else ",|\s"

    # Split field and process each entry
    for entry in re.split(split_chars, manager_field):

        # Remove extraneous special characters
        for char in "`_-*":
            entry = entry.replace(char, "")

        # Strip whitespace
        entry = entry.strip()

        # Omit entry if empty, refers to missing value, contains
        # a decimal, or corresponds to a Form 13F filer number
        if (
            not entry
            or entry.upper()
            in ("NO", "NONE", "NON", "NA", "N/A", "OTHER", "SOLE")
            or re.match(r"028[0-9]{5}", entry)
        ):
            continue

        # Cast entry to integer if applicable; otherwise, standardize case
        if not is_word:
            entry = int(entry)
        else:
            entry = entry.upper()

        # Append cleaned entry to list
        cleaned_managers.append(entry)

    return cleaned_managers
