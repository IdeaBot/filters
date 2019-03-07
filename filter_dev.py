from libs import command
import re

class Command(command.DirectOnlyCommand, command.AdminCommand):
    '''Revive/Feature/Publish a filter (devs only)
You probably don't have permission to use this command.

**Usage**
```@Idea feature/publish/revive filter <name>```
Where
**`<name>`** is the filter to apply the action to '''
    def collect_args(self, message):
        return re.search(r'\b(feature|publish|revive)\s*filter\s*(\S+)', message.content, re.I)

    def matches(self, message):
        return self.collect_args(message) is not None

    def action(self, message, bot):
        if message.author.id not in bot.ADMINS:
            yield from self.send_message(message.channel, 'You do not have permissions to use this dev-only command')
            return
        args = self.collect_args(message)
        self.public_namespace.db.execute('SELECT active, public, featured FROM filters WHERE name=?', (args.group(2), ))
        rows = self.public_namespace.db.cursor.fetchall()
        if len(rows) == 0:
            yield from self.send_message(message.channel, 'Unable to find filter `%s`' % args.group(2))
            return
        activity = args.group(1).lower()
        if activity == 'revive':
            self.public_namespace.db.execute('UPDATE filters SET active=1 WHERE name=?', (args.group(2), ))
            yield from self.send_message(message.channel, '`%s` was revived' % args.group(2))
        else:
            if rows[0]['active'] == 0:
                yield from self.send_message(message.channel, '!!Modifying inactive filter!!')
            if activity == 'publish':
                self.public_namespace.db.execute('UPDATE filters SET public=? WHERE name=?', (int(not rows[0]['public']), args.group(2)))
                yield from self.send_message(message.channel, '`%s` public was toggled to %s' % (args.group(2), not rows[0]['public']))
            if activity == 'feature':
                self.public_namespace.db.execute('UPDATE filters SET featured=? WHERE name=?', (int(not rows[0]['featured']), args.group(2)))
                yield from self.send_message(message.channel, '`%s` featured was toggled to %s' % (args.group(2), not rows[0]['featured']))
        self.public_namespace.db.save()
