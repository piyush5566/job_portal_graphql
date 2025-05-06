"""
Test script to verify that the GraphQL implementation is working correctly.

This script makes a GraphQL query to the API and displays the results.
"""

import requests
import json
import sys

def test_graphql_query():
    """Test a simple GraphQL query to the API."""
    url = "http://localhost:5000/graphql"
    
    # Simple query to get all jobs
    query = """
    query {
        jobs {
            id
            title
            company
            location
            category
        }
    }
    """
    
    try:
        response = requests.post(
            url,
            json={"query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GraphQL query successful!")
            print("\nResponse data:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ GraphQL query failed with status code: {response.status_code}")
            print("\nResponse:")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error making GraphQL request: {e}")
        return False

if __name__ == "__main__":
    print("Testing GraphQL implementation...")
    success = test_graphql_query()
    
    if success:
        print("\n🎉 GraphQL implementation is working correctly! 🎉")
        sys.exit(0)
    else:
        print("\n❌ GraphQL implementation has issues that need to be resolved.")
        sys.exit(1)