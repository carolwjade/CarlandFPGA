"""R01 provenance/trace validation; no registration, model or hardware effects."""
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

PRODUCT = Path(__file__).resolve().parents[1]
REPO = PRODUCT.parents[1]
PATH = PRODUCT / 'tools/check_rules.py'
if PATH.exists():
    spec = importlib.util.spec_from_file_location('deepeye_rule_checker_test_target', PATH)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
else:
    checker = None


class RuleCheckerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(checker, 'taskbook check_rules entrypoint is missing')
        self.rules = json.loads((PRODUCT / 'docs/rules.json').read_bytes())
        self.rows = list(csv.DictReader(io.StringIO((PRODUCT / 'docs/requirements_trace.csv').read_text(encoding='utf-8'))))
        self.scope = json.loads((REPO / 'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())

    def validate(self):
        return checker.validate_metadata(self.rules, self.rows, self.scope)

    def test_current_artifacts_have_fifteen_official_and_fifteen_human_rows(self):
        value = self.validate()
        self.assertEqual(value['official_requirements'], 15)
        self.assertEqual(value['human_requirements'], 15)
        self.assertEqual(value['core_metrics'], 5)
        self.assertEqual(value['special_metrics'], 2)

    def test_removed_human_or_official_row_is_rejected(self):
        for index in (0, 15, 23, 29):
            with self.subTest(index=index):
                rows = copy.deepcopy(self.rows); rows.pop(index)
                with self.assertRaises(ValueError): checker.validate_metadata(self.rules, rows, self.scope)

    def test_duplicate_trace_row_does_not_fake_coverage(self):
        self.rows.append(copy.deepcopy(self.rows[0]))
        with self.assertRaises(ValueError): self.validate()

    def test_scope_content_change_cannot_reuse_pinned_hash_field(self):
        self.scope['requirements'][0]['must'] = 'downgraded'
        with self.assertRaises(ValueError): self.validate()

    def test_human_owner_mapping_cannot_be_omitted_or_redirected(self):
        for owners in ('G01', 'A01', 'G01;G02;G07;G08;not_a_card'):
            with self.subTest(owners=owners):
                self.rows[0]['owner_cards'] = owners
                with self.assertRaises(ValueError): self.validate()

    def test_wrong_page_or_source_is_rejected(self):
        for key, value in (('source_page', '1'), ('source_page', '13;14;29'),
                           ('source', '../amd_guide_20260831.pdf')):
            with self.subTest(key=key, value=value):
                rows = copy.deepcopy(self.rows); rows[15][key] = value
                with self.assertRaises(ValueError): checker.validate_metadata(self.rules, rows, self.scope)

    def test_jointly_changed_csv_and_rules_cannot_move_rocm_requirement(self):
        row = next(r for r in self.rules['requirements'] if r['id'] == 'official_3_2_rocm')
        row['pdf_pages'] = [3]; row['owner_cards'] = ['R01']
        trace = next(r for r in self.rows if r['requirement_id'] == row['id'])
        trace['source_page'] = '3'; trace['owner_cards'] = 'R01'
        with self.assertRaises(ValueError): self.validate()

    def test_declared_metric_count_cannot_replace_missing_actual_metric(self):
        self.rules['requirements'] = [r for r in self.rules['requirements'] if r['id'] != 'official_core_link']
        with self.assertRaises(ValueError): self.validate()

    def test_special_metrics_must_be_distinct_mapped_categories(self):
        for value in (['system reliability', 'system reliability'], ['FPGA resources/timing'], ['novelty', 'looks']):
            with self.subTest(value=value):
                self.rules['selected_special_metrics'] = value
                with self.assertRaises(ValueError): self.validate()

    def test_strict_integer_and_gate_types(self):
        for field in ('schema', 'implementation_task_version', 'core_metrics_count'):
            with self.subTest(field=field):
                rules = copy.deepcopy(self.rules); rules[field] = True
                with self.assertRaises(ValueError): checker.validate_metadata(rules, self.rows, self.scope)
        for value in (True, 'success', 'waived'):
            with self.subTest(gate=value):
                rules = copy.deepcopy(self.rules); rules['gates']['physical_gain_rules_recognition'] = value
                with self.assertRaises(ValueError): checker.validate_metadata(rules, self.rows, self.scope)

    def test_source_identity_claims_cannot_substitute_for_original_bytes(self):
        for field, value in (('sha256', 'a' * 64), ('filename', '../../secret'), ('pdf_pages', True)):
            with self.subTest(field=field):
                rules = copy.deepcopy(self.rules); rules['source'][field] = value
                with self.assertRaises(ValueError): checker.validate_metadata(rules, self.rows, self.scope)

    def test_requirement_status_mismatch_or_unknown_status_is_rejected(self):
        for value in ('passed', 'unknown'):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.rows); rows[15]['status'] = value
                with self.assertRaises(ValueError): checker.validate_metadata(self.rules, rows, self.scope)

    def test_json_duplicate_keys_and_nonfinite_constants_are_rejected(self):
        for raw in (b'{"schema":1,"schema":1}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): checker.parse_json(raw)

    def test_json_exponent_overflow_is_rejected_at_any_depth(self):
        for raw in (b'{"x":1e99999}', b'{"claim":{"x":[-1e99999]}}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): checker.parse_json(raw)
        self.assertEqual(checker.parse_json(b'{"x":1.25e2}'), {'x': 125.0})

    def test_csv_headers_extra_columns_and_oversized_metadata_are_rejected(self):
        for raw in (b'requirement_id,source,source_page,owner_cards,status,status\n',
                    b'requirement_id,source,source_page,owner_cards,status\nH01,x,,G01,not_run,extra\n',
                    b'x' * (1_048_576 + 1)):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): checker.parse_trace(raw)

    def test_missing_source_stays_blocked_and_forged_pdf_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'source.pdf'
            missing = checker.verify_source(path)
            self.assertEqual(missing['status'], 'blocked')
            path.write_bytes(b'%PDF-1.7\nfake')
            with self.assertRaises(ValueError): checker.verify_source(path)

    def test_all_passed_metadata_cannot_grant_formal_acceptance(self):
        for row in self.rules['requirements']: row['product_status'] = 'passed'
        for row in self.rows: row['status'] = 'passed'
        for key in ('rocm_project_C03', 'physical_gain_rules_recognition', 'physical_gain_engineering_A05', 'R01'):
            self.rules['gates'][key] = 'passed'
        coverage = self.validate()
        for reference, code in ((False, 2), (True, 0)):
            with self.subTest(reference=reference):
                result, actual = checker.make_result(coverage, {'status': 'passed'}, self.rules, reference)
                self.assertEqual(actual, code)
                self.assertEqual(result['R01'], 'not_run')
                self.assertFalse(result['hardware_enable_eligible'])
                self.assertFalse(result['formal_acceptance'])


if __name__ == '__main__': unittest.main()
