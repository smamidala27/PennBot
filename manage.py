import requests
import os
import json
from pick import pick
import argparse

parser = argparse.ArgumentParser(description="Control Yalebot directly")
parser.add_argument("verb", choices=("create_bot", "destroy_bot", "send"))
parser.add_argument("--token", default=os.environ.get("GROUPME_ACCESS_TOKEN"))
parser.add_argument("--groups-file", default="groups.json")
args = parser.parse_args()

def read(prop, default):
    return input(f"{prop} [{default}]: ") or default

def get_user_groups():
    return requests.get(f"https://api.groupme.com/v3/groups?token={args.token}").json()["response"]

def get_joined_groups():
    with open(args.groups_file, "r") as f:
        return json.load(f)

def pick_joined_group() -> str:
    """
    :return: ID of group chosen
    """
    groups = get_joined_groups()
    group_name = pick([groups[group_id]["name"] for group_id in groups])[0]
    # Knowing name chosen, get group ID
    for candidate in groups:
        if groups[candidate]["name"] == group_name:
            group_id = candidate
            break
    print(f"Selected group {group_id}/{group_name}.")

def pick_user_group() -> str:
    """
    :return:
    """
    groups = get_user_groups()
    group_name = pick([group["name"] for group in groups])[0]
    # Knowing name chosen, get group id
    for candidate in groups:
        if candidate["name"] == group_name:
            group_id = candidate["group_id"]
            break
    print(f"Selected group {group_id}/{group_name}.")


if args.verb == "create_bot":
    group_id = pick_user_group()

    bot = {
        "name": read("name", "yalebot"),
        "group_id": group_id,
        "avatar_url": read("avatar url", "https://i.groupme.com/310x310.jpeg.1c88aac983ff4587b15ef69c2649a09c"),
        "callback_url": read("callback url", "https://yalebot.herokuapp.com/"),
        "dm_notification": false,
    }
    result = requests.post(f"https://api.groupme.com/v3/bots?token={args.token}",
                           json={"bot": bot}).json()["response"]["bot"]

    groups = get_joined_groups()
    groups[result["group_id"]] = {
        "name": bot["name"],
        "bot_id": result["bot_id"],
    }
    with open(args.groups_file, "r+") as f:
        json.dump(groups, f)
elif args.verb == "destroy_bot":
    group_id = pick_joined_group()
    request = requests.post(f"https://api.groupme.com/v3/bots/destroy?token={args.token}", data={"bot_id": groups[group_id]["bot_id"]})
    if request.ok:
        print("Success.")
        with open(args.groups_file, "w") as f:
            del groups[group_id]
            json.dump(groups, f)
    else:
        print("Failure: ", end="")
        print(request.json())
elif args.verb == "send":
    group_id = pick_joined_group()
    text = input("Message: ")
    requests.post("https://api.groupme.com/v3/bots/post", data={"text": text, "bot_id": groups[group_id]["bot_id"]})
