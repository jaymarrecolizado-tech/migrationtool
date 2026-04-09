"""Test the upload endpoint with NaN/emoji handling."""
import urllib.request
import urllib.parse
import json
import os
import math

SERVER = "http://localhost:5000"

def test_status():
    """Test the status endpoint."""
    print("\n=== Testing /api/status ===")
    req = urllib.request.urlopen(f"{SERVER}/api/status")
    data = json.loads(req.read())
    print(f"Status: {data['status']}")
    print(f"Features: {len(data['features'])}")
    assert data['status'] == 'ok'
    print("✅ Status OK")
    return True

def test_upload(filepath):
    """Test file upload and check for NaN in response."""
    print(f"\n=== Testing /api/upload with {os.path.basename(filepath)} ===")
    
    # Multipart form data
    import http.client
    import mimetypes
    
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(filepath)}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode('utf-8') + file_data + b'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
    
    req = urllib.request.Request(
        f"{SERVER}/api/upload",
        data=body,
        headers={'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'}
    )
    
    try:
        resp = urllib.request.urlopen(req)
        raw = resp.read()
        
        # Try to parse as JSON
        try:
            data = json.loads(raw)
            print(f"✅ Valid JSON response (size: {len(raw)} bytes)")
            print(f"Success: {data.get('success')}")
            
            # Check for NaN
            json_str = json.dumps(data)
            if 'NaN' in json_str or 'Infinity' in json_str:
                print("❌ Found NaN/Infinity in response!")
                # Find where
                idx = json_str.find('NaN')
                if idx == -1:
                    idx = json_str.find('Infinity')
                print(f"  Context: ...{json_str[max(0,idx-50):idx+50]}...")
                return False
            else:
                print("✅ No NaN/Infinity found")
            
            # Print summary
            if 'summary' in data:
                summary = data['summary']
                print(f"Sheets: {len(summary.get('sheets_processed', []))}")
                print(f"Errors: {summary.get('total_errors', 0)}")
                print(f"Warnings: {summary.get('total_warnings', 0)}")
            
            if 'statistics' in data:
                stats = data['statistics']
                print(f"Statistics: {len(json.dumps(stats))} chars")
                # Check each sheet's statistics for NaN
                for sheet_name, sheet_stats in stats.items():
                    issues = check_nan_in_value(sheet_stats, sheet_name)
                    if issues:
                        print(f"  ❌ {sheet_name}: {issues}")
                    else:
                        print(f"  ✅ {sheet_name}: No NaN in stats")
            
            if 'quality_scores' in data:
                print(f"Quality scores: {len(data['quality_scores'])} sheets")
                for sheet_name, score in data['quality_scores'].items():
                    issues = check_nan_in_value(score, sheet_name)
                    if issues:
                        print(f"  ❌ {sheet_name}: {issues}")
                    else:
                        print(f"  ✅ {sheet_name}: Score={score.get('quality_score', 'N/A')}")
            
            # Check cross_row_issues
            if 'cross_row_issues' in data:
                print(f"Cross-row issues: {len(data['cross_row_issues'])}")
            
            # Check duplicates
            if 'duplicates' in data:
                dups = data['duplicates']
                total = 0
                for v in dups.values():
                    if isinstance(v, list):
                        total += len(v)
                    elif isinstance(v, int):
                        total += v
                print(f"Duplicate entries: {total}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            print(f"Raw (first 500): {raw[:500]}")
            return False
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code}")
        print(f"Response: {e.read()[:500]}")
        return False

def check_nan_in_value(obj, path=""):
    """Recursively check for NaN/Infinity values."""
    issues = []
    if isinstance(obj, float):
        if math.isnan(obj):
            issues.append(f"{path}: NaN")
        elif math.isinf(obj):
            issues.append(f"{path}: Infinity")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            issues.extend(check_nan_in_value(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            issues.extend(check_nan_in_value(item, f"{path}[{i}]"))
    return issues

if __name__ == "__main__":
    print("🧪 BPLS CSV Generator - Upload Endpoint Test")
    print("=" * 50)
    
    try:
        # Test 1: Status
        test_status()
        
        # Test 2: Upload foolproof test data
        template_path = "foolproof_test_data.xlsx"
        if os.path.exists(template_path):
            test_upload(template_path)
        else:
            print(f"\n⚠️  Template not found: {template_path}")
            print("Generating one first...")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
