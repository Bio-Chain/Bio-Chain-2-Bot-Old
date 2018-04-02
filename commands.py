from util import *


def cmd_help(db, update, directed, command_args):
    """/help - shows this message"""
    if not directed:
        return

    update.message.reply_text(help_text, parse_mode='Markdown')


def cmd_pin(db, update, directed, command_args):
    """/pin - quotes the current pin message"""
    if update.message.chat.id != CHAT_ID:
        update.message.reply_text('Sorry, I can only do that in the official group')
        return

    update.message.reply_text('^', reply_to_message_id=LAST_PIN.get())


help_text = []
for name, attr in locals().copy().items():
    if callable(attr) and name.startswith('cmd_'):
        doc = attr.__doc__
        if doc:
            help_text.append(doc)
        else:
            help_text.append('/{} - no help available'.format(
                attr[4:],
            ))
help_text = '\n'.join(help_text)
