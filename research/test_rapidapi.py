#!/usr/bin/env python3
"""
Test script for evaluating RapidAPI UFO sighting APIs.
Run this once you have a free RapidAPI key to analyze data structure and quality.
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional

# RapidAPI Configuration
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY_HERE"  # Replace with your free tier key
RAPIDAPI_HOST_UFO_SIGHTINGS = "ufo-sightings.p.rapidapi.com"
RAPIDAPI_HOST_UFO_AFICIONADO = "ufo-aficionado-api.p.rapidapi.com"

def test_ufo_sightings_api(api_key: str) -> Dict:
    """Test the UFO Sightings API (MUFON data)."""
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST_UFO_SIGHTINGS
    }
    
    results = {
        "api_name": "UFO Sightings (MUFON)",
        "endpoints_tested": [],
        "sample_responses": [],
        "errors": []
    }
    
    # Common endpoint patterns to test
    test_endpoints = [
        "/",
        "/sightings",
        "/recent",
        "/search",
        "/api/sightings",
        "/api/recent"
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"Testing endpoint: {endpoint}")
            url = f"https://{RAPIDAPI_HOST_UFO_SIGHTINGS}{endpoint}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            results["endpoints_tested"].append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_type": response.headers.get("content-type", ""),
                "rate_limit_remaining": response.headers.get("x-ratelimit-remaining", "unknown")
            })
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results["sample_responses"].append({
                        "endpoint": endpoint,
                        "sample_data": data[:2] if isinstance(data, list) else data,  # First 2 items or full object
                        "total_records": len(data) if isinstance(data, list) else 1,
                        "data_structure": analyze_data_structure(data)
                    })
                    print(f"✅ Success: {endpoint} returned {len(data) if isinstance(data, list) else 1} records")
                except json.JSONDecodeError:
                    results["errors"].append(f"Invalid JSON response from {endpoint}")
            else:
                print(f"❌ Failed: {endpoint} returned {response.status_code}")
                results["errors"].append(f"{endpoint}: HTTP {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {str(e)}")
            results["errors"].append(f"{endpoint}: {str(e)}")
        
        # Rate limiting - be respectful to free tier
        time.sleep(2)
    
    return results


def test_ufo_aficionado_api(api_key: str) -> Dict:
    """Test the UFO Aficionado API (88K reports)."""
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST_UFO_AFICIONADO
    }
    
    results = {
        "api_name": "UFO Aficionado API",
        "endpoints_tested": [],
        "sample_responses": [],
        "errors": []
    }
    
    # Common endpoint patterns to test
    test_endpoints = [
        "/",
        "/sightings",
        "/api/sightings",
        "/ufo",
        "/reports"
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"Testing UFO Aficionado endpoint: {endpoint}")
            url = f"https://{RAPIDAPI_HOST_UFO_AFICIONADO}{endpoint}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            results["endpoints_tested"].append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_type": response.headers.get("content-type", ""),
                "rate_limit_remaining": response.headers.get("x-ratelimit-remaining", "unknown")
            })
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results["sample_responses"].append({
                        "endpoint": endpoint,
                        "sample_data": data[:2] if isinstance(data, list) else data,
                        "total_records": len(data) if isinstance(data, list) else 1,
                        "data_structure": analyze_data_structure(data)
                    })
                    print(f"✅ Success: {endpoint} returned {len(data) if isinstance(data, list) else 1} records")
                except json.JSONDecodeError:
                    results["errors"].append(f"Invalid JSON response from {endpoint}")
            else:
                print(f"❌ Failed: {endpoint} returned {response.status_code}")
                results["errors"].append(f"{endpoint}: HTTP {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {str(e)}")
            results["errors"].append(f"{endpoint}: {str(e)}")
        
        time.sleep(2)  # Rate limiting
    
    return results


def analyze_data_structure(data) -> Dict:
    """Analyze the structure of API response data."""
    
    if isinstance(data, list):
        if len(data) == 0:
            return {"type": "empty_list"}
        
        # Analyze first item structure
        sample_item = data[0]
        return {
            "type": "list",
            "item_count": len(data),
            "sample_item_structure": analyze_item_structure(sample_item)
        }
    elif isinstance(data, dict):
        return {
            "type": "object",
            "keys": list(data.keys()),
            "structure": {k: type(v).__name__ for k, v in data.items()}
        }
    else:
        return {"type": type(data).__name__, "value": str(data)}


def analyze_item_structure(item) -> Dict:
    """Analyze structure of a single sighting record."""
    
    if not isinstance(item, dict):
        return {"type": type(item).__name__}
    
    structure = {}
    our_schema_mapping = {}
    
    # Map to our current schema fields
    for key, value in item.items():
        structure[key] = {
            "type": type(value).__name__,
            "sample_value": str(value)[:100] if value else None
        }
        
        # Try to map to our schema
        key_lower = key.lower()
        if any(x in key_lower for x in ['date', 'time']):
            our_schema_mapping[key] = "date_time"
        elif any(x in key_lower for x in ['city', 'location']):
            our_schema_mapping[key] = "city"
        elif 'state' in key_lower:
            our_schema_mapping[key] = "state"
        elif any(x in key_lower for x in ['shape', 'form']):
            our_schema_mapping[key] = "shape"
        elif any(x in key_lower for x in ['duration', 'length']):
            our_schema_mapping[key] = "duration"
        elif any(x in key_lower for x in ['summary', 'short']):
            our_schema_mapping[key] = "summary"
        elif any(x in key_lower for x in ['description', 'text', 'details', 'report']):
            our_schema_mapping[key] = "text"
        elif any(x in key_lower for x in ['lat', 'latitude']):
            our_schema_mapping[key] = "latitude"
        elif any(x in key_lower for x in ['lon', 'lng', 'longitude']):
            our_schema_mapping[key] = "longitude"
        elif any(x in key_lower for x in ['posted', 'reported', 'submitted']):
            our_schema_mapping[key] = "posted"
    
    return {
        "field_structure": structure,
        "schema_mapping": our_schema_mapping,
        "unmapped_fields": [k for k in item.keys() if k not in our_schema_mapping]
    }


def compare_with_our_schema(api_results: List[Dict]) -> Dict:
    """Compare API data structure with our current schema."""
    
    our_schema = {
        "id": "Primary key",
        "date_time": "DATETIME NOT NULL",
        "city": "VARCHAR(100) NOT NULL", 
        "state": "VARCHAR(10)",
        "shape": "VARCHAR(50) NOT NULL",
        "duration": "VARCHAR(100) NOT NULL",
        "summary": "TEXT NOT NULL",
        "text": "TEXT NOT NULL",
        "posted": "DATETIME NOT NULL",
        "latitude": "FLOAT",
        "longitude": "FLOAT"
    }
    
    comparison = {
        "our_schema": our_schema,
        "apis_analyzed": len(api_results),
        "mapping_analysis": [],
        "integration_feasibility": "unknown"
    }
    
    for api_result in api_results:
        if api_result["sample_responses"]:
            for response in api_result["sample_responses"]:
                if "data_structure" in response and "sample_item_structure" in response["data_structure"]:
                    mapping = response["data_structure"]["sample_item_structure"].get("schema_mapping", {})
                    comparison["mapping_analysis"].append({
                        "api": api_result["api_name"],
                        "endpoint": response["endpoint"],
                        "mapped_fields": len(mapping),
                        "total_fields": len(response["data_structure"]["sample_item_structure"]["field_structure"]),
                        "coverage_percentage": len(mapping) / len(our_schema) * 100,
                        "field_mapping": mapping
                    })
    
    return comparison


def main():
    """Main function to test RapidAPI UFO endpoints."""
    
    print("🛸 Testing RapidAPI UFO Sighting APIs")
    print("=" * 50)
    
    # Check if API key is set
    if RAPIDAPI_KEY == "YOUR_RAPIDAPI_KEY_HERE":
        print("❌ Please set your RapidAPI key in the RAPIDAPI_KEY variable")
        return
    
    results = []
    
    # Test UFO Sightings API
    print("\n🔍 Testing UFO Sightings API (MUFON data)...")
    ufo_sightings_results = test_ufo_sightings_api(RAPIDAPI_KEY)
    results.append(ufo_sightings_results)
    
    print("\n" + "="*50)
    
    # Test UFO Aficionado API
    print("\n🔍 Testing UFO Aficionado API (88K reports)...")
    ufo_aficionado_results = test_ufo_aficionado_api(RAPIDAPI_KEY)
    results.append(ufo_aficionado_results)
    
    print("\n" + "="*50)
    
    # Compare with our schema
    print("\n📊 Analyzing compatibility with our schema...")
    schema_comparison = compare_with_our_schema(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"rapidapi_test_results_{timestamp}.json"
    
    final_results = {
        "test_timestamp": datetime.now().isoformat(),
        "api_test_results": results,
        "schema_comparison": schema_comparison,
        "recommendations": generate_recommendations(results, schema_comparison)
    }
    
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    # Print summary
    print_summary(results, schema_comparison)


def generate_recommendations(api_results: List[Dict], schema_comparison: Dict) -> List[str]:
    """Generate integration recommendations based on test results."""
    
    recommendations = []
    
    # Check if any APIs returned data
    successful_apis = [api for api in api_results if api["sample_responses"]]
    
    if not successful_apis:
        recommendations.append("❌ No APIs returned usable data - consider alternative approaches")
        return recommendations
    
    # Analyze data coverage
    for analysis in schema_comparison["mapping_analysis"]:
        coverage = analysis["coverage_percentage"]
        if coverage >= 70:
            recommendations.append(f"✅ {analysis['api']} has good schema compatibility ({coverage:.1f}%)")
        elif coverage >= 40:
            recommendations.append(f"⚠️ {analysis['api']} has moderate compatibility ({coverage:.1f}%) - may need data enrichment")
        else:
            recommendations.append(f"❌ {analysis['api']} has poor compatibility ({coverage:.1f}%) - not recommended")
    
    return recommendations


def print_summary(api_results: List[Dict], schema_comparison: Dict):
    """Print a summary of the test results."""
    
    print("\n" + "="*50)
    print("📋 SUMMARY")
    print("="*50)
    
    for api_result in api_results:
        print(f"\n🛸 {api_result['api_name']}")
        print(f"   Successful endpoints: {len([e for e in api_result['endpoints_tested'] if e['status_code'] == 200])}")
        print(f"   Errors: {len(api_result['errors'])}")
        
        if api_result["sample_responses"]:
            for response in api_result["sample_responses"]:
                print(f"   📊 {response['endpoint']}: {response['total_records']} records")
    
    print(f"\n🔄 Schema Compatibility Analysis:")
    for analysis in schema_comparison["mapping_analysis"]:
        print(f"   {analysis['api']}: {analysis['coverage_percentage']:.1f}% field coverage")
    
    print(f"\n📝 Recommendations:")
    for rec in schema_comparison.get("recommendations", []):
        print(f"   {rec}")


if __name__ == "__main__":
    main()