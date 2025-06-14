from typing import List
from dataclasses import dataclass

import json
import os
from dataclasses import asdict
from matai.email_processing.model import EmailContent, ActionItem, ActionType
import logging

logger = logging.getLogger(__name__)

# This script implements the basic funcitonalities to manage the dataset used to evaluate the application and to run the banchmark using this dataset.
# The dataset is stored in jsonl format, each line contains a json object describing:
#     1. The email being analysed
#     2. The expected action item extracted from those email.
# When running the benchmark the score is evaluated using an AI Judge that will compare the extracted action item with the expected one.
# A score between 1 and 5 will be assigned by the judge depending on the correctness of the extracted informations.


@dataclass
class DatasetLine:
    email: EmailContent
    expected_action_items: List[ActionItem]

    def to_json(self) -> dict:
        """Convert the DatasetLine to a JSON serializable dictionary."""
        return {
            "email": self.email.to_json(),
            "expected_action_items": [ai.to_json() for ai in self.expected_action_items]
        }


class Dataset:
    def __init__(self, file_path: str = "dataset.jsonl"):
        """Initialize the Dataset with a file path.
        Args:
            file_path (str): The path to the dataset file.
        """
        self.dataset_file = file_path

    def load(self) -> List[DatasetLine]:
        """Load the dataset from a jsonl file.

        Returns:
            List[DatasetLine]: A list of DatasetLine objects containing email content and expected action items.
        """
        lines = []
        if not os.path.exists(self.dataset_file):
            return []
        with open(self.dataset_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                try:
                    data = json.loads(line)
                    email_data = data.get("email", {})
                    email = EmailContent.from_json(email_data)
                    action_data_list = data.get("expected_action_items", [])
                    action_items = [ActionItem.from_json(ai) for ai in action_data_list]
                    lines.append(DatasetLine(
                        email=email, expected_action_items=action_items))
                except Exception as e:
                    logger.error(f"Error decoding JSON on line {i + 1}: {e}")
                    raise ValueError(f"Invalid dataset format at line {i+1}. Please check the dataset file.") from e

        return lines

    def append(self, line: DatasetLine):
        """Append a new line to the dataset.
        The dataset is stored to file before returning.

        Args:
            line (DatasetLine): The line to append.
        """
        dataset_file = self.dataset_file


        with open(dataset_file, "a", encoding="utf-8") as f:
            json_line = json.dumps(line.to_json())
            f.write(json_line + "\n")

    def save(self, lines: List[DatasetLine]) -> None:
        """Save the given dataset lines, overwriting the dataset file."""
        with open(self.dataset_file, "w", encoding="utf-8") as f:
            for line in lines:
                json_line = json.dumps(line.to_json())
                f.write(json_line + "\n")
