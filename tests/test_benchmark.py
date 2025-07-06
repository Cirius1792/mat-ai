from unittest.mock import MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from matai_v2.benchmark import (
    EvaluationResult,
    print_benchmark_results, 
    store_judge_test_to_jsonl, 
    load_judge_test_from_jsonl, 
    create_perfect_score_test_case,
)



def test_store_and_load_judge_test_to_jsonl():
    # Arrange
    test_case = create_perfect_score_test_case()
    file_path = "test_judge_cases.jsonl"

    # Act
    store_judge_test_to_jsonl(test_case, file_path)
    loaded_test_cases = list(load_judge_test_from_jsonl(file_path))

    # Assert
    assert len(loaded_test_cases) == 1
    loaded_test_case, loaded_expected_scores = loaded_test_cases[0]
    
    original_test_case, original_expected_scores = test_case

    # Compare EmailTestCase
    assert loaded_test_case.description == original_test_case.description
    assert loaded_test_case.email.subject == original_test_case.email.subject
    assert loaded_test_case.email.body == original_test_case.email.body
    
    # Compare EvaluationResult
    assert loaded_expected_scores.overall_score == original_expected_scores.overall_score
    assert loaded_expected_scores.dimension_scores == original_expected_scores.dimension_scores

    # Clean up the created file
    os.remove(file_path)

def test_print_benchmark_results():
    # Arrange
    printer_mock = MagicMock()
    test_outcomes = {
        "test_model": {
            "test_case_1": EvaluationResult(
                overall_score=0.5,
                dimension_scores={
                    "completeness": 1.0,
                    "accuracy_clarity": 0.0,
                    "due_date_precision": 1.0,
                    "confidence_calibration": 0.0,
                }
            )
        }
    }

    # Act
    print_benchmark_results(test_outcomes, printer=printer_mock)

    # Assert
    printer_mock.assert_called_once()
    call_args = printer_mock.call_args[0][0]
    assert len(call_args.rows) == 1
    assert call_args.field_names == ["Model", "Test Description", "Delta Weighted Score", "Delta in completeness", "Delta in accuracy_clarity", "Delta in due_date_precision", "Delta in confidence_calibration"]
