from typing import List
from dataclasses import dataclass

from matai.email_processing.model import ActionItem, EmailContent

# This script implements the basic funcitonalities to manage the dataset used to evaluate the application and to run the banchmark using this dataset.
# The dataset is stored in jsonl format, each line contains a json object describing:
#     1. The email being analysed
#     2. The expected action item extracted from those email.
# When running the benchmark the score is evaluated using an AI Judge that will compare the extracted action item with the expected one.
# A score between 1 and 5 will be assigned by the judge depending on the correctness of the extracted informations.

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
        import json, os
        from matai.email_processing.model import EmailContent, ActionItem, ActionType, EmailAddress
        dataset_file = "dataset.jsonl"
        lines = []
        if not os.path.exists(dataset_file):
            return []
        with open(dataset_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                email_data = data.get("email", {})
                action_data = data.get("expected_action_item", {})
                email = EmailContent.from_json(email_data)
                action_item = ActionItem.from_json(action_data)
                from matai.benchmark.dataset import DatasetLine
                lines.append(DatasetLine(email=email, expected_action_item=action_item))
        return lines

    def append(self, line: DatasetLine):
        """Append a new line to the dataset.
        The dataset is stored to file before returning.
    
        Args:
            line (DatasetLine): The line to append.
        """
        import json
        from dataclasses import asdict
        from matai.email_processing.model import ActionType
        dataset_file = "dataset.jsonl"

        def serialize(obj):
            from datetime import datetime
            if isinstance(obj, ActionType):
                return obj.name
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(dataset_file, "a", encoding="utf-8") as f:
            json_line = json.dumps(asdict(line), default=serialize)
            f.write(json_line + "\n")
