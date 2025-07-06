import pytest
from unittest.mock import MagicMock, patch, call
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from matai_v2.benchmark import (
    EvaluationResult,
    benchmark_model_from_dataset, 
    print_benchmark_results, 
    store_judge_test_to_jsonl, 
    load_judge_test_from_jsonl, 
    create_perfect_score_test_case,
    compute_score,
)
from matai_v2.email import EmailContent, EmailAddress
from matai_v2.processor import ActionItem, ActionType

def test_compute_score_retry_on_key_error():
    # Arrange
    llm_client_mock = MagicMock()
    mock_response_invalid = MagicMock()
    mock_response_invalid.choices[0].message.content = '{"invalid_key": "some_value"}'
    
    mock_response_valid = MagicMock()
    valid_content = {
        "overall_score": 4.0,
        "dimension_scores": {
            "completeness": 4.0,
            "accuracy_clarity": 4.0,
            "due_date_precision": 4.0,
            "confidence_calibration": 4.0,
        }
    }
    mock_response_valid.choices[0].message.content = json.dumps(valid_content)

    llm_client_mock.chat.completions.create.side_effect = [
        mock_response_invalid,
        mock_response_valid
    ]

    email = EmailContent("id", "subject", EmailAddress("test", "test@test.com", "test.com"), [], "thread_id", datetime(2025, 1, 1), "body")
    
    # Act
    result = compute_score(email, [], [], llm_client_mock, "test_model")

    # Assert
    assert llm_client_mock.chat.completions.create.call_count == 2
    assert result.overall_score == 4.0

def test_compute_score_returns_zero_on_persistent_bad_json():
    # Arrange
    llm_client_mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"bad_json": "missing_fields"}'
    llm_client_mock.chat.completions.create.return_value = mock_response

    email = EmailContent("id", "subject", EmailAddress("test", "test@test.com", "test.com"), [], "thread_id", datetime(2025, 1, 1), "body")

    # Act
    result = compute_score(email, [], [], llm_client_mock, "test_model")

    # Assert
    assert llm_client_mock.chat.completions.create.call_count == 3  # Max retries
    assert result.overall_score == 0.0
    assert result.completeness == 0.0
    assert result.accuracy_clarity == 0.0
    assert result.due_date_precision == 0.0
    assert result.confidence_calibration == 0.0

def test_benchmark_model_with_mocked_score_fnc():
    def create_test_data():
        return [create_perfect_score_test_case()]
    # Arrange
    llm_client_mock = MagicMock()
    judge_models = ["test_model_1", "test_model_2"]

    # Create a mock score_fnc that returns a predictable EvaluationResult
    mock_score = EvaluationResult(
        overall_score=4.0,
        dimension_scores={
            "completeness": 4.0,
            "accuracy_clarity": 4.0,
            "due_date_precision": 4.0,
            "confidence_calibration": 4.0,
        }
    )
    score_fnc_mock = MagicMock(return_value=mock_score)

    # Act
    results = benchmark_model_from_dataset(llm_client_mock, judge_models, 
                                           create_test_data(),
                                           score_fnc=score_fnc_mock)

    # Assert
    assert len(results) == len(judge_models)
    for model in judge_models:
        assert model in results
        assert len(results[model]) == 1

    # Verify score_fnc was called for each test case and each model
    assert score_fnc_mock.call_count == len(judge_models) * len(list(create_test_data()))

    # Check the calculation of the delta
    for model in judge_models:
        for test_case, expected_scores in list(create_test_data()):
            result_score = results[model][test_case.description]
            expected_delta_overall = expected_scores.overall_score - mock_score.overall_score
            assert result_score.overall_score == pytest.approx(expected_delta_overall)

            for dim, score in expected_scores.dimension_scores.items():
                expected_delta_dim = score - mock_score.dimension_scores[dim]
                assert result_score.dimension_scores[dim] == pytest.approx(expected_delta_dim)


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
