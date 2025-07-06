from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from typing import List
import json
from datetime import datetime, timedelta
from collections import namedtuple
from openai import OpenAI
from matai_v2.email import EmailAddress, EmailContent
from matai_v2.logging import configure_logging
from matai_v2.processor import ActionItem, ActionType
import logging
from prettytable import PrettyTable
configure_logging()
logger = logging.getLogger(__name__)

EmailTestCase = namedtuple(
    'EmailTestCase', ['email', 'expected', 'actual', 'description'])


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
                  judge_model) -> Optional[EvaluationResult]:
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
            # Fallback: try to extract scores from response text
            if i == max_retries - 1:
                logger.error(
                    f"Failed to parse LLM response after {max_retries} attempts: {e}")
                raise e


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


# Example test case for false positives
def create_false_positive_test_case() -> Tuple[EmailTestCase, EvaluationResult]:
    """Example test case where no action items should be extracted."""

    email = EmailContent(
        message_id="test-false-positive",
        subject="Thank you for the great meeting",
        sender=EmailAddress("John", "john@company.com", "company.com"),
        recipients=[EmailAddress("Sarah", "sarah@company.com", "company.com")],
        thread_id="thread-123",
        timestamp=datetime.now(),
        body="""Hi Sarah,

        Thank you for the excellent presentation yesterday. The client was very impressed
        with our proposal and I believe we're in a strong position for the next phase.

        I'll be out of office next week for vacation, but please feel free to reach out
        if anything urgent comes up.

        Best regards,
        John"""
    )

    # No action items should be extracted from this email
    expected_action_items = []

    # Example of model extracting false positives
    actual_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Prepare for next phase with client",
            due_date=datetime.now() + timedelta(days=7),
            message_id="test-false-positive",
            confidence_score=0.8,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Handle urgent matters while John is on vacation",
            due_date=datetime.now() + timedelta(days=3),
            message_id="test-false-positive",
            confidence_score=0.6,
            id=2
        )
    ]

    return (
        EmailTestCase(email=email,
                      expected=expected_action_items,
                      actual=actual_action_items,
                      description="Test case for false positive detection - no action items should be extracted"
                      ),
        EvaluationResult(overall_score=1.5, dimension_scores={
            # Major penalty for 2 false positives (expected 0)
            "completeness": 0.0,
            "accuracy_clarity": 2.0,     # Descriptions are somewhat related but not actual tasks
            "due_date_precision": 2.0,   # Dates assigned without basis
            "confidence_calibration": 0.0  # High confidence on completely wrong items
        })
    )


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


# Example test case for near-perfect score (minor variations)
def create_near_perfect_test_case() -> Tuple[EmailTestCase, EvaluationResult]:
    """Example test case that should return a near-perfect score (4.0-4.5)."""

    email = EmailContent(
        message_id="test-near-perfect",
        subject="Weekly Team Sync - Action Items",
        sender=EmailAddress("Manager", "manager@company.com", "company.com"),
        recipients=[EmailAddress("Team", "team@company.com", "company.com")],
        thread_id="thread-789",
        timestamp=datetime.now(),
        body="""Team,

        Thanks for the great discussion in today's sync. Here's what we agreed on:

        - Please review the user feedback document and provide your thoughts by end of week
        - We need to update the project timeline based on the new requirements
        - Don't forget to submit your timesheets by Monday as usual

        Let's keep the momentum going!

        Best,
        Manager"""
    )

    # Expected action items
    expected_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Review user feedback document and provide thoughts",
            due_date=datetime.now() + timedelta(days=3),  # End of week
            message_id="test-near-perfect",
            confidence_score=0.85,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Update project timeline based on new requirements",
            due_date=None,  # No specific due date mentioned
            message_id="test-near-perfect",
            confidence_score=0.80,
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Submit timesheets",
            due_date=datetime.now() + timedelta(days=5),  # Monday
            message_id="test-near-perfect",
            confidence_score=0.90,
            id=3
        )
    ]

    # Near-perfect model extraction - slight variations in wording and dates
    actual_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            # Slightly different wording
            description="Review the user feedback document and share thoughts",
            due_date=datetime.now() + timedelta(days=2),  # One day off from "end of week"
            message_id="test-near-perfect",
            confidence_score=0.88,  # Slightly different confidence
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Update project timeline with new requirements",  # Minor wording change
            due_date=None,  # Correctly identified no due date
            message_id="test-near-perfect",
            confidence_score=0.82,  # Close confidence
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Submit timesheets by Monday",  # More specific description
            due_date=datetime.now() + timedelta(days=5),  # Correct due date
            message_id="test-near-perfect",
            confidence_score=0.90,  # Perfect confidence
            id=3
        )
    ]

    return (
        EmailTestCase(email=email,
                      expected=expected_action_items,
                      actual=actual_action_items,
                      description="Test case for near-perfect score - minor variations in wording and dates"
                      ),
        EvaluationResult(overall_score=4.5, dimension_scores={
            "completeness": 5.0,        # All expected items extracted, no false positives
            # Minor wording differences ("share thoughts" vs "provide thoughts")
            "accuracy_clarity": 4.0,
            # One date is 1 day off ("end of week" interpretation)
            "due_date_precision": 4.0,
            # Close but not perfect confidence scores (±0.03-0.05)
            "confidence_calibration": 4.0
        }))


# Comprehensive test suite
def create_comprehensive_test_suite():
    """Create a comprehensive test suite covering various scenarios."""

    return [
        create_perfect_score_test_case(),
        create_near_perfect_test_case(),
        create_false_positive_test_case(),
        create_missing_action_items_test_case(),
        create_wrong_due_dates_test_case()
    ]


def create_missing_action_items_test_case() -> Tuple[EmailTestCase, EvaluationResult]:
    """Test case where model misses some action items."""

    email = EmailContent(
        message_id="test-missing-items",
        subject="Urgent: Client Issues Need Resolution",
        sender=EmailAddress("Support", "support@company.com", "company.com"),
        recipients=[EmailAddress(
            "Dev Team", "dev@company.com", "company.com")],
        thread_id="thread-urgent",
        timestamp=datetime.now(),
        body="""Dev Team,

        We have three critical issues that need immediate attention:

        1. The payment gateway is down - needs to be fixed by 5 PM today
        2. Users are reporting login issues - investigate and resolve ASAP
        3. The mobile app is crashing on iOS devices - patch needed by tomorrow

        Please prioritize these issues and keep me updated on progress.

        Thanks,
        Support Team"""
    )

    expected_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Fix payment gateway issue",
            due_date=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
            message_id="test-missing-items",
            confidence_score=0.95,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Investigate and resolve login issues",
            due_date=datetime.now(),  # ASAP
            message_id="test-missing-items",
            confidence_score=0.90,
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Create patch for iOS app crashes",
            due_date=datetime.now() + timedelta(days=1),
            message_id="test-missing-items",
            confidence_score=0.88,
            id=3
        )
    ]

    # Model only catches 2 out of 3 action items
    actual_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Fix payment gateway issue",
            due_date=datetime.now().replace(hour=17, minute=0, second=0, microsecond=0),
            message_id="test-missing-items",
            confidence_score=0.95,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Investigate login issues",
            due_date=datetime.now(),
            message_id="test-missing-items",
            confidence_score=0.85,
            id=2
        )
        # Missing the iOS crash issue
    ]

    return (
        EmailTestCase(email=email,
                      expected=expected_action_items,
                      actual=actual_action_items,
                      description="Test case for missing action items - model should catch incompleteness"
                      ),
        EvaluationResult(overall_score=2.8, dimension_scores={
            # Missed 1 out of 3 action items (66% recall)
            "completeness": 2.0,
            "accuracy_clarity": 4.0,     # The extracted items are accurate
            "due_date_precision": 4.0,   # Dates correct for extracted items
            "confidence_calibration": 3.0  # Confidence slightly off on one item
        })
    )


def create_wrong_due_dates_test_case() -> Tuple[EmailTestCase, EvaluationResult]:
    """Test case where model gets due dates wrong."""

    email = EmailContent(
        message_id="test-wrong-dates",
        subject="Conference Preparation Timeline",
        sender=EmailAddress("Event Coordinator",
                            "events@company.com", "company.com"),
        recipients=[EmailAddress(
            "Marketing", "marketing@company.com", "company.com")],
        thread_id="thread-conf",
        timestamp=datetime.now(),
        body="""Marketing Team,

        The annual conference is in 3 weeks. Here's what we need to prepare:

        - Marketing materials need to be ready 1 week before the conference
        - Social media campaign should start 2 weeks before
        - Press release must be sent out 5 days before the event

        Please let me know if you need any additional resources.

        Best,
        Event Coordinator"""
    )

    expected_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Prepare marketing materials",
            # 1 week before conference (3 weeks - 1 week)
            due_date=datetime.now() + timedelta(weeks=2),
            message_id="test-wrong-dates",
            confidence_score=0.90,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Start social media campaign",
            due_date=datetime.now() + timedelta(weeks=1),  # 2 weeks before conference
            message_id="test-wrong-dates",
            confidence_score=0.85,
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Send press release",
            due_date=datetime.now() + timedelta(days=16),  # 5 days before conference
            message_id="test-wrong-dates",
            confidence_score=0.88,
            id=3
        )
    ]

    # Model gets the tasks right but dates wrong
    actual_action_items = [
        ActionItem(
            action_type=ActionType.TASK,
            description="Prepare marketing materials",
            due_date=datetime.now() + timedelta(weeks=3),  # Wrong: should be 2 weeks
            message_id="test-wrong-dates",
            confidence_score=0.90,
            id=1
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Start social media campaign",
            due_date=datetime.now() + timedelta(days=5),  # Wrong: should be 1 week
            message_id="test-wrong-dates",
            confidence_score=0.85,
            id=2
        ),
        ActionItem(
            action_type=ActionType.TASK,
            description="Send press release",
            due_date=datetime.now() + timedelta(days=10),  # Wrong: should be 16 days
            message_id="test-wrong-dates",
            confidence_score=0.88,
            id=3
        )
    ]

    return (EmailTestCase(email=email,
                          expected=expected_action_items,
                          actual=actual_action_items,
                          description="Test case for wrong due dates - model should catch date calculation errors"
                          ),

            EvaluationResult(overall_score=3.0, dimension_scores={
                "completeness": 5.0,        # All items were extracted
                "accuracy_clarity": 4.0,     # Descriptions are correct
                "due_date_precision": 1.0,   # All dates are significantly wrong
                "confidence_calibration": 3.0  # Confidence scores are close
            })
            )


def benchmark_model(llm_client: OpenAI, judge_models: List[str]):
    """Run a benchmark against the given judge model. The goal is to evaluate the effectiveness of a model to act a judge for the application. 
    The score returned by the model is compared against a baseline score expected for each test case and the difference between the score in every category is computed. """

    for judge_model in judge_models:
        result_table = PrettyTable([
            "Description",
            "Delta Weighted Score",
            f"Delta in {EvaluationResult.COMPLETENESS}",
            f"Delta in {EvaluationResult.ACCURACY_CLARITY}",
            f"Delta in {EvaluationResult.DUE_DATE_PRECISION}",
            f"Delta in {EvaluationResult.CONFIDENCE_CALIBRATION}"
        ])
        for test_case, expected_scores in create_comprehensive_test_suite():
            actual_score = compute_score(
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
            result_table.add_row([
                test_case.description,
                expected_scores.get_weighted_score() - actual_score.get_weighted_score(),
                expected_scores.completeness - actual_score.completeness,
                expected_scores.accuracy_clarity - actual_score.accuracy_clarity,
                expected_scores.due_date_precision - actual_score.due_date_precision,
                expected_scores.confidence_calibration - actual_score.confidence_calibration,
            ])
        logger.info(f"Benchmark results for model {judge_model}:")
        logger.info(result_table)
