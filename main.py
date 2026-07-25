import scratchattach as sa
import warnings
import commons
import csv
import random
import time
import os
import json

from key import b64
from bot import Bot
from bot import CommentPostWarning
from scratchattach.utils.exceptions import CommentPostFailure

# Disable warnings
warnings.filterwarnings(action="ignore", category=sa.LoginDataWarning)
warnings.filterwarnings(action="ignore", category=sa.GetAuthenticationWarning)

# Target project
PROJECT_ID: int = 1364330722

# Command prefix
PREFIX: str = "&gt;bot"

# Connect the command project
project: sa.Project = sa.get_project(PROJECT_ID)

# Owned bots
bots: dict[str, Bot] = {}

# Load bots into the bots dictionary
with open("owners.json", 'r') as f:
    owners: dict[str, str] = json.load(f)

with open("accounts.txt", 'r') as f:
    reader = csv.reader(f)
    accounts: dict[str, str] = {}

    for row in reader:
        username, password = row
        accounts[username] = password

for owner, username in owners.items():
    if username in accounts:
        bots[owner] = Bot(username, accounts[username])


# Alert bot
session: sa.Session = sa.login("tortesting", os.environ.get("SCRATCH_PASSWORD"))
poster: sa.Project = session.connect_project(PROJECT_ID)

# Claim codes
codes: dict[str, dict[str, bool | str]] = json.load(open("codes.json", 'r'))

# Reviewed comments
reviewed_comments: list[int] = []


# Safely reply to a comment
def reply_comment(content: str, parent_id: int):
    if session.mute_status is None:
        try:
            poster.reply_comment(content, parent_id=parent_id)
        except CommentPostFailure as err:
            warnings.warn(f"Comment failed to post because {err}", CommentPostWarning)
    else:
        warnings.warn("Poster bot is muted")


# Set status to the command project
poster.set_notes("ONLINE\nCredits to @TimMcCool for scratchattach")

try:
    while True:
        comment = project.comments(limit=1, offset=0)[0]

        if comment.id not in reviewed_comments:
            print(comment.content)
            if comment.content.startswith(PREFIX):
                args: list[str] = comment.content.split(" ")
                print(f"Command: {args}")

                # Check if the user ran claim
                if args[1] == "claim":
                    print("Running claim command")
                    if comment.author_name not in bots:
                        # Check if the code exists in codes
                        if args[2] in codes:
                            if not codes[args[2]]["expired"]:
                                password: str
                                with open("accounts.txt", 'r') as f:
                                    reader = csv.reader(f)

                                    for row in reader:
                                        if row[0] == codes[args[2]]["name"]:
                                            password = row[1]
                                            break

                                bots[comment.author_name] = Bot(
                                    codes[args[2]]["name"], password
                                )
                                codes[args[2]]["expired"] = True
                                owners[comment.author_name] = codes[args[2]]["name"]

                                reply_comment(
                                    f"You now own the bot @{codes[args[2]]["name"]}! (ID: {random.randint(1, 1000)})",
                                    parent_id=comment.id,
                                )
                            else:
                                reply_comment(f"This bot has already been claimed!", comment.id)
                                print("This code has already been used")
                        else:
                            # Scan accounts.txt for the code
                            name: str = b64.decode(args[2])
                            with open("accounts.txt", 'r') as f:
                                reader = csv.reader(f)

                                for row in reader:
                                    if name == row[0]:
                                        bots[comment.author_name] = Bot(name, row[1])
                                        owners[comment.author_name] = name
                                        reply_comment(
                                            f"You now own the bot @{name}! (ID: {random.randint(1, 1000)})",
                                            parent_id=comment.id,
                                        )
                                        break
                    else:
                        print("User already owns a bot")
                        reply_comment(
                            f"You already own a bot! (ID: {random.randint(1, 1000)})",
                            parent_id=comment.id,
                        )

                # Check if the user ran target
                elif args[1] == "target":
                    if comment.author_name in bots:
                        bot: Bot = bots[comment.author_name]
                        try:
                            bot.target(int(args[2]))
                            print("Set bot target")
                        except ValueError as e:
                            warnings.warn("User did not provide a valid integer")
                    else:
                        print("User doesn't own any bots")
                        reply_comment(f"You don't own any bots! (ID: {random.randint(1, 1000)})", comment.id)

                # Check if the user ran advertise
                elif args[1] == "advertise":
                    if comment.author_name in bots:
                        bot: Bot = bots[comment.author_name]
                        try:
                            bot.advertise(int(args[2]))
                            print("Set bot ad")
                        except ValueError as e:
                            warnings.warn("User did not provide a valid integer")
                    else:
                        print("User doesn't own any bots")
                        reply_comment(f"You don't own any bots! (ID: {random.randint(1, 1000)})", comment.id)

                # Check if the user ran start
                elif args[1] == "start":
                    if comment.author_name in bots:
                        bot: Bot = bots[comment.author_name]
                        bot.start()

                        time.sleep(1)

                        if commons.warning is not None:
                            print(f"Failed to start bot: {commons.warning}")
                            reply_comment(f"Failed to start bot: {commons.warning} (ID: {random.randint(1, 1000)})", comment.id)
                            commons.warning = None
                        else:
                            print("Successfully started bot")
                            reply_comment(f"Successfully started bot! (ID: {random.randint(1, 1000)})", comment.id)
                    else:
                        print("User doesn't own any bots")
                        reply_comment(f"You don't own any bots! (ID: {random.randint(1, 1000)})", comment.id)

                elif args[1] == "stop":
                    if comment.author_name in bots:
                        bot: Bot = bots[comment.author_name]
                        bot.stop()

                        time.sleep(1)

                        if commons.warning is not None:
                            print(f"Failed to stop bot: {commons.warning}")
                            reply_comment(f"Failed to stop bot: {commons.warning} (ID: {random.randint(1, 1000)})", comment.id)
                            commons.warning = None
                        else:
                            print("Successfully stopped bot")
                            reply_comment(f"Successfully stopped bot! (ID: {random.randint(1, 1000)})", comment.id)
                    else:
                        print("User doesn't own any bots")
                        reply_comment(f"You don't own any bots! (ID: {random.randint(1, 1000)})", comment.id)

        # Add the comment ID to the list so the script doesn't rerun it
        reviewed_comments.append(comment.id)
        time.sleep(1)

except KeyboardInterrupt:
    print("Program stopped. Saving...")

    with open("codes.json", 'w') as f:
        json.dump(codes, f, indent=2)

    with open("owners.json", 'w') as f:
        json.dump(owners, f, indent=2)

    poster.post_comment(f"END (ID: {random.randint(1, 1000)})")
    poster.set_notes("OFFLINE\nCredits to @TimMcCool for scratchattach")
    exit()

except Exception as e:
    print("Error encountered. Saving...")

    with open("codes.json", 'w') as f:
        json.dump(codes, f, indent=2)

    with open("owners.json", 'w') as f:
        json.dump(owners, f, indent=2)

    poster.post_comment(f"END (ID: {random.randint(1, 1000)})")
    poster.set_notes("OFFLINE\nCredits to @TimMcCool for scratchattach")

    print(e)

    commons.event.set()
    exit(1)
