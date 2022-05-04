# Copyright 2022 The Elekto Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author(s): Dawn M. Foster <fosterd@vmware.com>

"""
Before using this script, please make sure that you are adhering 
to the GitHub Acceptable Use Policies:
https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies
In particular, "You may not use information from the Service 
(whether scraped, collected through our API, or obtained otherwise)
for spamming purposes, including for the purposes of sending unsolicited
emails to users or selling User Personal Information (as defined in the
GitHub Privacy Statement), such as to recruiters, headhunters, and job boards."

Takes an elekto voters.yaml file with a list of "eligible_voters:"
GitHub logins, and attempts to use the GitHub API to get an email
for each person to make it possible to send email reminders to eligible
voters. 

If an email address is in the GitHub profile, that is used first. Otherwise,
it attempts to find an email address from the most recent commit. If the
email contains the string 'noreply' it is not written to the csv file.

As output, a csv file of this format containing comma separated email addresses 
is created:
elekto_emails_GHorgName_YYYYMMDD.csv

A message with the number of email addresses found out of the total voters
is printed to the screen

Parameters
----------
org_name : str
    The primary GitHub organization for the vote.
    Used to gather email address from commits
file_name : str
    This should be an Elekto yaml file starting with "eligible_voters:"
"""

def read_args():
    """Reads the org name and yaml filename where the votes can be found.
    
    Parameters
    ----------
    None

    Returns
    -------
    org_name : str
        The primary GitHub organization for the vote.
        Used to gather email address from commits
    file_name : str
        This should be an Elekto yaml file (raw) starting with "eligible_voters:" Example:
        https://raw.githubusercontent.com/knative/community/main/elections/2021-TOC/voters.yaml
    """
    import sys

    # read org name and filename from command line or prompt if no 
    # arguments were given.
    try:
        org_name = str(sys.argv[1])
        file_name = str(sys.argv[2])

    except:
        print("Please enter the org name and filename for voters.yaml.")
        org_name = input("Enter a GitHub org name (like kubernetes): ")
        file_name = input("Enter a file name (like https://raw.githubusercontent.com/knative/community/main/elections/2021-TOC/voters.yaml): ")

    api_token = input("Enter your GitHub Personal Access Token: ")

    return org_name, file_name, api_token

def get_email(org, username, api_token):
    """Attempts to get an email address from the GitHub profile first. 
    Otherwise, it attempts to find an email address from the most recent
    commit, which is why the name of the GitHub org is required. If the
    email contains the string 'noreply' it is not written to the csv file.
    
    Parameters
    ----------
    org : str
        The primary org name where the users can be found
    username : str
        GitHub username

    Returns
    -------
    email : str
    """

    import sys
    from github import Github # Uses https://github.com/PyGithub/

    try:
        g = Github(api_token)
    except:
        print("Cannot read gh_key file or does not contain a valid GitHub API token?")
        sys.exit()

    try:
        email = g.get_user(username).email

        email_list = []

        if email == None:
            repo_list = g.get_organization(org).get_repos()

            for repo in repo_list:
                commits = repo.get_commits(author=username)

                if commits.totalCount > 0:
                    email_list.append([commits[0].commit.author.email, commits[0].commit.author.date, repo.name])

            if len(email_list) > 0:
                newest = sorted(email_list, key = lambda x: x[1], reverse = True)
                email = newest[0][0]
            else:
                email = None
        if 'noreply' in email:
            email = None
    except:
        email = None

    return(email)

import sys
import yaml
import csv
import urllib.request
from datetime import datetime

org_name, file_name, api_token = read_args()

# Loads the yaml file and creates a list of voters
try:
    
    voters_file = urllib.request.urlopen(file_name)
    voters = yaml.safe_load(voters_file)
    voter_list = voters['eligible_voters']

except:
    print("Cannot load or process the yaml file. Did you use the raw link?")
    sys.exit()

print("Gathering email addresses from GitHub. This may take a while.")

# Create a list for the emails and initialize a counter for the
# number of emails found.
email_list = []
found_count = 0

# Attempt to get an email address for each voter. If an email address is found
# append it to the list and increment the counter.
for username in voter_list:
    email = get_email(org_name, username, api_token)
    if email:
        email_list.append(email)
        found_count+=1
        print(email)

# Print status and write emails to the csv file.
print("Found emails for", found_count, "out of", len(voter_list), "voters")

# Open the CSV file for writing
today = datetime.today().strftime('%Y-%m-%d')
outfile_name = 'elekto_emails_' + org_name + "_" + today + '.csv'
f = open(outfile_name,'w')
csv_file = csv.writer(f)

csv_file.writerow(email_list)
f.close()
