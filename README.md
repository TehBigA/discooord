# discooord
Discord API for creating bots.

**This project is still in its infancy and may contain bugs or not fully implement the [Discord API](https://discordapp.com/developers/docs/intro).**

This is a symptom of starting this for a gaming community and as a learning experience (so implementation has mostly been as needed). Also I didn't like the existing libraries I came across. Now that I'm putting this up here I hope it motivates me to really polish this off.

## Requirements
- requests
- websocket-client

## Blatantly missing
- Proper packaging with setup.py (Will try to do this for the next commit - **for now just put this code in with your python 2.7 packages**)
- Python 3.x support
- Voice Connections

## Important but only partially implemented
- Data caching (available guilds, channels, and users)
- Connection loss recovery (Recently "fixed" - we'll see how that goes)
 - Reconnect OP code not implemented yet
- Command manager

## Important but not started
- Centralized configuration
- Automated sharding support

## Example usage
```python
import re

from .client import Client
from .extras.command import CommandManager, Command


TOKEN = 'YOUR TOKEN HERE'  # Goto https://discordapp.com/login?redirect_to=/developers/applications/me to setup your bot account

client = Client(token=TOKEN)
manager = CommandManager(client)


DICE_ROLL_REGEX = re.compile(r'^(\d+) ?d ?(\d+)(?: ?([+-]) ?(\d+))?$')


@manager.register
class Roll(Command):
    description = 'Roll dice just like in the real world, but with less randomness (ie. 1d20+4).'

    def target(self, payload, raw, *args):
        m = DICE_ROLL_REGEX.match(raw)

        if m is None:
            self.client.messages.put(payload.channel_id, "<@!{}> You want me to roll what?".format(payload.author.id))
            return

        count = int(m.group(1))
        sides = int(m.group(2))
        modifier_sign = m.group(3)
        modifier_magnitude = m.group(4)

        if sides <= 0 or sides > 100:
            self.client.messages.put(payload.channel_id, "<@!{}>... I'm not rolling that size of a die. :expressionless:".format(payload.author.id))
            return

        if count <= 0 or count > 100:
            self.client.messages.put(payload.channel_id, "<@!{}>... I'm not rolling that many dice. :expressionless:".format(payload.author.id))
            return

        results = []
        for x in xrange(count):
            results.append(randint(1, sides))

        final = sum(results)
        if modifier_sign and modifier_magnitude:
            modifier_magnitude = int(modifier_magnitude)

            if modifier_sign == '+':
                final = final + modifier_magnitude
            elif modifier_sign == '-':
                final = final - modifier_magnitude

        if len(results) > 1:
            last = results.pop()
            self.client.messages.put(payload.channel_id, '<@!{}> I rolled *{}* and *{}*{}  to get ***{}***.'.format(
                payload.author.id,
                ', '.join([str(r) for r in results]),
                last,
                '' if not modifier_magnitude else ' *{} {}*'.format('plus' if modifier_sign == '+' else 'minus', modifier_magnitude),
                final
            ))
        else:
            self.client.messages.put(payload.channel_id, '<@!{}> I rolled *{}*{}  to get ***{}***.'.format(
                payload.author.id,
                results[0],
                '' if not modifier_magnitude else ' *{} {}*'.format('plus' if modifier_sign == '+' else 'minus', modifier_magnitude),
                final
            ))

with client:
    client.run()
```
