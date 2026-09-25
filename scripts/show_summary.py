import json

with open('analyzer_result.json', 'r') as f:
    result = json.load(f)

print('=' * 60)
print('ANALYSIS SUMMARY')
print('=' * 60)
print(f"Has affected tests : {result.get('has_affected_tests', False)}")
print(f"Test count         : {result.get('test_count', 0)}")
print()
print('Affected tests:')
for test in result.get('affected_tests', []):
    print(f'  - {test}')
print('=' * 60)