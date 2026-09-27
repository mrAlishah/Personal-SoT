from pathlib import PurePosixPath
import unittest

from system.context.access import permitted
from system.validation.validate_public import contains_raw_secret


class AccessTests(unittest.TestCase):
    def allowed(self, header, **overrides):
        args = dict(path='workspace/context/personal/goals.md',
                    scope_path='workspace/context/personal', host_read=True,
                    required=True, personal_owner=False, private_instance=False)
        args.update(overrides)
        return permitted(header, **args)

    def test_allow_requires_host_scope_and_need(self):
        header = '---\nai_access: allow\n---\n'
        self.assertTrue(self.allowed(header))
        for change in ({'host_read': False}, {'required': False},
                       {'path': 'workspace/context/organizations/other/goals.md'},
                       {'path': 'workspace/context/personal/../other/goals.md'}):
            self.assertFalse(self.allowed(header, **change))

    def test_denied_invalid_and_duplicate_fail_closed(self):
        for header in ('---\nai_access: deny\n---', '',
                       '---\nai_access: unknown\n---',
                       '---\nai_access: deny\nai_access: allow\n---'):
            self.assertFalse(self.allowed(header, personal_owner=True, private_instance=True))

    def test_restricted_requires_trusted_private_personal_owner(self):
        header = '---\nai_access: restricted\n---'
        self.assertFalse(self.allowed(header))
        self.assertFalse(self.allowed(header, personal_owner=True))
        self.assertTrue(self.allowed(header, personal_owner=True, private_instance=True))
        self.assertFalse(self.allowed(header, personal_owner=True, private_instance=True,
                                      path='workspace/context/organizations/acme/goals.md',
                                      scope_path='workspace/context/organizations/acme'))

    def test_validator_owned_secret_check(self):
        self.assertTrue(contains_raw_secret('api_' + 'token: example_value'))
        self.assertFalse(contains_raw_secret('api_' + 'token: external_reference'))


if __name__ == '__main__':
    unittest.main()
