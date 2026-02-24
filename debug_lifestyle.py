
import os
import django
import sys
import json

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finmind_site.settings")
django.setup()

from account.analyzer.LifestyleAnalyzer import LifestyleAnalyzer

try:
    print("Initializing Analyzer...")
    analyzer = LifestyleAnalyzer()
    
    # Test Case 1: Specific User and Months (Long term)
    user_id = "xiaxinyu"
    months_long = 120
    print(f"Running analyze(user_id='{user_id}', months={months_long})...")
    result_long = analyzer.analyze(user_id=user_id, months=months_long)
    print(f"Long term analysis complete. Transactions analyzed: {result_long.get('total_analyzed', 0)}")

    # Test Case 2: Specific User and Months (Short term)
    months_short = 1
    print(f"Running analyze(user_id='{user_id}', months={months_short})...")
    result_short = analyzer.analyze(user_id=user_id, months=months_short)
    print(f"Short term analysis complete. Transactions analyzed: {result_short.get('total_analyzed', 0)}")
    
    # Check for NaN or Infinite values in the result structure recursively
    result = result_long # Check the larger result for NaNs
    def check_nan(obj, path=""):
        if isinstance(obj, float):
            import math
            if math.isnan(obj) or math.isinf(obj):
                print(f"FOUND NAN/INF at {path}: {obj}")
                return True
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if check_nan(v, f"{path}.{k}"):
                    return True
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if check_nan(v, f"{path}[{i}]"):
                    return True
        return False

    if check_nan(result):
        print("Result contains NaN/Inf values!")
    else:
        print("Result is clean (no NaN/Inf).")

    if isinstance(result, dict) and "modes" in result:
        print(f"Modes: {[m['label'] for m in result['modes']]}")
        
    # Check Parent Distribution
    if isinstance(result, dict) and "distribution" in result:
        others = [d for d in result['distribution'] if d['name'] == 'Other']
        if others:
            print(f"WARNING: 'Other' parent count: {others[0]['value']}")
        else:
            print("Distribution check: No 'Other' parent found (Good!)")
        
    # Test 6: All Time (months=0)
    print("\nTest 6: All Time (months=0)")
    analyzer = LifestyleAnalyzer()
    res = analyzer.analyze(user_id='xiaxinyu', months=0)
    check_nan(res, "Test 6")
    if isinstance(res, dict) and "modes" in res:
        print(f"Modes: {[m['label'] for m in res['modes']]}")
    
    # Serialize to JSON to ensure it's valid
    json_str = json.dumps(result)
    print(f"JSON serialization successful. Length: {len(json_str)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
