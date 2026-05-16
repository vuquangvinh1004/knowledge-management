"""Unit tests cho GraphService (Phase A)."""
from __future__ import annotations

import pytest

from core.services.graph_service import GraphService
from core.services.link_service import LinkService
from core.services.note_service import NoteService
from core.services.tag_service import TagService
from core.utils.exceptions import PKMError


@pytest.fixture
def note_svc(notes_dir):
    return NoteService(notes_dir=notes_dir)


@pytest.fixture
def graph_seed(db_session, note_svc):
    link_svc = LinkService()
    tag_svc = TagService()

    n1 = note_svc.create_note("Alpha Note", "concept_note")
    n2 = note_svc.create_note("Beta Note", "synthesis_note")
    n3 = note_svc.create_note("Gamma Note", "concept_note")

    link_svc.create_link(n1.id, n2.id, "wikilink")
    link_svc.create_link(n2.id, n3.id, "manual")

    tag_svc.add_tag_to_note(n1.id, "method")
    tag_svc.add_tag_to_note(n2.id, "method")
    tag_svc.add_tag_to_note(n3.id, "result")

    return n1, n2, n3


class TestGraphService:
    def test_build_graph_returns_nodes_and_edges(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph()

        assert len(snapshot.nodes) == 3
        assert len(snapshot.edges) == 2

    def test_filter_by_note_type(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(note_type="concept_note")

        node_ids = {n.note_id for n in snapshot.nodes}
        assert len(snapshot.nodes) == 2
        assert len(snapshot.edges) == 0
        assert node_ids

    def test_filter_by_tag(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(tag="method")

        assert len(snapshot.nodes) == 2
        assert len(snapshot.edges) == 1
        assert snapshot.edges[0].link_type == "wikilink"

    def test_filter_by_tag_not_found_returns_empty(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(tag="does-not-exist")

        assert snapshot.nodes == []
        assert snapshot.edges == []

    def test_exclude_isolated_nodes(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(note_type="concept_note", include_isolated=False)

        assert snapshot.nodes == []
        assert snapshot.edges == []

    def test_invalid_note_type_raises(self, db_session, graph_seed):
        svc = GraphService()
        with pytest.raises(PKMError):
            svc.build_graph(note_type="invalid_type")

    def test_source_filter_without_source_notes_returns_empty(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(source_id=999)

        assert snapshot.nodes == []
        assert snapshot.edges == []

    def test_virtualize_by_limit_nodes(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(limit_nodes=2)

        assert snapshot.is_virtualized is True
        assert snapshot.virtualized_from == 3
        assert len(snapshot.nodes) == 2
        assert len(snapshot.edges) <= 1

    def test_no_virtualize_when_limit_not_hit(self, db_session, graph_seed):
        svc = GraphService()
        snapshot = svc.build_graph(limit_nodes=10)

        assert snapshot.is_virtualized is False
        assert snapshot.virtualized_from == 0
        assert len(snapshot.nodes) == 3
