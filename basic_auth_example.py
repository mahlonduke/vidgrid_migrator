# Import library dependencies
import requests
import json
import base64

# Local file dependencies
import api_config

# API Variables
deployment = 'your-deployment'
clientId = api_config.clientId
clientSecret = api_config.clientSecret

# API Endpoint Setup
urlAffiliations = f'https://{deployment}.api.accelo.com/api/v0/companies?_fields=id,name&_limit=1'
urlAuthorize = f'https://{deployment}.api.accelo.com/oauth2/v0/token'

# Encode the Client ID and Secret
preCoding = f'{clientId}:{clientSecret}'
encoded = str(base64.b64encode(preCoding.encode("utf-8")), "utf-8")

# API Request Setup - for authentication
authHeaders = {'Authorization': f'Basic {encoded}',
          'Content-Type': 'application/json'}
body = {
    "grant_type": "client_credentials",
    "scope": "read(all)",
    "expires_in": "3600"
}

# Print the details for debugging
print("--------------------Debugging Details------------------------------")
# App details to be used for authentication
print("Authentication:")
print(f'Client ID: {clientId}')
print(f'Client Secret: {clientSecret}')
print(f'Encoded ID & Secret: {encoded}\n\n')

# Authentication request details
print(f'Token Request Header: {authHeaders}')
print(f'Token Request Body: {body}\n\n')

# Request a new token from the Accelo API, using the app authentication details
response = requests.post(urlAuthorize, headers=authHeaders, data=json.dumps(body)).json()

# Store the token that the Accelo API returns
token = response['access_token']
print(f'Access Token returned when supplying encoded ID & secret: {token}')

# API Header Setup Using new Token
headers = {'Content-Type': 'application/json',
          'Authorization': f'Bearer {token}'}
print(f'Request Header Using new Token: {headers}')

# Make a test request of the API, and print the result
response = requests.get(urlAffiliations, headers=headers).json()
print(f'Response from the API when making a request using the new token:   {response["meta"]["message"]}')
print("------------------End Debugging Details------------------------------")
