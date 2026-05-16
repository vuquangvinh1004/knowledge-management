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
    def test_create_from_template_meta_analysis_has_34_columns(self, board_service, notes_dir):
        board, note_id = board_service.create_from_template(
            "meta_analysis",
            "Meta Full",
            notes_dir=notes_dir,
            create_linked_board_note=False,
        )
        assert board is not None
        assert note_id is None
        cols = board_service.list_columns(board_id=board.id)
        assert len(cols) == 34

    def test_create_from_template_literature_has_20_columns(self, board_service, notes_dir):
        board, note_id = board_service.create_from_template(
            "literature",
            "Lit Board",
            notes_dir=notes_dir,
            create_linked_board_note=False,
        )
        assert board is not None
        assert note_id is None
        cols = board_service.list_columns(board_id=board.id)
        assert len(cols) == 20

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
