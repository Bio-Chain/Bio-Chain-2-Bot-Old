import matrix
from util import *


class Base:
    def __init__(self, user_id, last, current):
        self.user_id = user_id
        self.last = last
        self.current = current

    def __str__(self):
        return '{} {}: {} -> {}'.format(type(self), self.user_id, self.last, self.current)
        

class Username(Base):
    def shout(self, db):
        shouts = []
        if self.current != self.last:
            if not self.current:
                shouts.append(BULLET + '{} has removed their username!'.format(
                    get_html_mention(self.user_id, '@' + self.last)
                ))
            elif not self.last:
                shouts.append(BULLET + '{} is now known as {}!'.format(
                    get_html_mention(self.user_id, self.user_id),
                    db.users[self.user_id].get_mention()
                ))
            elif self.last and self.current:
                shouts.append(BULLET + '@{} has changed their username to @{}!'.format(
                    self.last,
                    self.current
                ))

        for i in range(1, len(db.best_chain)):
            prev_id, this_id = db.best_chain[i-1], db.best_chain[i]
            if this_id == self.user_id and db.matrix.get_link_to(prev_id, this_id) is not matrix.State.REAL:
                shouts.append(BULLET_2 + '{} should update their bio because of this!'.format(
                    db.users[prev_id].get_mention()
                ))
                break

        return '\n'.join(shouts)

    def iter_need_update(self, db):
        return db.matrix.get_links_from(self.user_id)


class Bio(Base):
    def _get_shout_from_list(self, l, prefix):
        return BULLET + prefix + ' remove their unnecessary link{} to <code>{}</code>!'.format(
                's' if len(l) > 1 else '',
                join_with_conjunction(l)
            )


    def shout(self, db):
        shouts = []
        correct_link_id = 0
        for i in range(1, len(db.best_chain)):
            this_id, next_id = db.best_chain[i-1], db.best_chain[i]

            if this_id == self.user_id:
                correct_link_id = next_id

                if db.matrix.get_link_to(this_id, next_id) is matrix.State.REAL:
                    break
                shouts.append(BULLET + '{}\'s bio should have a link to <code>{}</code> but it doesn\'t!'.format(
                    db.users[self.user_id].get_mention(),
                    db.users[next_id]
                ))

                if i < 2:
                    break
                shouts.append(BULLET_2 + '{} might want to link to <code>{}</code> because of this!'.format(
                    db.users[db.best_chain[i - 2]].get_mention(),
                    db.users[next_id]
                ))
                break

        unnecessary_known = []
        unnecessary_unknown = []
        for link_username in self.current:
            link_id = db.translation_table.get(link_username.lower(), None)
            if link_id == correct_link_id or link_id == self.user_id:
                continue

            if link_id:
                unnecessary_known.append(str(db.users[link_id]))
            else:
                unnecessary_unknown.append('@'+link_username)

        username = db.users[self.user_id].get_mention()
        if unnecessary_known:
            shouts.append(self._get_shout_from_list(unnecessary_known, username + " should"))
        if unnecessary_unknown:
            shouts.append(self._get_shout_from_list(unnecessary_unknown, username + " might want to"))

        return '\n'.join(shouts)

    def iter_need_update(self, db):
        return db.matrix.get_links_to(self.user_id)
