
from matai_v2.benchmark import create_comprehensive_test_suite, store_judge_test_to_jsonl


if __name__=='__main__': 
    test_cases = create_comprehensive_test_suite()
    file_path= "./test_cases.jsonl"
    for test in test_cases: 
        store_judge_test_to_jsonl(test, file_path)

