import os
import traceback
import datetime
from telegram.ext import Updater, MessageHandler, Filters
from signal import signal, SIGINT, SIGTERM, SIGABRT
import logging

from database import Database
import commands
from util import *

DATABASE_FILENAME = 'db.json'
LAST_CHAIN = FileString('last_chain.txt')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def update_chain(bot, chain_text):
    """
    Tries to post chain_text (editing the last message if possible)
    Returns True if chain_text was sent, False if not
    """
    if chain_text == LAST_CHAIN.get():
        return False

    if len(chain_text) >= 3000:
        send_message(bot, '@KateWasTaken Warning: The chain is approaching message character limit ({:.1%})'.format(
            len(chain_text) / 4096
        ))

    try:
        # try to edit our last pinned message
        bot.editMessageText(
            chat_id=CHAT_ID,
            message_id=LAST_PIN.get(),
            text=chain_text
        )
    except:
        # can't edit? send a placeholder and then edit it to prevent notifications
        message = send_message(bot, 'the game')
        if message:
            bot.editMessageText(
                chat_id=CHAT_ID,
                message_id=message.message_id,
                text=chain_text
            )
            bot.pinChatMessage(
                chat_id=CHAT_ID,
                message_id=message.message_id,
                disable_notification=True
            )

            LAST_PIN.set(message.message_id)

    LAST_CHAIN.set(chain_text)

    return True


def send_message(bot, text, chat_id=CHAT_ID, *args, **kwargs):
    """Prints a message and then sends it via the bot to the chat"""
    if not text:
        return
        
    print('out:', text)

    return bot.sendMessage(
        chat_id=chat_id,
        text=text,
        parse_mode='HTML',
        *args,
        **kwargs
    )


def send_message_pre(bot, text, chat_id=CHAT_ID):
    return send_message(bot, '<pre>{}</pre>'.format(html_escape(text)), chat_id)


def get_update_users(update):
    """Yields the new user IDs and usernames associated with an update in the chat"""
    if update.message and update.message.chat.id == CHAT_ID:
        for user in update.message.new_chat_members:
            if not user.is_bot:
                yield str(user.id), user.username or ''
        user = update.message.from_user
        if not user.is_bot:
            yield str(user.id), user.username or ''


def handle_update_command(db, update):
    if not update.message:
        return False

    message = update.message

    if message.forward_from or not message.text or not message.text.startswith('/'):
        return False

    command_split = message.text[1:].split(' ', 1)
    command_args = command_split[1:] or ''

    directed = False
    command = command_split[0].lower().split('@')
    if command[1:]:
        # the command was directed to a bot
        directed = True
    command.append(message.bot.username)
    if command[1] != message.bot.username:
        # this command is not for us
        return False

    try:
        getattr(commands, 'cmd_' + command[0])(db, update, directed, command_args)
    except AttributeError:
        if directed:
            print('got unknown command:', message.text)

    return True


def on_error(bot, update, error):
    send_message_pre(bot, error + '\n\n' + update, 232787997)
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    def on_signal(signum, frame):
        if updater.running:
            updater.stop()
        else:
            exit(1)


    def on_command(bot, update):
        message = update.message

        command_split = message.text[1:].split(' ', 1)
        command_args = command_split[1:] or ''

        command = command_split[0].lower().split('@')
        directed = bool(command[1:])
        command.append(bot.username)
        if command[1].lower() != bot.username.lower():
            # this command is not for us
            return

        try:
            getattr(commands, 'cmd_' + command[0].lower())(db, update, directed, command_args)
        except AttributeError:
            if directed:
                print('got unknown command:', message.text)


    def on_new_members(bot, update):
        for user in update.message.new_chat_members:
            if user.is_bot:
                continue
            if not db.add_user(str(user.id), user.username or ''):
                continue
            if (datetime.datetime.now() - update.message.date).total_seconds() > 60:
                continue

            send_message(
                bot, 
                (
                    'Welcome, {}!\n'
                    '<a href="https://t.me/GBReborn_bot?start=-1001145055784_rules">Read the rules</a>\n\n'
                    'Who did you start at?\n\n'
                    '(to join the chain, simply add <code>{}</code> to your bio)'
                ).format(
                    get_html_mention(user.id, user.username or user.first_name),
                    db.users[db.get_head_user_id()]
                ),
                reply_to_message_id=update.message.message_id
            )


    def on_left_member(bot, update):
        left_id = str(update.message.left_chat_member.id)
        if left_id in db.users:
            db.users[left_id].username_fetch_failed = True

    db = Database(DATABASE_FILENAME)
    db.update_best_chain(END_NODE)
    
    updater = Updater(token=TOKEN)
    bot = updater.bot
    updater.dispatcher.add_handler(
        MessageHandler(Filters.chat(CHAT_ID) & Filters.command & (~Filters.forwarded), on_command)
    )
    updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, on_new_members))
    updater.dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, on_left_member))
    updater.dispatcher.add_error_handler(on_error)
    updater.start_polling()

    for sig in (SIGINT, SIGTERM, SIGABRT):
        signal(sig, on_signal)

    pending_changes = []
    while updater.running:
        try:
            # try to update the user who expires next
            changes, user_was_updated = db.update_first_expired(bot)
            if not user_was_updated:
                time.sleep(1)

            pending_changes.extend(changes)

            if db.get_expired_count() > 0 or not pending_changes:
                continue

            # rebuild the best chain
            last_head = db.get_head_user_id()
            db.update_best_chain(END_NODE)

            # post the best chain if it's different to the old one
            update_chain(bot, db.stringify_chain(db.best_chain))

            # shout at branches if the head has changed
            if db.get_head_user_id() != last_head:
                send_message(bot, db.get_branch_announcements())

            # shout at users whose data has changed
            for pending_change in pending_changes:
                send_message(bot, pending_change.shout(db))
            pending_changes.clear()

            # disable users who we failed to fetch a username for and aren't in the chain
            for user_id in db.users:
                if not db.users[user_id].username_fetch_failed:
                    continue
                print('rechecking', db.users[user_id].str_with_id())
                if user_id not in db.best_chain:
                    db.disable_user(user_id)

            # Get rid of old non-existent links if the chain passes through only real links
            if db.best_chain_is_valid:
                print('Purged {} dead links'.format(db.clear_dead_links()))
            db.save()
        except Exception as e:
            #raise e
            print('Encountered exception while running main loop:', type(e))
            send_message_pre(bot, traceback.format_exc(), 232787997)


if __name__ == '__main__':
    main()
