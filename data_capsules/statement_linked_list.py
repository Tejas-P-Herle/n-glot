"""Stores statements as list and implements methods for easy navigation and
tagging"""


from dataclasses import dataclass, field
from typing import Any


class StatementLinkedList(dict):
    def __init__(self, stmts, upper=None, start_stmt=None):
        self.upper = upper
        if start_stmt is None:
            stmts = iter(stmts)
            start_stmt = next(stmts)
        self.start_stmt = start_stmt
        self.level = start_stmt.level
        self.last_stmt = self.curr_node = None
        self.top_end = self.bottom_end = None
        super().__init__()
        self.build_dict(stmts)

    def __str__(self):
        """Override __str__ method to avoid recursive list creations"""

        str_builder_dict = {k: v if v is None else "..."
                            for k, v in self.items()}
        return str(str_builder_dict)

    def build_dict(self, stmts):
        """Build statements dictionary"""

        self.top_end = self.curr_node = StatementLLNode(
            self.start_stmt, self, self.upper, None)
        for next_stmt in stmts:
            level_inc = next_stmt.level > self.level
            if level_inc:
                stmt_ll = StatementLinkedList(
                    stmts, upper=self, start_stmt=next_stmt)
                self.curr_node.next_ = stmt_ll.top_end
                next_stmt = stmt_ll.last_stmt
                if next_stmt is None:
                    break

            if next_stmt.level < self.level:
                self.last_stmt = next_stmt
                break

            self.link_node(next_stmt, self.curr_node, level_inc)

        self.bottom_end = self[self.curr_node.stmt] = self.curr_node

    def link_node(self, next_stmt, prev_node, level_inc=False):
        """Link current node with next and previous nodes"""

        next_node = StatementLLNode(next_stmt, self, prev_node, self.curr_node)
        self.curr_node.next_lvl = next_node
        if not level_inc:
            self.curr_node.next_ = next_node

        self[self.curr_node.stmt] = self.curr_node
        self.curr_node = next_node

    def iterate(self, start=None, same_lvl=False, all_=True):
        """Yield statements based on params"""

        if same_lvl:
            for node in self.level_iter(start):
                if all_ or not node.stmt.is_transition_stmt:
                    yield node
        else:
            for node in self.df_iter(all_):
                yield node

    def level_iter(self, start=None):
        """Iterate over statements in same level"""

        stmt_node = self.top_end if start is None else self[start].next_lvl
        while stmt_node is not None:
            yield stmt_node
            stmt_node = stmt_node.next_lvl

    def df_iter(self, include_trans_stmts=True):
        """Depth First Iterator, returns all stmts irrespective of level"""

        for node in self.values():
            yield node
            if node.next_ != node.next_lvl:
                for stmt in node.next_.stmt_ll.df_iter(include_trans_stmts):
                    yield stmt

    def get_next_stmt(self, stmt, same_level=False, include_trans_stmts=True):
        """Get next statement"""

        next_node = self[stmt].next_lvl if same_level else self[stmt].next_
        if next_node is None:
            return next_node

        if include_trans_stmts or not next_node.stmt.is_transition_stmt:
            return next_node
        return next_node.next_lvl if same_level else next_node.next_


@dataclass
class StatementLLNode:
    stmt: Any
    stmt_ll: StatementLinkedList = field(repr=False)
    prev: Any = field(repr=False)
    prev_lvl: Any = field(repr=False)
    next_: Any = field(default=None, repr=False)
    next_lvl: Any = field(default=None, repr=False)

    def __next__(self):
        """Implement next method"""

        return self.next_

    def get_next(self, same_lvl=False, all_=True):
        """Return next member in node"""

        next_ = self.next_lvl if same_lvl else self.next_

        # TODO: Consider removing all_ kw
        # If not all_, ie. don't include new line and INDENT stmts,
        # then skip one and get the next statement
        if not all_ and next_.stmt.is_transition_stmt:
            next_ = next_.next_lvl if same_lvl else next_.next_
        return next_

    def get_prev(self, same_lvl=False, all_=True):
        """Return prev member in node"""

        prev = self.prev_lvl if same_lvl else self.prev
        if not all_ and prev.stmt.is_transition_stmt:
            prev = prev.prev_lvl if same_lvl else prev.prev
        return prev
