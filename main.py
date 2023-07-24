import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import requests

comment_line = '\n___________\n'
header_line =  '\n###########\n'

def load_credentials():
    load_dotenv()
    credentials = {
        "server": os.environ.get("SERVER"),
        "username": os.environ.get("USERNAME"),
        "password": os.environ.get("PASSWORD"), # Probably your account api key - not ur password 
        "project_key": os.environ.get("PROJECT_KEY"),
    }
    return credentials

def get_issues(credentials, start_at=0, max_results=100):
    response = requests.get(
        f"{credentials['server']}/rest/api/2/search?jql=project={credentials['project_key']}&fields=comment&maxResults={max_results}&startAt={start_at}",
        auth=(credentials['username'], credentials['password'])
    )
    response.raise_for_status()
    data = response.json()
    return data["issues"]

def get_public_comments_from_issue(issue):
    public_comments = []
    for comment in issue["fields"]["comment"]["comments"]:
        if comment['jsdPublic']:
            author_name = comment['author']['displayName']
            creation_date = comment['created']
            comment_body = comment['body']
            comment_info = f"{header_line}Author: {author_name}\nDate: {creation_date}{header_line}Comment: {comment_body}"
            public_comments.append(comment_info)
    return comment_line.join(public_comments)

def main():
    credentials = load_credentials()
    df = pd.DataFrame(columns=["Ticket", "Public Comments"])
    start_at = 0
    while True:
        issues = get_issues(credentials, start_at=start_at)
        if not issues:
            break
        for issue in issues:
            public_comments = get_public_comments_from_issue(issue)
            new_df = pd.DataFrame({"Ticket": [issue["key"]], "Public Comments": [public_comments]})
            df = pd.concat([df, new_df], ignore_index=True)
        start_at += 100
    df.to_csv(f"{credentials['project_key']}-Export-{datetime.today().strftime('%Y-%m-%d')}.csv", index=False)

if __name__ == "__main__":
    main()
