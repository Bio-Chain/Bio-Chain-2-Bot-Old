import changes
import html
import requests
import re
from util import *
import telegram


RE_SCRAPE_BIO = re.compile(r'<meta +property="og:description" +content="(.+?)".*>')
RE_USERNAME = re.compile(r'@([a-zA-Z][\w\d]{4,31})')


class User:
    defaults = {
        'bio': [],
        'joined': None,
        'expires': 0,
        'disabled': False,
    }

    def __init__(self, user_id, data):
        self.id = user_id
        self.username = data['username']
        self.username_fetch_failed = False

        for key, default_val in self.defaults.items():
            setattr(self, key, data.get(key, default_val))

    def __str__(self):
        #todo: handle blank username better
        return '@' + self.username if self.username else "id:" + self.id

    def get_mention(self):
        return get_html_mention(self.id, str(self))

    def str_with_id(self):
        return self.__str__() + " [" + self.id + "]" if self.username else str(self)

    def is_expired(self):
        return self.expires < get_current_timestamp()

    def reset_expiry(self):
        self.expires = get_current_timestamp() + 60
        return True

    def to_dict(self):
        result = {'username': self.username}
        for key, default_val in self.defaults.items():
            current_val = getattr(self, key)
            if current_val != default_val:
                result[key] = current_val
        return result

    def update_username(self, bot):
        pending_changes = []

        try:
            member = bot.getChatMember(CHAT_ID, self.id)
            new_username = member.user.username or ''
            if not new_username and member.status.lower() in ['left', 'kicked']:
                raise RuntimeError('user left/kicked, no username available')
            if new_username != self.username:
                if new_username.lower() != self.username.lower():
                    pending_changes.append(changes.Username(self.id, self.username, new_username))
                self.username = new_username
        except telegram.error.TimedOut:
            print('  Timed out fetching username')
        except Exception as e:
            self.username_fetch_failed = True
            print('  Failed to fetch username', type(e), e)

        return pending_changes

    def update_bio(self):
        if self.username:
            r = requests.get("http://t.me/" + self.username)
            if not r.ok:
                print("  Request for bio failed (" + r.status_code + ")")
                return []

            bio = RE_SCRAPE_BIO.findall(r.text)
            if not bio:
                print('  Failed to scrape bio tag')
                return []
        else:
            print('  Tried to scrape blank username')
            bio = ['']

        new_bio = {}
        #TODO
        #for bio_username in RE_USERNAME.findall(html.unescape(bio[0])):
        for bio_username in RE_USERNAME.findall(bio[0]):
            if bio_username.lower() == self.username.lower():
                continue
            new_bio[bio_username.lower()] = bio_username

        pending_changes = []
        new_bio = [v for k, v in new_bio.items()]
        if not caseless_set_eq(new_bio, self.bio):
            pending_changes.append(changes.Bio(self.id, self.bio, new_bio))
            self.bio = new_bio

        return pending_changes

    def try_update(self, bot):
        pending_changes = []
        pending_changes.extend(self.update_username(bot))
        pending_changes.extend(self.update_bio())
        self.reset_expiry()
        return pending_changes


if __name__ == '__main__':
    user = User(420, {'username': 'test_user'})
    assert user.id == 420
    assert user.username == 'test_user'
    assert user.is_expired() == True
    user.reset_expiry()
    assert user.is_expired() == False

    print(user)
    user = User(69, {'username': ''})
    print(user)
