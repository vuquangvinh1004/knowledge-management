"""Unit tests cho TagService và LinkService."""
from __future__ import annotations

import pytest

from core.services.link_service import LinkService
from core.services.note_service import NoteService
from core.services.tag_service import TagService
from core.utils.exceptions import PKMError


@pytest.fixture
def note_svc(notes_dir):
    return NoteService(notes_dir=notes_dir)


@pytest.fixture
def tag_svc():
    return TagService()


@pytest.fixture
def link_svc():
    return LinkService()


@pytest.fixture
def two_notes(note_svc, db_session):
    n1 = note_svc.create_note("Note Alpha", "concept_note")
    n2 = note_svc.create_note("Note Beta", "concept_note")
    return n1, n2


class TestTagService:
    def test_get_or_create_tag(self, tag_svc, db_session):
        tag = tag_svc.get_or_create_tag("Python")
        assert tag.id is not None
        assert tag.name == "python"  # normalize lowercase

    def test_get_or_create_tag_idempotent(self, tag_svc, db_session):
        t1 = tag_svc.get_or_create_tag("AI")
        t2 = tag_svc.get_or_create_tag("ai")
        assert t1.id == t2.id

    def test_empty_tag_name_raises(self, tag_svc, db_session):
        with pytest.raises(PKMError):
            tag_svc.get_or_create_tag("  ")

    def test_add_tag_to_note(self, tag_svc, note_svc, db_session):
        note = note_svc.create_note("Tagged Note", "concept_note")
        tag_svc.add_tag_to_note(note.id, "research")
        tags = tag_svc.get_tags_for_note(note.id)
        assert any(t.name == "research" for t in tags)

    def test_add_same_tag_twice_is_idempotent(self, tag_svc, note_svc, db_session):
        note = note_svc.create_note("Idempotent", "concept_note")
        tag_svc.add_tag_to_note(note.id, "test")
        tag_svc.add_tag_to_note(note.id, "test")  # Không raise
        assert len(tag_svc.get_tags_for_note(note.id)) == 1

    def test_remove_tag_from_note(self, tag_svc, note_svc, db_session):
        note = note_svc.create_note("Remove Tag", "concept_note")
        tag_svc.add_tag_to_note(note.id, "temp")
        tag_svc.remove_tag_from_note(note.id, "temp")
        assert tag_svc.get_tags_for_note(note.id) == []

    def test_list_tags(self, tag_svc, db_session):
        tag_svc.get_or_create_tag("z-tag")
        tag_svc.get_or_create_tag("a-tag")
        tags = tag_svc.list_tags()
        names = [t.name for t in tags]
        assert names == sorted(names)  # sorted by name


class TestLinkService:
    def test_create_manual_link(self, link_svc, two_notes, db_session):
        n1, n2 = two_notes
        link = link_svc.create_link(n1.id, n2.id, "manual")
        assert link.id is not None
        assert link.from_note_id == n1.id
        assert link.to_note_id == n2.id

    def test_create_duplicate_link_returns_existing(self, link_svc, two_notes, db_session):
        n1, n2 = two_notes
        lnk1 = link_svc.create_link(n1.id, n2.id, "manual")
        lnk2 = link_svc.create_link(n1.id, n2.id, "manual")
        assert lnk1.id == lnk2.id

    def test_self_link_raises(self, link_svc, two_notes, db_session):
        n1, _ = two_notes
        with pytest.raises(PKMError, match="tự trỏ"):
            link_svc.create_link(n1.id, n1.id)

    def test_invalid_link_type_raises(self, link_svc, two_notes, db_session):
        n1, n2 = two_notes
        with pytest.raises(PKMError, match="link_type"):
            link_svc.create_link(n1.id, n2.id, "invalid")

    def test_get_backlinks(self, link_svc, two_notes, db_session):
        n1, n2 = two_notes
        link_svc.create_link(n1.id, n2.id, "wikilink")
        backlinks = link_svc.get_backlinks(n2.id)
        assert len(backlinks) == 1
        assert backlinks[0].from_note_id == n1.id

    def test_get_outgoing_links(self, link_svc, two_notes, db_session):
        n1, n2 = two_notes
        link_svc.create_link(n1.id, n2.id, "manual")
        outgoing = link_svc.get_outgoing_links(n1.id)
        assert len(outgoing) == 1

    def test_resolve_wikilink_by_slug(self, link_svc, note_svc, db_session):
        note = note_svc.create_note("Wikilink Target", "concept_note")
        found = link_svc.resolve_wikilink("wikilink-target")
        assert found is not None
        assert found.id == note.id

    def test_resolve_wikilink_not_found(self, link_svc, db_session):
        result = link_svc.resolve_wikilink("nonexistent-note")
        assert result is None
