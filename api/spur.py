import http.client
import json

def get_example_context():
    '''
    Get an example context for testing purposes.
    I cannot figure out how to set an API key in Maltego for a local transform
    without hardcoding it, so I'm using example context for testing.
    '''
    import os
    script_dir = os.path.dirname(__file__)
    filename = "context_example_2.json"
    file_path = os.path.join(script_dir, filename)
    return json.loads(open(file_path, "r").read())

def get_context_for_ip(ip_address: str, api_key: str):
    '''
    Get context for an IP address using the Spur API.
    '''

    if api_key == "example-api-key":
        return get_example_context()

    host = "api.spur.us"
    endpoint = f"/v2/context/{ip_address}"
    headers = {
        "Token": api_key,
        "Content-Type": "application/json"
    }

    conn = http.client.HTTPSConnection(host)
    conn.request("GET", endpoint, headers=headers)
    response = conn.getresponse()
    if response.status == 200:
        data = response.read()
        return json.loads(data.decode("utf-8"))
    elif response.status == 401:
        raise Exception(f"Unauthorized. Check your Spur API key. Status code: {response.status}")
    else:
        raise Exception(f"Failed to query IP. Status code: {response.status}")
