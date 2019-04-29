# Copyright (C) 2019 Frederick W. Nielsen
#
# This file is part of headshotTools.
#
# headshotTools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# headshotTools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with headshotTools.  If not, see <http://www.gnu.org/licenses/>.

"""
Processes a CSV with email addresses and URLs that return headshot images and
bulks load these to Webex Common Identity user accounts listed.

Requires an auth token from a user with admin privileges against the Webex Control Hub org.
"""

import csv
import json
import os
import sys
import time
import urllib

import requests
import yaml

CONFIG_FILE = "../config.yml"
WXTAPI_HEADERS = {"Accept" : "application/json", "Content-Type":"application/json"}

def wxt_get_person(email, myheaders):
    """retrieve user details via Webex Teams API based on email address"""
    get_person_url = 'https://api.ciscossspark.com/v1/people?email={0}'
    response = requests.get(get_person_url.format(urllib.parse.quote(email)), headers=myheaders)
    return response

def wxt_update_person(person_id, data, myheaders):
    """update user details via Webex Teams API based on person ID and formatted JSON"""
    update_person_url = 'https://api.ciscospark.com/v1/people/{0}'
    response = requests.put(update_person_url.format(person_id),
                            data=json.dumps(data),
                            headers=myheaders)
    return response

def main():
    """processes external CSV and updates user avatars"""
    # load separate config file with non-portable parameters, in this case a temp auth token
    # Obtain a 12-hour access token at https://developer.webex.com/docs/api/getting-started
    # We're looking for the token presented like this in a YAML file:
    """
    wxteams:
      auth_token: JB3+FXy71SO9f+ti9D23JQ-291a-4dd5-9f12-a7342bd3ea9d50
    """

    with open(CONFIG_FILE, 'r') as config_file:
        ext_config = yaml.full_load(config_file)['wxteams']

    # set up neccessary HTTP headers
    auth_bearer = {"Authorization": "Bearer " + ext_config['auth_token']}
    request_headers = {**WXTAPI_HEADERS, **auth_bearer}

    # read action list from CSV file
    # CSV format should be email,avatarURL WITH header row (which we intentionally skip)
    update_input_file = os.path.splitext(os.path.basename(__file__))[0] + ".csv"
    with open(update_input_file, 'r') as file:
        user_updates = list(csv.reader(file))

    for (user, avatar) in user_updates[1:]:
        try:
            # retry flag, used when API returns unexpected results
            retry = True
            while retry:
                print(f"Working on: {user}, ", end='')
                # attempt to retrieve person details
                getperson_result = wxt_get_person(user, request_headers)
                if getperson_result.status_code < 300:
                    # person details are returned as lists of dictionaries under 'items'
                    if getperson_result.json().get('items'):
                        # grab the first (and hopefully only) list entry
                        person_details = getperson_result.json().get('items')[0]
                        # extract person UID, used later to update person
                        person_id = person_details['id']
                        # replace if present or add avatar entry
                        person_details.update({"avatar":avatar})
                        # API returns timeZone for some persons, but doesn't accept it in updates
                        # so let's remove it
                        del person_details['timeZone']
                        # update our person with a new avatar
                        updateperson_result = wxt_update_person(person_id,
                                                                person_details,
                                                                request_headers)
                        print(f"HTTP status: {updateperson_result.status_code}")
                    else:
                        # if items dictionary is empty then no matching user was located
                        print("user does not exist")
                    retry = False
                else:
                    print(f"Failed due to lookup user because: {getperson_result.status_code}")
                    if getperson_result.status_code == 429:
                        # Sometimes the API gets busy and asks you to come back
                        sleep_time = getperson_result.headers.get('Retry-After')
                        if sleep_time is None:
                            sleep_time = 60
                        else:
                            sleep_time = int(sleep_time)
                        print(f"Sleeping for {sleep_time} seconds before trying again.")
                        time.sleep(sleep_time)
                    else:
                        # Most other errors are non-recoverable
                        print(getperson_result.json())
                        sys.exit("Stopping here because this error will likely repeat.")

        except Exception as exception:
            print(exception)

if __name__ == "__main__":
    main()
