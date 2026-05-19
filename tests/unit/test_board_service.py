"""Unit tests cho BoardService."""
from __future__ import annotations

import pytest


@pytest.fixture
def board_service(db_session):
    from core.services.board_service import BoardService
    return BoardService()


@pytest.fixture
def notes_dir(tmp_path):
    d = tmp_path / "notes"
    d.mkdir()
    return d


class TestBoardRows:
    def test_create_row(self, board_service):
        row = board_service.create_row("Nguồn 1")
        assert row.id is not None
        assert row.label == "Nguồn 1"

    def test_list_rows_ordered(self, board_service):
        board_service.create_row("Hàng A")
        board_service.create_row("Hàng B")
        rows = board_service.list_rows()
        assert len(rows) >= 2
        labels = [r.label for r in rows]
        assert "Hàng A" in labels
        assert "Hàng B" in labels

    def test_empty_label_raises(self, board_service):
        from core.utils.exceptions import PKMError
        with pytest.raises(PKMError):
            board_service.create_row("")

    def test_rename_row(self, board_service):
        row = board_service.create_row("Tên cũ")
        board_service.rename_row(row.id, "Tên mới")
        rows = board_service.list_rows()
        renamed = next(r for r in rows if r.id == row.id)
        assert renamed.label == "Tên mới"

    def test_delete_row(self, board_service):
        row = board_service.create_row("Xóa tôi")
        row_id = row.id
        board_service.delete_row(row_id)
        rows = board_service.list_rows()
        assert all(r.id != row_id for r in rows)

    def test_list_rows_scoped_by_board(self, board_service):
        b1 = board_service.create_board("Board A")
        b2 = board_service.create_board("Board B")
        board_service.create_row("A-1", board_id=b1.id)
        board_service.create_row("B-1", board_id=b2.id)

        rows_a = board_service.list_rows(board_id=b1.id)
        rows_b = board_service.list_rows(board_id=b2.id)
        assert [r.label for r in rows_a] == ["A-1"]
        assert [r.label for r in rows_b] == ["B-1"]


class TestBoardColumns:
    def test_create_column(self, board_service):
        col = board_service.create_column("Góc nhìn 1")
        assert col.id is not None
        assert col.label == "Góc nhìn 1"

    def test_rename_column(self, board_service):
        col = board_service.create_column("Cột cũ")
        board_service.rename_column(col.id, "Cột mới")
        cols = board_service.list_columns()
        renamed = next(c for c in cols if c.id == col.id)
        assert renamed.label == "Cột mới"

    def test_delete_column(self, board_service):
        col = board_service.create_column("Xóa cột")
        col_id = col.id
        board_service.delete_column(col_id)
        cols = board_service.list_columns()
        assert all(c.id != col_id for c in cols)

    def test_list_columns_scoped_by_board(self, board_service):
        b1 = board_service.create_board("Board C")
        b2 = board_service.create_board("Board D")
        board_service.create_column("C-1", board_id=b1.id)
        board_service.create_column("D-1", board_id=b2.id)

        cols_c = board_service.list_columns(board_id=b1.id)
        cols_d = board_service.list_columns(board_id=b2.id)
        assert [c.label for c in cols_c] == ["C-1"]
        assert [c.label for c in cols_d] == ["D-1"]


class TestBoardCells:
    def test_update_cell_creates_new(self, board_service):
        row = board_service.create_row("R1")
        col = board_service.create_column("C1")
        cell = board_service.update_cell(row.id, col.id, content_md="Nội dung thử")
        assert cell.id is not None
        assert cell.content_md == "Nội dung thử"

    def test_get_cell(self, board_service):
        row = board_service.create_row("R2")
        col = board_service.create_column("C2")
        board_service.update_cell(row.id, col.id, content_md="Tồn tại")
        cell = board_service.get_cell(row.id, col.id)
        assert cell is not None
        assert cell.content_md == "Tồn tại"

    def test_get_cell_nonexistent_returns_none(self, board_service):
        row = board_service.create_row("R3")
        col = board_service.create_column("C3")
        assert board_service.get_cell(row.id, col.id) is None

    def test_update_cell_overwrites(self, board_service):
        row = board_service.create_row("R4")
        col = board_service.create_column("C4")
        board_service.update_cell(row.id, col.id, content_md="Cũ")
        board_service.update_cell(row.id, col.id, content_md="Mới")
        cell = board_service.get_cell(row.id, col.id)
        assert cell.content_md == "Mới"

    def test_delete_row_cascades_cells(self, board_service):
        row = board_service.create_row("Cascade R")
        col = board_service.create_column("Cascade C")
        board_service.update_cell(row.id, col.id, content_md="cell")
        board_service.delete_row(row.id)
        assert board_service.get_cell(row.id, col.id) is None

    def test_update_cell_cross_board_raises(self, board_service):
        from core.utils.exceptions import PKMError

        b1 = board_service.create_board("Board E")
        b2 = board_service.create_board("Board F")
        row = board_service.create_row("R", board_id=b1.id)
        col = board_service.create_column("C", board_id=b2.id)

        with pytest.raises(PKMError):
            board_service.update_cell(row.id, col.id, content_md="invalid", board_id=b1.id)


class TestBoards:
    def test_create_and_list_boards(self, board_service):
        created = board_service.create_board("Meta Board", board_type="meta_analysis")
        boards = board_service.list_boards()
        assert any(b.id == created.id for b in boards)

    def test_rename_board(self, board_service):
        board = board_service.create_board("Tên cũ")
        board_service.rename_board(board.id, "Tên mới")
        fetched = board_service.get_board(board.id)
        assert fetched.title == "Tên mới"

    def test_delete_board(self, board_service):
        board = board_service.create_board("Delete board")
        board_service.delete_board(board.id)
        boards = board_service.list_boards()
        assert all(b.id != board.id for b in boards)


class TestBoardTemplates:
    def test_create_from_template_meta_analysis_has_30_columns(self, board_service, notes_dir):
        board, note_id = board_service.create_from_template(
            "meta_analysis",
            "Meta Full",
            notes_dir=notes_dir,
            create_linked_board_note=False,
        )
        assert board is not None
        assert note_id is None
        cols = board_service.list_columns(board_id=board.id)
        assert len(cols) == 30

    def test_create_from_template_literature_has_16_columns(self, board_service, notes_dir):
        board, note_id = board_service.create_from_template(
            "literature",
            "Lit Board",
            notes_dir=notes_dir,
            create_linked_board_note=False,
        )
        assert board is not None
        assert note_id is None
        cols = board_service.list_columns(board_id=board.id)
        assert len(cols) == 16

    def test_create_from_template_with_linked_board_note(self, board_service, notes_dir):
        board, note_id = board_service.create_from_template(
            "literature",
            "Lit + Note",
            notes_dir=notes_dir,
            create_linked_board_note=True,
        )
        assert board is not None
        assert note_id is not None
        fetched = board_service.get_board(board.id)
        assert fetched.linked_note_id == note_id

    def test_create_from_template_board_note_only(self, board_service, notes_dir):
        board, note_id = board_service.create_from_template(
            "board_note",
            "board note tong hop",
            notes_dir=notes_dir,
        )
        assert board is None
        assert note_id is not None


class TestBoardSourceNoteSync:
    def test_ensure_full_meta_columns_returns_30(self, board_service):
        cols = board_service.ensure_full_meta_columns()
        assert len(cols) == 30

    def test_sync_rows_with_source_notes_creates_linked_rows(self, board_service, notes_dir):
        from datetime import datetime, timezone

        from core.services.note_service import NoteService
        from core.storage.models import Source
        from core.storage.session import get_session

        with get_session() as session:
            src = Source(
                file_path="D:/sync-source.pdf",
                file_hash="sync_source_hash",
                title="Sync Source",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(src)
            session.flush()
            source_id = int(src.id)

        note = NoteService(notes_dir).create_note(
            title="source - Sync Source",
            note_type="source_note",
            source_id=source_id,
        )

        rows = board_service.sync_rows_with_source_notes()
        assert any(int(r.source_note_id or 0) == int(note.id) for r in rows)

    def test_list_source_note_rows_only_returns_linked_rows(self, board_service, notes_dir):
        from datetime import datetime, timezone

        from core.services.note_service import NoteService
        from core.storage.models import Source
        from core.storage.session import get_session

        with get_session() as session:
            src = Source(
                file_path="D:/linked-only-source.pdf",
                file_hash="linked_only_source_hash",
                title="Linked Only",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(src)
            session.flush()
            source_id = int(src.id)

        note = NoteService(notes_dir).create_note(
            title="source - Linked Only",
            note_type="source_note",
            source_id=source_id,
        )

        board_service.create_row("Legacy Row")
        board_service.sync_rows_with_source_notes()
        rows = board_service.list_source_note_rows()
        assert all(r.source_note_id is not None for r in rows)
        assert any(int(r.source_note_id or 0) == int(note.id) for r in rows)

    def test_sync_cells_from_source_note_metadata_updates_board_cells(self, board_service, notes_dir):
        from datetime import datetime, timezone

        from core.services.note_service import NoteService
        from core.storage.models import Source
        from core.storage.session import get_session

        with get_session() as session:
            src = Source(
                file_path="D:/meta-sync-source.pdf",
                file_hash="meta_sync_source_hash",
                title="Meta Sync Source",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(src)
            session.flush()
            source_id = int(src.id)

        content = (
            "# source - Meta Sync\n\n"
            "## Ghi chú của tôi\n"
            "- \n\n"
            "## Metadata\n"
            "> [!TÁC GIẢ]\n"
            "> Lê Thị Lan Phương, Phạm Huy Kiến Tài.\n\n"
            "> [!NĂM]\n"
            "> 2024\n"
        )

        note = NoteService(notes_dir).create_note(
            title="source - Meta Sync",
            note_type="source_note",
            source_id=source_id,
            initial_content=content,
        )

        board_service.ensure_full_meta_columns()
        rows = board_service.sync_rows_with_source_notes()
        assert any(int(r.source_note_id or 0) == int(note.id) for r in rows)

        changed = board_service.sync_cells_from_source_note_metadata()
        assert changed >= 2

        row = next(r for r in rows if int(r.source_note_id or 0) == int(note.id))
        cols = {c.label: c for c in board_service.ensure_full_meta_columns()}

        author_cell = board_service.get_cell(row.id, cols["Tác giả"].id)
        year_cell = board_service.get_cell(row.id, cols["Năm"].id)
        assert author_cell is not None
        assert year_cell is not None
        assert author_cell.content_md == "Lê Thị Lan Phương, Phạm Huy Kiến Tài."
        assert year_cell.content_md == "2024"

    def test_sync_rows_keeps_existing_cells_when_source_note_soft_deleted(self, board_service, notes_dir):
        from datetime import datetime, timezone

        from core.services.note_service import NoteService
        from core.storage.models import Source
        from core.storage.session import get_session

        note_svc = NoteService(notes_dir)

        with get_session() as session:
            src = Source(
                file_path="D:/meta-persist-source.pdf",
                file_hash="meta_persist_source_hash",
                title="Meta Persist Source",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(src)
            session.flush()
            source_id = int(src.id)

        note = note_svc.create_note(
            title="source - Persist",
            note_type="source_note",
            source_id=source_id,
            initial_content=(
                "# source - Persist\n\n"
                "## Metadata\n"
                "> [!NĂM]\n"
                "> 2025\n"
            ),
        )

        board_service.ensure_full_meta_columns()
        rows = board_service.sync_rows_with_source_notes()
        row = next(r for r in rows if int(r.source_note_id or 0) == int(note.id))
        board_service.sync_cells_from_source_note_metadata()

        year_col = next(c for c in board_service.ensure_full_meta_columns() if c.label == "Năm")
        cell_before = board_service.get_cell(row.id, year_col.id)
        assert cell_before is not None
        assert cell_before.content_md == "2025"

        note_svc.soft_delete(note.id)
        board_service.sync_rows_with_source_notes()
        board_service.sync_cells_from_source_note_metadata()

        cell_after = board_service.get_cell(row.id, year_col.id)
        assert cell_after is not None
        assert cell_after.content_md == "2025"

    def test_sync_cells_from_my_notes_section_without_metadata_header(self, board_service, notes_dir):
        from datetime import datetime, timezone

        from core.services.note_service import NoteService
        from core.storage.models import Source
        from core.storage.session import get_session

        with get_session() as session:
            src = Source(
                file_path="D:/legacy-notes-section-source.pdf",
                file_hash="legacy_notes_section_hash",
                title="Legacy Notes Section",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(src)
            session.flush()
            source_id = int(src.id)

        note = NoteService(notes_dir).create_note(
            title="source - Legacy Metadata",
            note_type="source_note",
            source_id=source_id,
            initial_content=(
                "# source - Legacy Metadata\n\n"
                "## Ghi chú của tôi\n"
                "> [!TÁC GIẢ]\n"
                "> Legacy Author\n\n"
                "> [!NĂM]\n"
                "> 2021\n\n"
                "> [!QUỐC GIA/BỐI CẢNH]\n"
                "> Thông tin tiêu chí.\n"
            ),
        )

        board_service.ensure_full_meta_columns()
        rows = board_service.sync_rows_with_source_notes()
        assert any(int(r.source_note_id or 0) == int(note.id) for r in rows)

        board_service.sync_cells_from_source_note_metadata()
        row = next(r for r in rows if int(r.source_note_id or 0) == int(note.id))
        cols = {c.label: c for c in board_service.ensure_full_meta_columns()}

        author_cell = board_service.get_cell(row.id, cols["Tác giả"].id)
        year_cell = board_service.get_cell(row.id, cols["Năm"].id)
        context_cell = board_service.get_cell(row.id, cols["Quốc gia/Bối cảnh"].id)

        assert author_cell is not None and author_cell.content_md == "Legacy Author"
        assert year_cell is not None and year_cell.content_md == "2021"
        assert context_cell is not None and context_cell.content_md == ""


class TestBoardExport:
    def test_export_markdown_empty(self, board_service):
        md = board_service.export_markdown()
        assert isinstance(md, str)

    def test_export_markdown_with_data(self, board_service):
        row = board_service.create_row("PDF A")
        col = board_service.create_column("Tổng quan")
        board_service.update_cell(row.id, col.id, content_md="Nội dung")
        md = board_service.export_markdown()
        assert "PDF A" in md
        assert "Tổng quan" in md
        assert "Nội dung" in md

    def test_export_csv_with_data(self, board_service):
        row = board_service.create_row("CSV Row")
        col = board_service.create_column("CSV Col")
        board_service.update_cell(row.id, col.id, content_md="csv content")
        csv_output = board_service.export_csv()
        assert "CSV Row" in csv_output
        assert "CSV Col" in csv_output
