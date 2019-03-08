from libs import command
from libs import dataloader
import time
import re
import asyncio

DELETE = 'delete'
PIN = 'pin'
PIPE = 'pipe'
NOTHING = 'none'

FILTER_ACTIONS = (DELETE, PIN, PIPE, NOTHING)

COLUMNS = {
            'owner': 'TEXT NOT NULL DEFAULT "106537989684887552"',
            'server': 'TEXT NOT NULL DEFAULT "381172950448996363"',
            'channels': 'TEXT NOT NULL DEFAULT "000000000000000000"',
            'regex': 'TEXT NOT NULL DEFAULT "."',
            'created': 'REAL NOT NULL DEFAULT %s' % time.time(),
            'active': 'INTEGER NOT NULL DEFAULT 1',
            'action': 'TEXT NOT NULL DEFAULT "none"',
            'param': 'TEXT',
            'public': 'INTEGER NOT NULL DEFAULT 0',
            'featured': 'INTEGER NOT NULL DEFAULT 0'
            }

class Command(command.Config, command.AdminCommand):
    '''Filters messages sent in a channel

**Usage**
Create a filter
```@Idea create filter <name> match <regex> action <action> [<parameters>] ```
Where
**`<name>`** is the name of the filter you want to create
**`<regex>`** is the regular expression to match (replace spaces with `\\s`)
**`<action>`** is the action to perform when <regex> matches
**`<parameters>`** is the parameters for the action, if applicable

**NOTE:** `[thing]` means `thing` is optional

For more info on creating filters, do
```@Idea help filter_add ```

Delete a filter
```@idea delete filter <name>```
Where
**`<name>`** is the name of the filter you want to remove

For more info on deleting filters, do
```@Idea help filter_remove ```
'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.public_namespace.database = self.public_namespace.db = dataloader.datafile(self.config['database'])
        # set up db if not already setup
        self.public_namespace.db.execute('CREATE TABLE IF NOT EXISTS filters (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)')
        # create columns if not exist
        self.public_namespace.db.patch('filters', COLUMNS, commit=True)
        # set up constants
        self.public_namespace.DELETE = DELETE
        self.public_namespace.PIN = PIN
        self.public_namespace.PIPE = PIPE
        self.public_namespace.NOTHING = NOTHING
        self.public_namespace.FILTER_ACTIONS = FILTER_ACTIONS

    def matches(self, message):
        return self.find_match(message) is not None and message.server.me != message.author

    @asyncio.coroutine
    def action(self, message, bot):
        match_id = self.find_match(message)
        self.public_namespace.db.execute('SELECT action, param FROM filters WHERE id=?', (match_id,))
        match_row = self.public_namespace.db.cursor.fetchone()
        if match_row['action'] == DELETE:
            yield from self.do_delete_action(message, match_row['param'], bot)
        elif match_row['action'] == PIN:
            yield from self.do_pin_action(message, match_row['param'], bot)
        elif match_row['action'] == PIPE:
            yield from self.do_pipe_action(message, match_row['param'], bot)
        elif match_row['action'] == NOTHING:
            pass
        else:
            raise ValueError('Invalid Action Value for %s' % match_id)

    def find_match(self, message):
        if message.server is None:
            return
        self.public_namespace.db.execute('SELECT regex, id FROM filters WHERE server=? AND channels LIKE ? AND active=1', (message.server.id, '%'+message.channel.id+'%'))
        for row in self.public_namespace.db.cursor.fetchall():
            if re.search(row['regex'], message.content, re.I) is not None:
                return row['id']

    def do_delete_action(self, message, param, bot):
        yield from bot.delete_message(message)

    def do_pin_action(self, message, param, bot):
        yield from bot.pin_message(message)

    def do_pipe_action(self, message, param, bot):
        msg_content = '%s %s >> %s' % (bot.user.mention, message.content, param)
        pipe_msg = yield from self.send_message(message.channel, msg_content)
        yield from bot.delete_message(pipe_msg)

    def shutdown(self):
        self.public_namespace.database.save()
