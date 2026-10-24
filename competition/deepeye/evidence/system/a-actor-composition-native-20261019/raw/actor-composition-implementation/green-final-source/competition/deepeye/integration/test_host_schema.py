"""Structural interoperability tests; these do not prove runtime pipe isolation."""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


PRODUCT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((PRODUCT / 'docs/host_contract.json').read_text(encoding='utf-8'))
CONTEXT = dict(session=7, config_epoch=2, boot_sha256='a' * 64,
               transport_profile_id=1, source_id=3, topology_id=1,
               acquisition_profile_id=1)


def response():
    return dict(schema_version=1, context=copy.deepcopy(CONTEXT),
                kind='board_response', receipt_interval_ns=dict(lower_ns=10, upper_ns=20),
                wire_frame_hex='00' * 34, timing_record_sha256=None,
                physical_capture_record_sha256=None)


class HostSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Draft202012Validator.check_schema(SCHEMA)
        cls.validator = Draft202012Validator(SCHEMA)

    def test_board_response_structure_has_a_route_from_bridge_to_authority(self):
        self.assertTrue(self.validator.is_valid(response()))
        self.assertIn('board_response', SCHEMA['x-producers']['hardware_bridge'])
        self.assertEqual(SCHEMA['x-authority-only-kinds'], ['board_response'])

    def test_board_response_rejects_hidden_truth_at_every_object_boundary(self):
        for path in [(), ('context',), ('receipt_interval_ns',)]:
            with self.subTest(path=path):
                data = response()
                target = data
                for key in path:
                    target = target[key]
                target['obstacle_xyz'] = [1, 2, 3]
                self.assertFalse(self.validator.is_valid(data))

    def test_measurement_reference_is_optional_but_cannot_be_a_claim_boolean(self):
        for field in ['timing_record_sha256', 'physical_capture_record_sha256']:
            with self.subTest(field=field):
                data = response()
                data[field] = True
                self.assertFalse(self.validator.is_valid(data))
                data[field] = 'b' * 64
                self.assertTrue(self.validator.is_valid(data))

    def test_response_byte_container_is_bounded_and_even_length(self):
        for value in ['00' * 47, '00' * 13, 'a' * 67, 'gg' * 34]:
            with self.subTest(value=value):
                data = response()
                data['wire_frame_hex'] = value
                self.assertFalse(self.validator.is_valid(data))

    def test_numeric_identity_rejects_booleans_and_unknown_enums(self):
        for field, value in [('session', True), ('transport_profile_id', True),
                             ('source_id', 5), ('topology_id', 4),
                             ('acquisition_profile_id', 0)]:
            with self.subTest(field=field, value=value):
                data = response()
                data['context'][field] = value
                self.assertFalse(self.validator.is_valid(data))

    def test_every_declared_message_has_a_producer(self):
        kinds = {ref['$ref'].split('/')[-1] for ref in SCHEMA['oneOf']}
        produced = {kind for group in SCHEMA['x-producers'].values() for kind in group}
        self.assertEqual(kinds, produced)

    def test_local_refs_and_sealed_objects(self):
        def walk(node):
            if isinstance(node, dict):
                if '$ref' in node:
                    self.assertTrue(node['$ref'].startswith('#/$defs/'))
                if node.get('type') == 'object':
                    self.assertIs(node.get('additionalProperties'), False)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(SCHEMA)


if __name__ == '__main__':
    unittest.main()
