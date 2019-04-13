# Poll Maubot
A bot for [maubot](https://github.com/maubot/maubot) that creates a poll in a riot room and allows users to vote

## Usage
'!poll new  "Question" "Choice1" "Choice2" "Choice3"' - Creates a new poll with given choices. The number of choices must be >1, but has no maximum limit.
'!poll vote choice' - Has user vote for given choice (int). Users can only vote once per poll
'!poll results' - Displays the results from the poll
'!poll close' - Ends the poll


## TODO
- Add user configuration to only allow certain users to create polls
- Add auto-timing ability
