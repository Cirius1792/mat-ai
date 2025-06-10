# This script implements the basic funcitonalities to manage the dataset used to evaluate the application and to run the banchmark using this dataset.
# The dataset is stored in jsonl format, each line contains a json object describing:
#     1. The email being analysed
#     2. The expected action item extracted from those email.
# When running the benchmark the score is evaluated using an AI Judge that will compare the extracted action item with the expected one.
# A score between 1 and 5 will be assigned by the judge depending on the correctness of the extracted informations.
from typing import List
from dataclasses import dataclass

from matai.email_processing.model import ActionItem, EmailContent


@dataclass
class DatasetLine:
    email: EmailContent
    expected_action_item: ActionItem


class Dataset:

    def load(self) -> List[DatasetLine]:
        """Load the dataset from a jsonl file.

        Returns:
            List[DatasetLine]: A list of DatasetLine objects containing email content and expected action items.
        """
        pass

    def append(self, line: DatasetLine):
        """Append a new line to the dataset.
        The dataset is stored to file before returning.

        Args:
            line (DatasetLine): The line to append.
        """
        pass
