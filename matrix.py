from enum import Enum

from collections import defaultdict


class State(Enum):
    """
    State of a link:
    DEAD: The link has existed in the past but does not exist right now
    NONE: There's no link here
    REAL: The link exists right now
    """
    DEAD = -1
    NONE = 0
    REAL = 1


class LinkMatrix:
    """Wrapper for two matricies that represent forward and backwards connections in a graph"""
    def __init__(self):
        self.links_to = self.__new_empty()
        self.links_from = self.__new_empty()

    def __new_empty(self):
        return defaultdict(
            lambda: defaultdict(
                lambda: State.NONE
            )
        )

    def replace(self, state, new_state):
        count = 0
        for linker in self.links_to:
            for linked in self.links_to[linker]:
                if self.links_to[linker][linked] is state:
                    self.set_link_to(linker, linked, new_state)
                    count += 1
        return count

    def set_link_to(self, linker, linked, state):
        self.links_to[linker][linked] = state
        self.links_from[linked][linker] = state

    def set_link_from(self, linked, linker, state):
        self.links_from[linked][linker] = state
        self.links_to[linker][linked] = state

    def get_link_to(self, linker, linked):
        return self.links_to[linker][linked]

    def get_link_from(self, linked, linker):
        return self.links_from[linked][linker]

    def get_links_to(self, linker, filter=lambda l: l is not State.NONE):
        """yields nodes that the linker links to that match filter"""
        for linked in self.links_to[linker]:
            if filter(self.links_to[linker][linked]):
                yield linked

    def get_links_from(self, linked, filter=lambda l: l is not State.NONE):
        """yields nodes that linked is linked from that match filter"""
        for linker in self.links_from[linked]:
            if filter(self.links_from[linked][linker]):
                yield linker


    def has_link_like(self, linker, state=State.REAL):
        """Returns True if linker has a link that is the same as state"""
        for linked in self.links_to[linker]:
            if self.links_to[linker][linked] is state:
                return True
        return False

    def get_chains_ending_on(self, end_node):
        """
        Returns a list of chains (if any) that end on end_node
        """
        found_chains = []

        pending_chains = [[end_node]]

        while pending_chains:
            # grab a chain from the stack
            this_chain = pending_chains.pop()
            last_link = this_chain[-1]
            is_end = True

            # iterate through all the links lead to here
            for next_link in self.get_links_from(last_link):
                # skip link if we have visited it before
                if next_link in this_chain:
                    continue

                # since we can reach a node then this is not the end
                is_end = False
                # add [this_chain + next_link] to pending_chains
                new_chain = this_chain[:]
                new_chain.append(next_link)
                pending_chains.append(new_chain)

            # if last_link doesn't go anywhere, then add it to our found chains
            if is_end:
                found_chains.append(this_chain[::-1])

        return found_chains

    def chain_all_links_equal(self, chain, state=State.REAL):
        """Returns true if all links in chain are equal to state"""
        for i in range(1, len(chain)):
            this_node, next_node = chain[i-1], chain[i]
            if self.links_to[this_node][next_node] is not state:
                return False

        return True

    def chain_tally(self, chain):
        count = defaultdict(int)

        for i in range(1, len(chain)):
            this_node, next_node = chain[i-1], chain[i]
            count[self.links_to[this_node][next_node]] += 1

        return count

    def chain_get_merge_points(self, chain1, chain2):
        """Finds the index of the nodes just before the merge of two chains"""
        i1 = len(chain1)-1
        i2 = len(chain2)-1

        while chain1[i1] == chain2[i2] and (i1 > 0 or i2 > 0):
            i1 = max(i1 - 1, 0)
            i2 = max(i2 - 1, 0)

        return i1, i2


if __name__ == '__main__':
    matrix = LinkMatrix()

    matrix.set_link_to('A', 'B', State.REAL)
    assert matrix.get_link_from('B', 'A') == State.REAL
    assert matrix.get_link_from('B', 'A') == matrix.get_link_to('A', 'B')

    matrix.set_link_to('A', 'C', State.REAL)
    matrix.set_link_to('B', 'C', State.REAL)
    matrix.set_link_to('C', 'D', State.REAL)
    matrix.set_link_to('Q', 'D', State.REAL)
    # A -> B -> C -> D
    #  \_______/

    chains = matrix.get_chains_ending_on('D')

    print(chains)
    print(matrix.chain_get_merge_points(chains[0], chains[1]))

    print(matrix.chain_tally(chains[0]))
