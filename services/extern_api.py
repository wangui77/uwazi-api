import requests  # type: ignore

def post(url, data):
    # Make a POST request to the URL with the given data
    try:
        res = requests.post(url, data=data)

        # Check for successful response (HTTP 201)
        if res.status_code == 201:
            print("Data posted successfully!")
            return res.json()  # Return the response data (JSON)
        
        # If not a successful post, handle the error
        print(f"Error: {res.status_code}")
        return {"error": "Failed to upload"}, 400
    
    except requests.exceptions.RequestException as e:
        # Handle exceptions (network errors, timeouts, etc.)
        print(f"An error occurred: {e}")
        return {"error": "Failed to post data"}, 500


def get(url, data=None):
    # Make a GET request to the URL with or without data (optional)
    try:
        if data is not None:
            res = requests.get(url, data=data)
        else:
            res = requests.get(url)

        # Check for successful response (HTTP 200)
        if res.status_code == 200:
            return res.json()  # Return the response data (JSON)
        
        # If the response is not successful, return an error message
        print(f"Error: {res.status_code}")
        return {"error": res.json()}, 400

    except requests.exceptions.RequestException as e:
        # Handle exceptions (network errors, timeouts, etc.)
        print(f"An error occurred: {e}")
        return {"error": "Failed to fetch data"}, 500


def main():
    # Test POST request
    url_post = 'https://uwazitek-2.onrender.com/process-invoice'
    data = {
        "invoice_text":"jhefvjhbreiusdgtcvkejbdckdjbcghkjdshbc"
    }
    print("Testing POST request...")
    response = post(url_post, data)
    print("POST Response:", response)

    # Test GET requesthttps://uwazitek-2.onrender.com/generate-report
    url_get = ''
    
    print("\nTesting GET request...")
    response = get(url_get)
    print("GET Response:", response)


if __name__ == "__main__":
    main()