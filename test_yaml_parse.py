import sys
sys.path.insert(0, ".")

from analyzer.config_parser import parse_yaml, parse_config_file

path = "microservices-demo/release/kubernetes-manifests.yaml"

print("=" * 60)
print(f"Testing parse_yaml({path})")
print("=" * 60)

result = parse_yaml(path)
print(f"Number of keys extracted: {len(result)}")
print()
print("First 15 keys:")
for key in list(result.keys())[:15]:
    print(f"  {key}")
print()

print("=" * 60)
print(f"Testing parse_config_file({path})")
print("=" * 60)

result2 = parse_config_file(path)
print(f"Number of keys extracted: {len(result2)}")