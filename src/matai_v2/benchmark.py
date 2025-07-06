from typing import Dict, Iterator, List, Optional, Tuple
from dataclasses import dataclass
from typing import List
import json
from datetime import datetime, timedelta
from openai import OpenAI
from matai_v2.email import EmailAddress, EmailContent
from matai_v2.logging import configure_logging
from matai_v2.processor import ActionItem, ActionType, load_action_item_from_json
import logging
from prettytable import PrettyTable, TableStyle
configure_logging()
logger = logging.getLogger(__name__)


@dataclass
class EmailTestCase:
    email: EmailContent
    expected: List[ActionItem]
    actual: List[ActionItem]
    description: str


def create_judge_prompt(email: EmailContent, expected_action_items: List[ActionItem], actual_action_items: List[ActionItem]) -> str:
    """
    Creates a comprehensive prompt for LLM judge to evaluate action item extraction quality.

    Args:
        email: The original email content
        expected_action_items: Ground truth action items
        actual_action_items: Action items extracted by the system

    Returns:
        str: Formatted prompt for the LLM judge
    """

    prompt = f"""You are an expert evaluator tasked with scoring the quality of action item extraction from emails. Your role is to assess how well a system extracted action items compared to the expected ground truth.

## EVALUATION CRITERIA

Score from 0-5 based on these four dimensions:

### 1. COMPLETENESS & PRECISION (30% weight)
- **5**: All expected action items extracted with no missing items AND no false positives
- **4**: All/most expected items extracted with minimal false positives (1 reasonable extra item)
- **3**: Majority of expected items extracted with some false positives (2-3 extra items)
- **2**: Some expected items extracted but with significant false positives or gaps
- **1**: Few expected items extracted and/or many false positives
- **0**: No relevant action items extracted OR mostly false positives

### 2. ACCURACY & CLARITY (30% weight)
- **5**: Action items are precise, clear, and perfectly match the email context
- **4**: Action items are mostly accurate with minor wording differences
- **3**: Action items capture the essence but lack some precision
- **2**: Action items are somewhat unclear or miss important details
- **1**: Action items are vague or contain inaccuracies
- **0**: Action items are completely inaccurate or unintelligible

### 3. DUE DATE PRECISION (25% weight)
- **5**: Due dates are exactly correct based on email context
- **4**: Due dates are very close (within 1 day) to expected
- **3**: Due dates are reasonably close (within 2-3 days) to expected
- **2**: Due dates are somewhat off (within a week) but logical
- **1**: Due dates are significantly off but still reasonable
- **0**: Due dates are completely wrong or missing when required

### 4. CONFIDENCE CALIBRATION (15% weight)
- **5**: Confidence scores perfectly match expected levels
- **4**: Confidence scores are very close to expected (±0.1)
- **3**: Confidence scores are reasonably close to expected (±0.2)
- **2**: Confidence scores are somewhat off (±0.3)
- **1**: Confidence scores are significantly off (±0.4-0.5)
- **0**: Confidence scores are completely miscalibrated (>±0.5)

## INPUT DATA

### ORIGINAL EMAIL:
**Subject:** {email.subject}
**From:** {email.sender.name} <{email.sender.email}>
**To:** {', '.join([f"{r.name} <{r.email}>" for r in email.recipients])}
**Date:** {email.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Body:**
{email.body}

### EXPECTED ACTION ITEMS (Ground Truth):
{_format_action_items(expected_action_items)}

### ACTUAL EXTRACTED ACTION ITEMS:
{_format_action_items(actual_action_items)}

## SPECIAL CASES TO EVALUATE CAREFULLY

### False Positives (Hallucinated Action Items):
When the model extracts action items that don't exist in the email:
- **Severe penalty**: Reduce completeness score significantly (at least -2 points)
- **Confidence misalignment**: If hallucinated items have high confidence, penalize confidence calibration
- **Context relevance**: Some "extra" items might be reasonable inferences - judge based on email context

### Zero Expected Action Items:
When no action items should be extracted from the email:
- **Perfect score (5)**: No action items extracted
- **Good score (4)**: Only reasonable/borderline interpretations extracted
- **Poor score (0-2)**: Multiple clear hallucinations extracted

### Confidence Score Evaluation:
- **High confidence + Wrong extraction**: Major penalty
- **Low confidence + Wrong extraction**: Minor penalty
- **High confidence + Correct extraction**: Reward
- **Low confidence + Correct extraction**: Slight penalty

## EVALUATION INSTRUCTIONS
1. **Compare systematically**: Match each expected action item with extracted ones
2. **Identify false positives**: Flag any extracted items that don't correspond to expected ones
3. **Evaluate false positive severity**:
   - **Reasonable inference**: Minor penalty (e.g., "follow up after meeting" when meeting is mentioned)
   - **Weak inference**: Moderate penalty (e.g., "prepare agenda" when only "meeting" is mentioned)
   - **Clear hallucination**: Major penalty (e.g., "send invoice" when email is about vacation plans)
4. **Consider context**: Evaluate based on the original email content and implicit requirements
5. **Be objective**: Focus on measurable differences rather than stylistic preferences
6. **Account for reasonable variations**: Similar descriptions should score well if meaning is preserved
7. **Penalize unreliable behavior**: Heavily penalize clear hallucinations that would confuse users

## SCORING EXAMPLES

**Perfect Match (Score: 5)**
- Expected: "Prepare presentation slides for client meeting"
- Actual: "Prepare presentation slides for client meeting"
- Due dates match exactly, confidence scores align

**Good Match (Score: 4)**
- Expected: "Prepare presentation slides for client meeting"
- Actual: "Create presentation materials for upcoming client meeting"
- Minor wording differences but same intent, dates close

**Acceptable Match (Score: 3)**
- Expected: "Prepare presentation slides for client meeting"
- Actual: "Get ready for client meeting"
- Less specific but captures core requirement

**Zero Expected Items (Score: 5)**
- Expected: No action items
- Actual: No action items extracted
- Perfect reliability

**Reasonable Extra Item (Score: 4)**
- Expected: "Prepare presentation slides for client meeting"
- Actual: "Prepare presentation slides for client meeting" + "Send meeting agenda to participants"
- Extra item is reasonable given email context

**Hallucination (Score: 1-2)**
- Expected: "Prepare presentation slides for client meeting"
- Actual: "Prepare presentation slides for client meeting" + "Process quarterly invoices"
- Extra item has no basis in email content

## OUTPUT FORMAT

Provide your evaluation in this exact JSON format:

```json
{{
    "overall_score": <0-5>,
    "dimension_scores": {{
        "completeness": <0-5>,
        "accuracy_clarity": <0-5>,
        "due_date_precision": <0-5>,
        "confidence_calibration": <0-5>
    }}
}}
```

## IMPORTANT NOTES

- Be consistent in your scoring across similar cases
- Consider the business context and urgency implied in the email
- **Prioritize reliability**: False positives can be more harmful than false negatives in production
- **Zero tolerance for clear hallucinations**: Items with no basis in the email should be severely penalized
- **Reasonable inferences are acceptable**: But should be clearly justified by email content
- When evaluating emails with no expected action items, perfect score requires no extraction
- When in doubt about whether an item is a reasonable inference, err on the side of caution

Now, please evaluate the action item extraction and provide your detailed scoring."""

    return prompt


def _format_action_items(action_items: List[ActionItem]) -> str:
    """Helper function to format action items for the prompt."""
    if not action_items:
        return "None"

    formatted_items = []
    for i, item in enumerate(action_items, 1):
        due_date_str = item.due_date.strftime(
            '%Y-%m-%d') if item.due_date else "No due date"
        formatted_items.append(
            f"{i}. **Description:** {item.description}\n"
            f"   **Type:** {item.action_type.value}\n"
            f"   **Due Date:** {due_date_str}\n"
            f"   **Confidence:** {item.confidence_score:.2f}"
        )

    return "\n\n".join(formatted_items)


# Data class for evaluation results


@dataclass
class EvaluationResult:
    """Comprehensive evaluation result with detailed scoring breakdown."""
    COMPLETENESS = "completeness"
    ACCURACY_CLARITY = "accuracy_clarity"
    DUE_DATE_PRECISION = "due_date_precision"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    overall_score: float
    dimension_scores: Dict[str, float]

    def get_weighted_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted score with custom weights."""
        if weights is None:
            weights = {
                self.COMPLETENESS: 0.25,
                self.ACCURACY_CLARITY: 0.35,
                self.DUE_DATE_PRECISION: 0.25,
                self.CONFIDENCE_CALIBRATION: 0.15,
            }

        return sum(self.dimension_scores[dim] * weight
                   for dim, weight in weights.items())

    def get_performance_summary(self) -> Dict[str, str]:
        """Get qualitative performance summary for each dimension."""
        def score_to_label(score: float) -> str:
            if score >= 4.5:
                return "Excellent"
            elif score >= 3.5:
                return "Good"
            elif score >= 2.5:
                return "Fair"
            elif score >= 1.5:
                return "Poor"
            else:
                return "Very Poor"

        return {dim: score_to_label(score)
                for dim, score in self.dimension_scores.items()}

    def to_json(self):
        return {
            "overall_score": self.overall_score,
            "dimension_scores": self.dimension_scores
        }

    @property
    def completeness(self) -> float:
        """Get completeness score."""
        return self.dimension_scores.get(self.COMPLETENESS, 0.0)

    @property
    def accuracy_clarity(self) -> float:
        """Get accuracy clarity score."""
        return self.dimension_scores.get(self.ACCURACY_CLARITY, 0.0)

    @property
    def due_date_precision(self) -> float:
        """Get due date precision score."""
        return self.dimension_scores.get(self.DUE_DATE_PRECISION, 0.0)

    @property
    def confidence_calibration(self) -> float:
        """Get confidence calibration score."""
        return self.dimension_scores.get(self.CONFIDENCE_CALIBRATION, 0.0)
# Example usage function


def compute_score(email: EmailContent,
                  expected_action_items: List[ActionItem],
                  actual_action_items: List[ActionItem],
                  llm_client,
                  judge_model) -> EvaluationResult:
    """
    Compute comprehensive evaluation for extracted action items using LLM judge.

    Args:
        email: Original email content
        expected_action_items: Ground truth action items
        actual_action_items: Extracted action items
        llm_client: LLM client for making API calls
        judge_model: Model identifier for the judge

    Returns:
        EvaluationResult: Comprehensive evaluation with detailed scoring
    """
    prompt = create_judge_prompt(
        email, expected_action_items, actual_action_items)

    # pprint("/n")
    # print(prompt)
    # pprint("/n")
    # return

    # Call your LLM client here
    max_retries = 3

    for i in range(max_retries):
        try:
            # Retry logic for robustness
            if i > 0:
                logger.info(
                    f"Retrying LLM evaluation (attempt {i+1}) for email: {email.subject}")
            response = llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=judge_model,
                temperature=0.1,  # Low temperature for consistent scoring
                response_format={"type": "json_object"},
                timeout=120,  # seconds
                max_tokens=2000,
            )
            result = json.loads(response.choices[0].message.content)

            return EvaluationResult(
                overall_score=result["overall_score"],
                dimension_scores=result["dimension_scores"],
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"LLM response parsing failed on attempt {i + 1}/{max_retries}. Error: {e}")
            if i == max_retries - 1:
                logger.error(
                    f"Failed to parse LLM response after {max_retries} attempts. Returning zero score.")
                return EvaluationResult(
                    overall_score=0.0,
                    dimension_scores={
                        EvaluationResult.COMPLETENESS: 0.0,
                        EvaluationResult.ACCURACY_CLARITY: 0.0,
                        EvaluationResult.DUE_DATE_PRECISION: 0.0,
                        EvaluationResult.CONFIDENCE_CALIBRATION: 0.0,
                    }
                )
    # This path should not be hit if max_retries > 0
    return EvaluationResult(
        overall_score=0.0,
        dimension_scores={
            EvaluationResult.COMPLETENESS: 0.0,
            EvaluationResult.ACCURACY_CLARITY: 0.0,
            EvaluationResult.DUE_DATE_PRECISION: 0.0,
            EvaluationResult.CONFIDENCE_CALIBRATION: 0.0,
        }
    )


def analyze_model_performance(test_cases: List[Dict], client: OpenAI, model: str) -> Dict[str, float]:
    """
    Analyze model performance across multiple test cases.

    Args:
        test_cases: List of test cases with email, expected, and actual action items

    Returns:
        Dict with aggregated performance metrics
    """
    results = []

    for case in test_cases:
        result = compute_score(
            case["email"],
            case["expected"],
            case["actual"],
            client,
            model,
        )
        results.append(result)

    # Aggregate results
    aggregated = {
        "overall_mean": sum(r.overall_score for r in results) / len(results),
        "completeness_precision_mean": sum(r.dimension_scores.get(EvaluationResult.COMPLETENESS, 0) for r in results) / len(results),
        "accuracy_mean": sum(r.dimension_scores.get(EvaluationResult.ACCURACY_CLARITY, 0) for r in results) / len(results),
        "due_date_mean": sum(r.dimension_scores.get(EvaluationResult.DUE_DATE_PRECISION, 0) for r in results) / len(results),
        "confidence_mean": sum(r.dimension_scores.get(EvaluationResult.CONFIDENCE_CALIBRATION, 0) for r in results) / len(results),
    }

    return aggregated


# This function could be useful in the feature to create new test cases, so I will keep it
def create_perfect_score_test_case() -> Tuple[EmailTestCase, EvaluationResult]:
    """Example test case that should return a perfect score (5.0)."""

    email = EmailContent(
        message_id="test-perfect-score",
        subject="Project Alpha - Next Steps and Deadlines",
        sender=EmailAddress("Alice", "alice@company.com", "company.com"),
        recipients=[EmailAddress("Bob", "bob@company.com", "company.com"),
                    EmailAddress("Carol", "carol@company.com", "company.com")],
        thread_id="thread-456",
        timestamp=datetime.now(),
        body="""Hi Bob and Carol,

        Following our productive meeting this morning, here are the key action items we discussed:

        1. Bob, please finalize the technical specifications document by Friday, March 15th.
           This is critical for the client presentation next week.

        2. Carol, we need you to coordinate with the design team and schedule a review session
           for next Tuesday, March 12th at 2 PM.

        3. Both of you should prepare your quarterly budget reports and submit them to me
           by Thursday, March 14th, so we can review them before the board meeting.

        Please confirm receipt of these tasks and let me know if you have any questions
        or need additional resources.

        Best regards,
        Alice"""
    )

    # Ground truth action items - what should be extracted
    expected_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Finalize the technical specifications document",
            due_date=datetime(2024, 3, 15),  # Friday, March 15th
            message_id="test-perfect-score",
            confidence_score=0.95,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Coordinate with design team and schedule review session",
            # Tuesday, March 12th at 2 PM
            due_date=datetime(2024, 3, 12, 14, 0),
            message_id="test-perfect-score",
            confidence_score=0.90,
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Prepare quarterly budget reports and submit",
            due_date=datetime(2024, 3, 14),  # Thursday, March 14th
            message_id="test-perfect-score",
            confidence_score=0.92,
            id=3
        )
    ]

    # Perfect model extraction - matches expected exactly
    actual_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Finalize the technical specifications document",
            due_date=datetime(2024, 3, 15),
            message_id="test-perfect-score",
            confidence_score=0.95,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Coordinate with design team and schedule review session",
            due_date=datetime(2024, 3, 12, 14, 0),
            message_id="test-perfect-score",
            confidence_score=0.90,
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Prepare quarterly budget reports and submit",
            due_date=datetime(2024, 3, 14),
            message_id="test-perfect-score",
            confidence_score=0.92,
            id=3
        )
    ]

    return (
        EmailTestCase(email=email,
                      expected=expected_action_items,
                      actual=actual_action_items,
                      description="Test case for perfect score - all action items extracted correctly with precise dates and confidence"
                      ),
        EvaluationResult(overall_score=5.0, dimension_scores={
            "completeness": 5.0,        # All expected items extracted, no false positives
            "accuracy_clarity": 5.0,     # Perfect match in descriptions
            "due_date_precision": 5.0,   # Exact due dates
            "confidence_calibration": 5.0  # Confidence scores match exactly
        }))


def benchmark_model_from_dataset(llm_client: OpenAI, judge_models: List[str],
                    test_data: List[Tuple[EmailTestCase, EvaluationResult]],
                    score_fnc=compute_score
                    ) -> Dict[str, Dict[str, EvaluationResult]]:
    """Run a benchmark against the given judge model. The goal is to evaluate the effectiveness of a model to act a judge for the application.
    The score returned by the model is compared against a baseline score expected for each test case and the difference between the score in every category is computed. """

    results: Dict[str, Dict[str, EvaluationResult]] = {}
    for judge_model in judge_models:
        results[judge_model] = {}
        for test_case, expected_scores in test_data:
            actual_score = score_fnc(
                test_case.email,
                test_case.expected,
                test_case.actual,
                llm_client,
                judge_model,
            )
            if actual_score is None:
                logger.error(
                    f"Error evaluating test case: {test_case.description}")
                continue
            logger.info(
                f"{test_case.description}: \t {actual_score.get_weighted_score()}")
            results[judge_model][test_case.description] = EvaluationResult(
                expected_scores.overall_score - actual_score.overall_score,
                {
                    EvaluationResult.COMPLETENESS: expected_scores.completeness - actual_score.completeness,
                    EvaluationResult.ACCURACY_CLARITY: expected_scores.accuracy_clarity - actual_score.accuracy_clarity,
                    EvaluationResult.DUE_DATE_PRECISION: expected_scores.due_date_precision - actual_score.due_date_precision,
                    EvaluationResult.CONFIDENCE_CALIBRATION: expected_scores.confidence_calibration - actual_score.confidence_calibration,
                })
        logger.info(f"Benchmark results for model {judge_model}:")
    return results


def _build_table(test_outcomes: Dict[str, Dict[str, EvaluationResult]],) -> PrettyTable:
    result_table = PrettyTable([
        "Model",
        "Test Description",
        "Delta Weighted Score",
        f"Delta in {EvaluationResult.COMPLETENESS}",
        f"Delta in {EvaluationResult.ACCURACY_CLARITY}",
        f"Delta in {EvaluationResult.DUE_DATE_PRECISION}",
        f"Delta in {EvaluationResult.CONFIDENCE_CALIBRATION}"
    ])
    for model, results in test_outcomes.items():
        for test, scores in results.items():
            result_table.add_row([
                model,
                test,
                scores.get_weighted_score(),
                scores.completeness,
                scores.accuracy_clarity,
                scores.due_date_precision,
                scores.confidence_calibration,
            ])
        result_table.add_divider()
    return result_table


def print_benchmark_results(test_outcomes: Dict[str, Dict[str, EvaluationResult]],  printer):
    result_table = _build_table(test_outcomes)
    printer(result_table)


def store_benchmark_results_to_markdown_file(test_outcomes: Dict[str, Dict[str, EvaluationResult]], file_path: str):
    """Store benchmark results to a markdown file."""
    result_table = _build_table(test_outcomes)
    result_table.set_style(TableStyle.MARKDOWN)
    with open(file_path, 'w') as f:
        f.write(result_table.get_string())


def store_judge_test_to_jsonl(test_case: Tuple[EmailTestCase, EvaluationResult], json_file_path: str):
    data = {
        "test_data": {
            "description": test_case[0].description,
            "email": test_case[0].email.to_json(),
            "expected": [item.to_json() for item in test_case[0].expected],
            "actual": [item.to_json() for item in test_case[0].actual],
        },
        "expected_scores": test_case[1].to_json()
    }
    with open(json_file_path, 'a') as f:
        f.write(json.dumps(data) + '\n')


def load_judge_test_from_jsonl(json_file_path: str) -> List[Tuple[EmailTestCase, EvaluationResult]]:
    """Load judge test cases from a JSONL file."""
    tests = []
    with open(json_file_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            email_data = data["test_data"]["email"]
            email = EmailContent.from_json(email_data)
            expected_items = [load_action_item_from_json(
                item) for item in data["test_data"]["expected"]]
            actual_items = [load_action_item_from_json(
                item) for item in data["test_data"]["actual"]]
            test_case = EmailTestCase(
                email=email,
                expected=expected_items,
                actual=actual_items,
                description=data["test_data"]["description"]
            )
            expected_scores = EvaluationResult(
                **data["expected_scores"])
            tests.append ((test_case, expected_scores))
    return tests


