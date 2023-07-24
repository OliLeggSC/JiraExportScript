# Jira External Comment Export Script

## Getting scripts to work
Install python3
```sh
brew install python3
```
```sh
python3 -m pip install python-dotenv pandas requests
touch .env
```
Populate your .env
```sh
# Populate .env:
SERVER="https://<<CompanyName>>.atlassian.net/"
PROJECT_KEY="ProjectName"
USERNAME="xyz@ikj.com"
PASSWORD="" # Probably your account api key - not ur actual password 
```

Running it:
```sh
python3 main.py
```
