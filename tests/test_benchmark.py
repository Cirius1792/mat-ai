import pytest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from matai_v2.benchmark import benchmark_model, EvaluationResult, create_comprehensive_test_suite, print_benchmark_results

def test_benchmark_model_with_mocked_score_fnc():
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
    results = benchmark_model(llm_client_mock, judge_models, score_fnc=score_fnc_mock)

    # Assert
    assert len(results) == len(judge_models)
    for model in judge_models:
        assert model in results
        assert len(results[model]) == len(create_comprehensive_test_suite())

    # Verify score_fnc was called for each test case and each model
    assert score_fnc_mock.call_count == len(judge_models) * len(create_comprehensive_test_suite())

    # Check the calculation of the delta
    for model in judge_models:
        for test_case, expected_scores in create_comprehensive_test_suite():
            result_score = results[model][test_case.description]
            expected_delta_overall = expected_scores.overall_score - mock_score.overall_score
            assert result_score.overall_score == pytest.approx(expected_delta_overall)

            for dim, score in expected_scores.dimension_scores.items():
                expected_delta_dim = score - mock_score.dimension_scores[dim]
                assert result_score.dimension_scores[dim] == pytest.approx(expected_delta_dim)

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
    # You can add more specific assertions here, e.g., by inspecting the arguments of the mock
    call_args = printer_mock.call_args[0][0]
    assert len(call_args.rows) == 1
    assert call_args.field_names == ["Model", "Test Description", "Delta Weighted Score", "Delta in completeness", "Delta in accuracy_clarity", "Delta in due_date_precision", "Delta in confidence_calibration"]
