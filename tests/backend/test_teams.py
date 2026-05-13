import os
import pytest
from unittest.mock import patch, MagicMock

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

from backend.services.teams import (
    create_org, get_user_orgs, get_org_members,
    create_team, get_org_teams, invite_member,
    remove_member, is_org_owner_or_admin,
)


class MockDB:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        obj.id = 1

    def query(self, model):
        return MockQuery()


class MockQuery:
    def filter(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return None

    def all(self):
        return []

    def count(self):
        return 0

    def delete(self, *args, **kwargs):
        return None

    def order_by(self, *args):
        return self

    def limit(self, *args):
        return self

    def offset(self, *args):
        return self


def test_is_org_owner_or_admin_no_membership():
    db = MockDB()
    result = is_org_owner_or_admin(db, 1, 1)
    assert result is False
