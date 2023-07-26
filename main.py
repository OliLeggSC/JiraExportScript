import os
import re
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import requests

COMMENT_LINE = "\n___________\n"
HEADER_LINE = "\n###########\n"


def load_credentials():
    load_dotenv()
    credentials = {
        "server": os.environ.get("SERVER"),
        "username": os.environ.get("USERNAME"),
        "password": os.environ.get("PASSWORD"),
        "project_key": os.environ.get("PROJECT_KEY"),
    }
    return credentials


credentials = load_credentials()

jira_http_get = lambda url, stream=False: requests.get(
    url,
    stream=stream,
    auth=(credentials["username"], credentials["password"]),
)


def get_issues(credentials, start_at=0, max_results=100):
    response = jira_http_get(
        f"{credentials['server']}/rest/api/2/search?jql=project={credentials['project_key']}&fields=comment,summary,description,status,created,attachment&maxResults={max_results}&startAt={start_at}"
    )
    response.raise_for_status()
    data = response.json()
    return data["issues"]


def get_public_comments_from_issue(issue):
    public_comments = []
    for comment in issue["fields"]["comment"]["comments"]:
        if "jsdPublic" in comment and comment["jsdPublic"]:
            author_name = comment["author"]["displayName"]
            creation_date = comment["created"]
            comment_body = comment["body"]
            comment_info = f"{HEADER_LINE}Author: {author_name}\nDate: {creation_date}{HEADER_LINE}Comment: {comment_body}"
            public_comments.append(comment_info)
    return COMMENT_LINE.join(public_comments)


def get_private_comments_from_issue(issue):
    private_comments = []
    for comment in issue["fields"]["comment"]["comments"]:
        if not comment.get("jsdPublic", False):
            private_comments.append(comment["body"])
    return private_comments


def get_mentioned_files_in_comments(comments):
    mentioned_files = set()
    pattern = r"\[\^([^\]]+)\]"
    for comment in comments:
        mentioned_files.update(re.findall(pattern, comment))
    return mentioned_files


def make_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def download_attachments(issue_key, attachments, private_files):
    make_dir("attachments")
    for attachment in attachments:
        if attachment["filename"] not in private_files:
            file_path = os.path.join("attachments", issue_key, attachment["filename"])
            if os.path.exists(file_path):
                print(f"Skipping {file_path}, already downloaded.")
                continue

            response = jira_http_get(attachment["content"], stream=True)
            try:
                response.raise_for_status()
                make_dir(os.path.join("attachments", issue_key))
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            except Exception as e:
                with open(os.path.join("attachments", "failed-downloads.txt"), "a") as file:
                    file.write(f"Failed {issue_key} {attachment['filename']}: {e}\n")

def get_data_from_issue(issue):
    ticket = issue["key"]
    summary = issue["fields"]["summary"]
    description = issue["fields"]["description"]
    status = issue["fields"]["status"]["name"]
    created = issue["fields"]["created"]
    public_comments = get_public_comments_from_issue(issue)
    return {
        "Ticket": ticket,
        "Summary": summary,
        "Description": description,
        "Status": status,
        "Created": created,
        "Public Comments": public_comments,
    }


def main():
    df = pd.DataFrame(columns=["Ticket", "Public Comments"])
    start_at = 0
    while True:
        issues = get_issues(credentials, start_at=start_at)
        if not issues:
            break
        for issue in issues:
            private_comments = get_private_comments_from_issue(issue)
            private_files = get_mentioned_files_in_comments(private_comments)
            download_attachments(
                issue["key"], issue["fields"]["attachment"], private_files
            )
            data = get_data_from_issue(issue)
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        start_at += 100
    df.to_csv(
        f"{credentials['project_key']}-Export-{datetime.today().strftime('%Y-%m-%d')}.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
