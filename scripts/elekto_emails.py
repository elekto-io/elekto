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

As output, a csv file of this format containing semicolon separated email addresses 
is created (semincolon separated allows for easy copy / paste into your email client):
elekto_emails_YYYYMMDD.csv

Each email address found is printed to the screen as a way to indicate progress,
and a message with the number of email addresses found out of the total voters
along with the name of the results csv file is printed to the screen at the end.

Parameters
----------
file_name : str
    This should be an Elekto yaml file starting with "eligible_voters:"
"""

def read_args():
    """Reads the yaml filename where the voters can be found and prompts for a 
       GitHub API Personal Access Token.
    
    Parameters
    ----------
    None

    Returns
    -------
    file_name : str
        This should be an Elekto yaml file (raw) starting with "eligible_voters:" Example:
        https://raw.githubusercontent.com/knative/community/main/elections/2022-TOC/voters.yaml
    """
    import sys

    # read filename from command line or prompt if no 
    # arguments were given.
    try:
        file_name = str(sys.argv[1])

    except:
        print("Please enter the filename for voters.yaml.")
        file_name = input("Enter a file name (like https://raw.githubusercontent.com/knative/community/main/elections/2021-TOC/voters.yaml): ")

    api_token = input("Enter your GitHub Personal Access Token: ")

    return file_name, api_token


def email_query():
    """This contains the GitHub GraphQL API Query to get an email address from the 
       profile and commits
    Returns
    -------
    str
    """
    return """query pr_info_query($user_login: String!, $start_date: DateTime!, $end_date: DateTime!){
             user(login: $user_login) {
                email
                contributionsCollection(from: $start_date, to: $end_date){
                    pullRequestContributions(first: 10){
                        nodes{
                            pullRequest{
                                commits(first: 10){
                                    nodes{
                                        url
                                        commit{
                                            authoredByCommitter
                                            author{
                                                email
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }"""

def get_email(username, api_token):
    """Attempts to get an email address from the GitHub profile first. 
    Otherwise, it attempts to find an email address from the most recent
    commit. If the email contains the string 'noreply' it is not written 
    to the csv file.
    
    Parameters
    ----------
    username : str
        GitHub username

    Returns
    -------
    email : str
    """

    import requests
    import json
    import sys
    from dateutil.relativedelta import relativedelta

    # Set GitHub GraphQL API variables
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': 'token %s' % api_token}

    # Set query variables including dates for past 12 months (req for query)
    today = datetime.now()
    end_date = today.isoformat() #isoformat required for json serialization
    start_date = (today + relativedelta(months=-12)).isoformat() 
    variables = {"user_login": username, "start_date": start_date, "end_date": end_date}

    # Run query and load the results into a JSON file
    query = email_query()
    r = requests.post(url=url, json={'query': query, 'variables': variables}, headers=headers)
    json_data = json.loads(r.text)

    # Error checking
    error = False
    if r.ok: # the request succeeds and the GH token is valid
        # check for and print errors returned from API before exiting
        # insufficient scope for your token would be a common error caught here
        try: 
            print("Error:", json_data['errors'][0]['type'])
            print(json_data['errors'][0]['message'])
            print( "Exiting ...")
            error = True
        except:
            pass # keep going because there are no errors
    else: # request failed - often due to invalid GH token
        try: # request fails with a message
            print("Error:", json_data['message'])
            print( "Exiting ...")
        except: # request failed for some reason that doesn't generate a message
            print("Unknown Error. Exiting ...")
        error = True

    if error: # Exit after any request or API error
        sys.exit(1)

    # Get email address
    email = None

    # Try to get the email address from the profile first
    # This will fail and return immediately if the user has been deleted.
    try:
        email = json_data['data']['user']['email']
    except:
        print(username, "not found")
        return email
    
    # If the profile didn't have an email address, loop through the PRs and commits
    # until you find an email address in a commit where the commit was authored by
    # username (since PRs can have commits from other people) and does not contain
    # 'noreply' anywhere in the email address.  
    if email == None or email == '':
        try:
            for pr in json_data['data']['user']['contributionsCollection']['pullRequestContributions']['nodes']:
                for commits in pr['pullRequest']['commits']['nodes']:
                    authoredBy = commits['commit']['authoredByCommitter']
                    if authoredBy:
                        email = commits['commit']['author']['email']
                        if 'noreply' not in email:
                            break
                        else:
                            email = None
        except:
            pass

    return(email)

import sys
import yaml
import csv
import urllib.request
from datetime import datetime

file_name, api_token = read_args()

# Loads the yaml file and creates a list of voters
try:
    
    voters_file = urllib.request.urlopen(file_name)
    voters = yaml.safe_load(voters_file)
    voter_list = voters['eligible_voters']

except:
    print("Cannot load or process the yaml file. Did you use the raw link?")
    sys.exit()

print("Gathering email addresses from GitHub. This will take ~3 minutes for 100 voters.")

# Create a list for the emails and initialize a counter for the
# number of emails found.
email_list = []
found_count = 0

# Attempt to get an email address for each voter. If an email address is found
# append it to the list and increment the counter. Also print to the screen to
# show that the script is progressing.
for username in voter_list:
    email = get_email(username, api_token)
    if email:
        email_list.append(email)
        found_count+=1
        print(email)

# Open the CSV file for writing
today = datetime.today().strftime('%Y-%m-%d')
outfile_name = 'elekto_emails_' + today + '.csv'
f = open(outfile_name,'w')
csv_file = csv.writer(f, delimiter =';')

# Print status and write emails to the csv file.
print("Found emails for", found_count, "out of", len(voter_list), "voters")
print("Your results can be found in", outfile_name)

csv_file.writerow(email_list)
f.close()
