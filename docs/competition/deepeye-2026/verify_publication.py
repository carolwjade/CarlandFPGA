"""Read-only publication verification; never writes source files or product state.

Run from any directory with Python 3. No third-party packages are required.
This verifies document integrity and coverage, not product acceptance.
"""
from pathlib import Path
import hashlib
import json
import re


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def verify(base):
    publication = json.loads((base / 'publication_manifest.json').read_bytes())
    release_bytes = (base / 'release_manifest_final.json').read_bytes()
    assert sha256(release_bytes) == publication['frozen_release_manifest_sha256'], 'Frozen manifest changed'
    release = json.loads(release_bytes)
    assert len(release['files']) == 59, 'Unexpected frozen release file count'
    copied = publication['copied_source_files']
    assert set(copied) == set(release['files']) | {'release_manifest_final.json', 'sources/provenance.json'}
    assert len(copied) == publication['source_file_count'] == 61
    for name, expected in copied.items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts, name
        value = (base / relative).read_bytes()
        assert len(value) == expected['bytes'], 'Byte count mismatch: ' + name
        assert sha256(value) == expected['sha256'], 'Source hash mismatch: ' + name
        if name in release['files']:
            assert expected == release['files'][name], 'Sealed release entry mismatch: ' + name

    compiled_meta = publication['compiled']
    compiled = (base / compiled_meta['path']).read_bytes()
    assert len(compiled) == compiled_meta['bytes']
    assert sha256(compiled) == compiled_meta['sha256'], 'Complete reader changed or truncated'
    sections = compiled_meta['sections']
    inline_names = {part['source'] for part in sections}
    binaries = set(publication['binary_originals'])
    assert inline_names == set(copied) - binaries, 'A text original is missing from the reader'
    assert len(sections) == len(inline_names) == publication['inline_text_source_count'] == 59
    previous_end = 0
    relative_links = []
    for part in sections:
        name = part['source']
        source = (base / name).read_bytes()
        expected = source.decode('utf-8')
        for change in part['relative_link_rewrites']:
            expected = expected.replace('](' + change['from'] + ')', '](' + change['to'] + ')')
        expected = expected.encode('utf-8')
        start = part['inline_start_byte']
        end = start + part['inline_bytes']
        assert previous_end <= start < end <= len(compiled), 'Overlapping/missing inline range: ' + name
        previous_end = end
        assert compiled[start:end] == expected, 'Incomplete or modified inline source: ' + name
        assert sha256(source) == part['source_sha256']
        assert sha256(expected) == part['inline_sha256']
        assert ('<a id="' + part['anchor'] + '"></a>').encode() in compiled
        if name.endswith('.md'):
            relative_links.extend(re.findall(r'\]\(([^)]+)\)', expected.decode('utf-8')))

    # All inline Markdown relative links now resolve in this reader's directory.
    for link in relative_links:
        if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', link) or link.startswith(('#', '/', '//')):
            continue
        path = link.split('#', 1)[0].split('?', 1)[0]
        assert (base / path).exists(), 'Broken local Markdown link: ' + link

    contract = json.loads((base / 'immutable_scope.json').read_bytes())
    canonical = json.dumps(contract['requirements'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    lock = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
    assert sha256(canonical) == contract['requirements_sha256'] == publication['immutable_scope_sha256'] == lock
    assert [item['id'] for item in contract['requirements']] == [f'H{i:02d}' for i in range(1, 16)]
    book = (base / 'taskbook_final.md').read_text(encoding='utf-8')
    complete_text = compiled.decode('utf-8')
    for item in contract['requirements']:
        assert item['must'] in book and item['must'] in complete_text, 'Missing human requirement: ' + item['id']
    assert len(re.findall(r'^## (?:[1-9]|1[0-8]) ', book, re.M)) == 18
    plan = json.loads((base / 'execution_plan_final.json').read_bytes())
    cards = plan['tasks']
    assert len(cards) == 29
    book_cards = re.findall(r'^### ((?:R|A|B|C|G)\d{2})\b', book, re.M)
    assert len(book_cards) == 29 and set(book_cards) == set(cards), 'Root task card coverage mismatch'
    assert {card['status'] for card in cards.values()} == {'not_run'}, 'Frozen baseline status changed'
    assert plan['immutable_scope_sha256'] == lock
    visited = set()
    visiting = set()

    def visit(card_id):
        assert card_id in cards, 'Unknown dependency: ' + card_id
        assert card_id not in visiting, 'Dependency cycle: ' + card_id
        if card_id in visited:
            return
        visiting.add(card_id)
        for dependency in cards[card_id]['dependencies']:
            visit(dependency)
        visiting.remove(card_id)
        visited.add(card_id)

    for card_id in cards:
        assert cards[card_id]['owner'] in {'A', 'B', 'C'}
        visit(card_id)
    for item in contract['requirements']:
        assert set(item['acceptance_cards']) <= set(cards)

    active_fence = None
    for line in complete_text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if not match:
            continue
        fence, rest = match.groups()
        if active_fence is None:
            active_fence = fence
        elif fence[0] == active_fence[0] and len(fence) >= len(active_fence) and not rest.strip():
            active_fence = None
    assert active_fence is None, 'Unclosed Markdown code fence'
    assert (base / 'deepeye_taskbook_final.pdf').read_bytes().startswith(b'%PDF-')
    assert (base / 'architecture_v4.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    return {
        'status': 'passed', 'scope': 'publication byte integrity, complete inline coverage and static document consistency only',
        'frozen_release_files': 59, 'copied_originals': len(copied), 'inline_text_originals': len(sections),
        'chapters': 18, 'root_task_cards': len(cards), 'human_requirements': 15,
        'compiled_bytes': len(compiled), 'compiled_sha256': sha256(compiled),
        'product_acceptance': 'not asserted; consult the implementation director for current evidence',
    }


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), ensure_ascii=False, indent=2))
