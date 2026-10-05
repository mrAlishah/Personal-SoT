import unittest

from system.routing.runtime_naming import (
    ASSIST_ACTION,
    CANONICAL_BOOTSTRAP_ACTION,
    DELETE_ACTION,
    DOCTOR_ACTION,
    EDIT_ACTION,
    FIX_ACTION,
    HELP_ACTION,
    RUN_ACTION,
    SETUP_ACTION,
    classify_bootstrap_invocation,
    classify_prompt_action,
    classify_system_action,
    is_profile_identity,
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
            "@run:ai/recap\n@do:setup",
            "@do:doctor\n@run:ai/recap",
            "@run:ai/recap\n@do:fix",
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

    def test_non_bootstrap_system_actions_are_not_bootstrap_invocations(self):
        for text in ("@do:help", "@do:assist", "@do:setup", "@do:doctor", "@do:fix"):
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

    def test_setup_doctor_and_fix_resolve_with_optional_body(self):
        cases = (
            ("@do:setup", SETUP_ACTION, ""),
            ("@do:setup\n\nContinue my installation.", SETUP_ACTION, "Continue my installation."),
            ("@do:doctor", DOCTOR_ACTION, ""),
            ("@do:doctor\n\nCheck the setup failure.", DOCTOR_ACTION, "Check the setup failure."),
            ("@do:fix", FIX_ACTION, ""),
            ("@do:fix\n\nDoctor says the runtime is broken.", FIX_ACTION, "Doctor says the runtime is broken."),
        )
        for text, action, body in cases:
            with self.subTest(text=text):
                result = classify_system_action(text)
                self.assertEqual(action, result.action)
                self.assertEqual(body, result.body)

    def test_sot_rejects_body(self):
        with self.assertRaises(ValueError):
            classify_system_action("@do:sot\n\nordinary body")

    def test_body_capable_system_actions_reject_inline_payload_on_action_line(self):
        for action in ("@do:help", "@do:assist", "@do:setup", "@do:doctor", "@do:fix"):
            for text in (f"{action}=value", f"{action} unexpected"):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        classify_system_action(text)

    def test_body_capable_system_actions_reject_param_companions(self):
        for action in ("@do:help", "@do:assist", "@do:setup", "@do:doctor", "@do:fix"):
            text = f"{action}\n@param:x=[1]"
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_body_capable_system_actions_reject_selector_and_control_companions(self):
        for text in (
            "@do:help\n@profile:code/review",
            "@do:assist\n@ctx:personal",
            "@do:help\n@control:learning=on",
            "@do:setup\n@profile:code/review",
            "@do:doctor\n@ctx:personal",
            "@do:fix\n@control:learning=on",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_system_actions_reject_a_second_high_level_action(self):
        for text in (
            "@do:help\n@do:assist",
            "@do:assist\n@do:sot",
            "@do:setup\n@do:doctor",
            "@do:doctor\n@do:fix",
            "@do:fix\n@run:ai/recap",
            "@do:assist\n@recap:2",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_system_action(text)

    def test_high_level_action_exclusivity_is_order_independent(self):
        """A system action must not become invisible merely because another
        directive precedes it in the control block."""
        for text in (
            "@profile:code/review\n@do:help",
            "@ctx:personal\n@do:assist",
            "@run:ai/recap\n@do:help",
            "@recap:2\n@do:assist",
            "@profile:code/review\n@do:sot",
            "@profile:code/review\n@do:setup",
            "@ctx:personal\n@do:doctor",
            "@recap:2\n@do:fix",
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
        for text in ("@do:HELP", "@do:Assist", "@do:Setup", "@do:Doctor", "@do:Fix", "@DO:help"):
            with self.subTest(text=text):
                self.assertIsNone(classify_system_action(text))


class PromptActionTests(unittest.TestCase):
    def test_run_resolves_canonical_prompt_identity(self):
        result = classify_prompt_action("@run:chat/snapshot")
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_edit_resolves_canonical_prompt_identity(self):
        result = classify_prompt_action("@edit:chat/snapshot")
        self.assertEqual(EDIT_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_delete_resolves_canonical_prompt_identity(self):
        result = classify_prompt_action("@delete:chat/snapshot")
        self.assertEqual(DELETE_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_lowercase_segment_nested_path_is_valid(self):
        result = classify_prompt_action("@run:sot/project/create")
        self.assertEqual("sot/project/create", result.prompt_id)

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
        text = "@ctx:personal\n@profile:code/review\n@run:chat/snapshot\n@param:focus=[architecture]"
        result = classify_prompt_action(text)
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_edit_preserves_currently_allowed_composition(self):
        text = "@profile:code/review\n@edit:chat/snapshot"
        result = classify_prompt_action(text)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_delete_resolves_without_requiring_a_second_confirm_directive(self):
        result = classify_prompt_action("@delete:chat/snapshot")
        self.assertEqual(DELETE_ACTION, result.keyword)

    def test_delete_rejects_single_line_param_after(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@delete:chat/snapshot\n@param:x=[1]")

    def test_delete_rejects_single_line_param_before(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@param:x=[1]\n@delete:chat/snapshot")

    def test_delete_rejects_multiline_param(self):
        text = "@delete:chat/snapshot\n@param:x=[[\nliteral data\n]]"
        with self.assertRaises(ValueError):
            classify_prompt_action(text)

    def test_run_with_param_still_resolves(self):
        result = classify_prompt_action("@run:chat/snapshot\n@param:x=[1]")
        self.assertEqual(RUN_ACTION, result.keyword)

    def test_edit_with_param_still_resolves(self):
        result = classify_prompt_action("@edit:chat/snapshot\n@param:x=[1]")
        self.assertEqual(EDIT_ACTION, result.keyword)

    def test_param_looking_text_in_body_does_not_reject_delete(self):
        result = classify_prompt_action("@delete:chat/snapshot\n\n@param:x=[1]")
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

    def test_prompt_action_rejects_a_coexisting_system_action_either_order(self):
        for text in (
            "@run:ai/recap\n@do:help",
            "@do:help\n@run:ai/recap",
            "@run:ai/recap\n@do:assist",
            "@do:assist\n@run:ai/recap",
            "@run:ai/recap\n@do:sot",
            "@do:sot\n@run:ai/recap",
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_prompt_action(text)

    def test_prompt_action_rejects_a_coexisting_recap_either_order(self):
        for text in ("@run:ai/recap\n@recap:2", "@recap:2\n@run:ai/recap"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    classify_prompt_action(text)

    def test_prompt_path_rejects_underscore_segment(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@run:code/review_pr")

    def test_prompt_path_rejects_case_variant(self):
        with self.assertRaises(ValueError):
            classify_prompt_action("@run:Code/review")

    def test_prompt_path_accepts_new_canonical_form(self):
        result = classify_prompt_action("@run:code/review")
        self.assertEqual(result.prompt_id, "code/review")

    def test_prompt_path_accepts_deep_hierarchy(self):
        result = classify_prompt_action("@run:sot/project/create")
        self.assertEqual(result.prompt_id, "sot/project/create")


class ControlBlockBoundaryTests(unittest.TestCase):
    """Defect 1: a real control block exists only when the first non-blank
    line is itself directive-shaped; ordinary text starts the body, and a
    later switch-looking line in that body is not executable."""

    def test_ordinary_text_before_system_action_leaves_it_unresolved(self):
        for action in ("@do:sot", "@do:help", "@do:assist", "@do:setup", "@do:doctor", "@do:fix"):
            with self.subTest(action=action):
                self.assertIsNone(classify_system_action(f"ordinary request\n{action}"))

    def test_ordinary_text_before_prompt_action_leaves_it_unresolved(self):
        for line in ("@run:chat/snapshot", "@edit:chat/snapshot",
                     "@delete:chat/snapshot"):
            with self.subTest(line=line):
                self.assertIsNone(classify_prompt_action(f"ordinary text\n{line}"))

    def test_ordinary_text_before_recap_is_not_promoted_by_either_classifier(self):
        text = "ordinary text\n@recap:2"
        self.assertIsNone(classify_system_action(text))
        self.assertIsNone(classify_prompt_action(text))

    def test_system_action_body_may_contain_switch_looking_text(self):
        result = classify_system_action("@do:help\n\nordinary body\n@run:not_an_action_here")
        self.assertEqual(HELP_ACTION, result.action)
        self.assertIn("@run:not_an_action_here", result.body)

    def test_prompt_action_body_may_contain_switch_looking_text(self):
        result = classify_prompt_action(
            "@run:chat/snapshot\n\nordinary body\n@do:help")
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)


class MultilineParameterOpacityTests(unittest.TestCase):
    """Defect 2: content inside an opened @param:<name>=[[ ... ]] region is
    opaque to high-level-action discovery, including switch-looking text
    and blank lines, regardless of whether they precede or follow it."""

    def test_dangerous_content_inside_multiline_param_is_not_a_second_action(self):
        text = "@run:chat/snapshot\n@param:focus=[[\n@do:sot\n@recap:2\n]]"
        result = classify_prompt_action(text)
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_edit_with_dangerous_multiline_content_is_not_a_second_action(self):
        text = ("@edit:chat/snapshot\n@param:fake=[[\n@delete:other/path\n"
                "@do:sot\n@fmt:yaml\n@param:fake=[value]\n]]")
        result = classify_prompt_action(text)
        self.assertEqual(EDIT_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_blank_line_inside_multiline_param_does_not_end_control_block(self):
        text = "@param:focus=[[\nline one\n\nline two\n]]\n@run:chat/snapshot"
        result = classify_prompt_action(text)
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)

    def test_full_multiline_example_resolves_to_exactly_one_action(self):
        text = (
            "@run:chat/snapshot\n"
            "@param:focus=[[\n"
            "line one\n"
            "\n"
            "@run:this/is_literal_data\n"
            "@do:help\n"
            "@recap:2\n"
            "\n"
            "line two\n"
            "]]"
        )
        result = classify_prompt_action(text)
        self.assertEqual(RUN_ACTION, result.keyword)
        self.assertEqual("chat/snapshot", result.prompt_id)


class ProfileIdentityTests(unittest.TestCase):
    def test_accepts_single_segment(self):
        for identity in ("coding", "research", "profile2"):
            with self.subTest(identity=identity):
                self.assertTrue(is_profile_identity(identity))

    def test_accepts_hierarchical_segments(self):
        for identity in ("code/review", "tech/learn", "lang/german"):
            with self.subTest(identity=identity):
                self.assertTrue(is_profile_identity(identity))

    def test_rejects_underscore_segment(self):
        self.assertFalse(is_profile_identity("tech_learn"))

    def test_rejects_case_variant(self):
        self.assertFalse(is_profile_identity("Tech/Learn"))

    def test_rejects_dot_separator(self):
        self.assertFalse(is_profile_identity("g.coding"))

    def test_rejects_empty_segment(self):
        for identity in ("", "/review", "code/", "code//review"):
            with self.subTest(identity=identity):
                self.assertFalse(is_profile_identity(identity))

    def test_no_identity_segment_is_structurally_reserved(self):
        self.assertTrue(is_profile_identity("g/anything"))
        self.assertTrue(is_profile_identity("game/show"))


if __name__ == "__main__":
    unittest.main()
