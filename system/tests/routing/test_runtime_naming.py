import unittest

from system.routing.runtime_naming import (
    CANONICAL_BOOTSTRAP_ACTION,
    classify_bootstrap_invocation,
    is_profile_identity,
    profile_identity_kind,
)


class BootstrapNamingTests(unittest.TestCase):
    def test_canonical_bootstrap_is_exact_and_parameterless(self):
        result = classify_bootstrap_invocation("@do:sot")

        self.assertEqual(result.action, CANONICAL_BOOTSTRAP_ACTION)
        self.assertFalse(result.legacy)
        self.assertIsNone(result.diagnostic)

    def test_legacy_bootstrap_resolves_with_deprecation_signal(self):
        result = classify_bootstrap_invocation("@do:initialSoT")

        self.assertEqual(result.action, CANONICAL_BOOTSTRAP_ACTION)
        self.assertTrue(result.legacy)
        self.assertIn("deprecated", result.diagnostic.lower())
        self.assertIn("@do:sot", result.diagnostic)

    def test_unknown_aliases_and_case_variants_do_not_resolve(self):
        for text in ("@sot", "@init", "@load", "@bootstrap", "@do:SOT"):
            with self.subTest(text=text):
                self.assertIsNone(classify_bootstrap_invocation(text))

    def test_bootstrap_rejects_parameters_companions_and_body(self):
        for text in (
            "@do:sot=value",
            "@do:sot\n@param:name=[value]",
            "@do:sot\n@do:prompt:ai/recap",
            "@do:sot\n@recap:2",
            "@do:sot\n\nordinary body",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_bootstrap_invocation(text)


class ProfileIdentityTests(unittest.TestCase):
    def test_custom_profile_keeps_lowercase_snake_case(self):
        for identity in ("coding", "my_profile", "profile2"):
            with self.subTest(identity=identity):
                self.assertEqual(profile_identity_kind(identity), "custom")
                self.assertTrue(is_profile_identity(identity))

    def test_built_in_profile_accepts_hierarchical_segments(self):
        for identity in (
            "g.coding",
            "g.architecture.review",
            "g.problem.solving",
            "g.technical.learning",
        ):
            with self.subTest(identity=identity):
                self.assertEqual(profile_identity_kind(identity), "built_in")
                self.assertTrue(is_profile_identity(identity))

    def test_invalid_built_in_forms_are_rejected(self):
        for identity in (
            "g.architecture_review",
            "g.problem_solving",
            "G.Architecture.Review",
            "g..review",
            "g.",
        ):
            with self.subTest(identity=identity):
                self.assertIsNone(profile_identity_kind(identity))
                self.assertFalse(is_profile_identity(identity))


if __name__ == "__main__":
    unittest.main()
