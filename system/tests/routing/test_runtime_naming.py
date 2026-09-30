import unittest

from system.routing.runtime_naming import (
    ASSIST_ACTION,
    CANONICAL_BOOTSTRAP_ACTION,
    DELETE_ACTION,
    EDIT_ACTION,
    HELP_ACTION,
    RUN_ACTION,
    classify_bootstrap_invocation,
    classify_prompt_action,
    classify_system_action,
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
            "@do:sot\n@run:ai/recap",
            "@do:sot\n@recap:2",
            "@do:sot\n\nordinary body",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_bootstrap_invocation(text)

    def test_bootstrap_rejects_inline_payloads_for_canonical_and_legacy(self):
        for text in (
            "@do:sot unexpected",
            "@do:initialSoT=value",
            "@do:initialSoT unexpected",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_bootstrap_invocation(text)

    def test_help_and_assist_are_not_bootstrap_invocations(self):
        for text in ("@do:help", "@do:assist"):
            with self.subTest(text=text):
                self.assertIsNone(classify_bootstrap_invocation(text))


class SystemActionTests(unittest.TestCase):
    def test_canonical_sot_resolves_through_system_action(self):
        result = classify_system_action("@do:sot")
        self.assertEqual(CANONICAL_BOOTSTRAP_ACTION, result.action)
        self.assertEqual("", result.body)

    def test_legacy_sot_resolves_with_deprecation_through_system_action(self):
        result = classify_system_action("@do:initialSoT")
        self.assertEqual(CANONICAL_BOOTSTRAP_ACTION, result.action)
        self.assertTrue(result.legacy)
        self.assertIn("@do:sot", result.diagnostic)

    def test_help_with_no_body_is_valid(self):
        result = classify_system_action("@do:help")
        self.assertEqual(HELP_ACTION, result.action)
        self.assertEqual("", result.body)

    def test_help_with_ordinary_body_is_valid(self):
        result = classify_system_action("@do:help\n\nHow do I use a coding Profile with a project?")
        self.assertEqual(HELP_ACTION, result.action)
        self.assertEqual("How do I use a coding Profile with a project?", result.body)

    def test_assist_with_no_body_is_valid(self):
        result = classify_system_action("@do:assist")
        self.assertEqual(ASSIST_ACTION, result.action)
        self.assertEqual("", result.body)

    def test_assist_with_ordinary_body_is_valid(self):
        result = classify_system_action(
            "@do:assist\n\nCreate a reusable Profile for deep professional research with short answers.")
        self.assertEqual(ASSIST_ACTION, result.action)
        self.assertIn("Profile", result.body)

    def test_sot_rejects_body(self):
        with self.assertRaises(ValueError):
            classify_system_action("@do:sot\n\nordinary body")

    def test_help_and_assist_reject_inline_payload_on_action_line(self):
        for text in ("@do:help=value", "@do:help unexpected",
                     "@do:assist=value", "@do:assist unexpected"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_help_and_assist_reject_param_companions(self):
        for text in ("@do:help\n@param:x=[1]", "@do:assist\n@param:x=[1]"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_help_and_assist_reject_selector_and_control_companions(self):
        for text in (
            "@do:help\n@profile:g.coding",
            "@do:assist\n@ctx:personal",
            "@do:help\n@control:learning=on",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_help_and_assist_reject_a_second_high_level_action(self):
        for text in (
            "@do:help\n@do:assist",
            "@do:assist\n@do:sot",
            "@do:help\n@run:ai/recap",
            "@do:assist\n@recap:2",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_unknown_do_action_does_not_normalize(self):
        for text in ("@do:guide", "@do:support", "@do:create", "@do:customize"):
            with self.subTest(text=text):
                self.assertIsNone(classify_system_action(text))

    def test_bare_help_and_assist_do_not_normalize(self):
        for text in ("@help", "@assist"):
            with self.subTest(text=text):
                self.assertIsNone(classify_system_action(text))

    def test_case_variants_do_not_normalize(self):
        for text in ("@do:HELP", "@do:Assist", "@DO:help"):
            with self.subTest(text=text):
                self.assertIsNone(classify_system_action(text))


class PromptActionTests(unittest.TestCase):
    def test_run_resolves_canonical_prompt_identity(self):
        result = classify_prompt_action("@run:ai/context_snapshot")
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("ai/context_snapshot", result.prompt_id)

    def test_edit_resolves_canonical_prompt_identity(self):
        result = classify_prompt_action("@edit:ai/context_snapshot")
        self.assertEqual(EDIT_ACTION, result.keyword)
        self.assertEqual("ai/context_snapshot", result.prompt_id)

    def test_delete_resolves_canonical_prompt_identity(self):
        result = classify_prompt_action("@delete:ai/context_snapshot")
        self.assertEqual(DELETE_ACTION, result.keyword)
        self.assertEqual("ai/context_snapshot", result.prompt_id)

    def test_lowercase_snake_case_nested_path_is_valid(self):
        result = classify_prompt_action("@run:sot/create_project")
        self.assertEqual("sot/create_project", result.prompt_id)

    def test_case_invalid_paths_fail(self):
        for path in ("Ai/Recap", "AI/RECAP", "ai/Recap"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    classify_prompt_action(f"@run:{path}")

    def test_traversal_and_physical_path_syntax_fails(self):
        for path in ("../etc/passwd", "ai/../recap", "workspace/prompts/ai/recap", "workspace"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    classify_prompt_action(f"@run:{path}")

    def test_physical_prefix_is_not_accepted_as_runtime_identity(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@edit:workspace/prompts/ai/recap")

    def test_run_preserves_allowed_parameter_and_selector_composition(self):
        text = "@ctx:personal\n@profile:g.coding\n@run:ai/context_snapshot\n@param:focus=[architecture]"
        result = classify_prompt_action(text)
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("ai/context_snapshot", result.prompt_id)

    def test_edit_preserves_currently_allowed_composition(self):
        text = "@profile:g.coding\n@edit:ai/context_snapshot"
        result = classify_prompt_action(text)
        self.assertEqual("ai/context_snapshot", result.prompt_id)

    def test_delete_resolves_without_requiring_a_second_confirm_directive(self):
        result = classify_prompt_action("@delete:ai/context_snapshot")
        self.assertEqual(DELETE_ACTION, result.keyword)

    def test_old_do_prompt_syntax_is_rejected(self):
        self.assertIsNone(classify_prompt_action("@do:prompt:ai/recap"))

    def test_old_edit_prompt_syntax_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@edit:prompt:ai/recap")

    def test_old_delete_prompt_syntax_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@delete:prompt:ai/recap")

    def test_old_confirm_delete_prompt_syntax_is_rejected(self):
        self.assertIsNone(classify_prompt_action("@confirm:delete:prompt:ai/recap"))

    def test_bare_prompt_remains_unsupported(self):
        self.assertIsNone(classify_prompt_action("@prompt:ai/recap"))


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
