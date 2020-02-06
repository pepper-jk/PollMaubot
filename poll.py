import re
import random
from typing import List, Tuple
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from mautrix.types import (EventType, ReactionEvent)
from maubot import Plugin, MessageEvent
from maubot.handlers import command


QUOTES_REGEX = r"\"?\s*?\""  # Regex to split string between quotes
# [Thumbs Up, Thumbs Down, Grinning, Ghost, Robot, Okay Hand, Clapping Hands, Hundred]
            # thumbs up (y), OK (yellow), smiley (y), ghost (white)
REACTIONS = ["\U0001F44D", "\U0001F44C", "\U0001F600", "\U0001F47B",
            # facepalm (grey, y), zebra (bw), pig (pink), t-rex (green)
             "\U0001F926", "\U0001F993", "\U0001F437", "\U0001F996",
            # rainbow, molester moon (dark), guitar (red), monkey (brown)
             "\U0001F308", "\U0001F31A", "\U0001F3B8", "\U0001F648",
            # whale (blue), cookie (bb), lolipop, horns (purple)
             "\U0001F433", "\U0001F36A", "\U0001F36D", "\U0001F608",
            # yarn (orange), :O (y,blue), goblin (red), alien (grey)
             "\U0001F9F6", "\U0001F631", "\U0001F47A", "\U0001F47D",
            # robot (blue), thumbs down (y), clapping (y), 100 (red)
             "\U0001F916", "\U0001F44E", "\U0001F44F", "\U0001F4AF"]

class Poll:
    def __init__(self, question, choices):
        self.question = question
        self.choices = choices
        self.votes = [0] * len(choices)  # initialize all votes to zero
        self.voters = []
        self.active = True  # Begins the poll
        self.total = 0

        self.emojis = REACTIONS[0:len(choices)] # Select a random assortment of emojis

    def vote(self, choice, user_id):
        # Adds a vote to the given choice
        self.votes[choice] += 1
        # Adds user to list of users who have already voted
        self.voters.append(user_id)
        self.total += 1

    def isAvailable(self, choice):
        # Checks if given choice is an option
        return choice <= len(self.choices)

    def hasVoted(self, user):
        # Checks if user has already voted
        return user in self.voters

    def isActive(self):
        # Checks if the poll is currently active
        return self.active

    def get_results(self):
        # Formats the results with percentages
        results = "<br />".join(
            [
                f"<tr><td>{choice}:</td> <td> {self.votes[i]}</td><td> {round(self.votes[i]/self.total if self.total else 0,3) * 100}%</td></tr>"
                for i, choice in enumerate(self.choices)
            ]
        )
        results = f"{self.question}: <br /> <table>" + results + "</table>"
        return results

    def close_poll(self):
        self.active = False


class PollPlugin(Plugin):
    currentPolls = {}

    @command.new("poll", help="Make a poll")
    async def poll(self) -> None:
        pass

    @poll.subcommand("new", help='Creates a new poll with "Question" "choice" "choice" "choice" ...')
    @command.argument(
        "poll_setup",
        pass_raw=True,
        required=True
    )

    async def handler(self, evt: MessageEvent, poll_setup: str) -> None:
        await evt.mark_read()
        r = re.compile(QUOTES_REGEX)  # Compiles regex for quotes
        setup = [
            s for s in r.split(poll_setup) if s != ""
        ]  # Split string between quotes
        question = setup[0]
        choices = setup[1 : len(setup)]
        if len(choices) <= 1:
            response = "You need to enter at least 2 choices."
        else:
            self.currentPolls[evt.room_id] = Poll(question, choices)
            # Show users active poll
            choice_list = "<br />".join(
                [f"{self.currentPolls[evt.room_id].emojis[i]} - {choice}" for i, choice in enumerate(choices)]
            )
            response = f"{question}<br />{choice_list}"
        self.currentPolls[evt.room_id].event_id = await evt.reply(response, allow_html=True)

    @poll.subcommand("results", help="Prints out the current results of the poll")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        if evt.room_id in self.currentPolls:
            await evt.reply(self.currentPolls[evt.room_id].get_results(), allow_html=True)
        else:
            await evt.reply("There is no active poll in this room", allow_html=True)

    @poll.subcommand("close", help="Ends the poll")
    async def handler(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        if evt.room_id in self.currentPolls:
            self.currentPolls[evt.room_id].close_poll()
            await evt.reply("This poll is now over. Type !poll results to see the results.")
        else:
            await evt.reply("There is no active poll in this room")

    @command.passive(regex=r"(?:("+'|'.join(REACTIONS) + r")[\U0001F3FB-\U0001F3FF]?)",
                     field=lambda evt: evt.content.relates_to.key,
                     event_type=EventType.REACTION, msgtypes=None)
    async def get_react_vote(self, evt: ReactionEvent, _: Tuple[str]) -> None:
        if (evt.content.relates_to.event_id == self.currentPolls[evt.room_id].event_id): # Is this on the correct message?
            if not self.currentPolls[evt.room_id].hasVoted(evt.sender): # has the user already voted?
                if (evt.content.relates_to.key in self.currentPolls[evt.room_id].emojis): # Is this a possible choice?
                    self.currentPolls[evt.room_id].vote(self.currentPolls[evt.room_id].emojis.index(evt.content.relates_to.key), evt.sender) # Add vote/sender to poll
