import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("--- Starting API Tests ---")
    
    # 1. Test Root
    try:
        response = requests.get(BASE_URL + "/")
        print("Root endpoint: " + str(response.status_code) + " - " + str(response.json()))
    except Exception as e:
        print("Root endpoint error: " + str(e))
        return

    # 2. Test Waitlist (POST)
    try:
        data = {"email": "tester@example.com"}
        response = requests.post(BASE_URL + "/waitlist", json=data)
        print("Waitlist endpoint: " + str(response.status_code) + " - " + str(response.json()))
    except Exception as e:
        print("Waitlist error: " + str(e))

    # 3. Test Deals Search (GET)
    try:
        query = "iphone"
        response = requests.get(BASE_URL + "/deals?q=" + query)
        print("Deals endpoint (" + query + "): " + str(response.status_code))
        results = response.json()
        print("Found " + str(results['count']) + " deals.")
        if results['count'] > 0:
            print("First result: " + results['results'][0]['title'] + " from " + results['results'][0]['platform'])
    except Exception as e:
        print("Deals error: " + str(e))

    print("--- Tests Complete ---")

if __name__ == "__main__":
    test_api()

