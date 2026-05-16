"""Service quản lý file assets (chụp ảnh từ PDF và nguồn khác)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.storage.models import Asset
from core.storage.session import get_session
from core.utils.exceptions import PKMError
from core.utils.logger import get_logger

logger = get_logger()


class AssetService:
    """Lưu trữ và quản lý asset files (ảnh, sao chụp)."""

    def __init__(self, assets_dir: Path) -> None:
        self._assets_dir = Path(assets_dir)
        self._assets_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def save_image_asset(
        self,
        source_id: int,
        image_bytes: bytes,
        note_id: int | None = None,
        caption: str | None = None,
        filename: str | None = None,
    ) -> Asset:
        """
        Lưu ảnh PNG vào assets_dir và tạo bản ghi Asset trong DB.

        Args:
            source_id: ID của source.
            image_bytes: PNG bytes.
            note_id: Note liên kết (tùy chọn).
            caption: Chú thích (tùy chọn).
            filename: Tên file (tự sinh nếu None).

        Returns:
            Asset đã lưu vào DB.
        """
        if not image_bytes:
            raise PKMError("image_bytes không được rỗng.")

        if filename is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            filename = f"capture_{source_id}_{ts}.png"

        dest = self._assets_dir / filename
        dest.write_bytes(image_bytes)
        logger.info(f"Lưu asset: {dest}")

        now = datetime.now(timezone.utc)
        asset = Asset(
            source_id=source_id,
            note_id=note_id,
            asset_type="image",
            file_path=str(dest),
            caption=caption,
            created_at=now,
        )
        with get_session() as session:
            session.add(asset)
            session.flush()
            session.expunge(asset)
        return asset

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_id(self, asset_id: int) -> Asset:
        """
        Raises:
            PKMError: Nếu không tìm thấy.
        """
        with get_session() as session:
            asset = session.get(Asset, asset_id)
            if asset is None:
                raise PKMError(f"Không tìm thấy asset id={asset_id}.")
            session.expunge(asset)
            return asset

    def list_by_source(self, source_id: int) -> list[Asset]:
        """Danh sách assets theo source."""
        with get_session() as session:
            assets = (
                session.query(Asset)
                .filter(Asset.source_id == source_id)
                .order_by(Asset.created_at.desc())
                .all()
            )
            for a in assets:
                session.expunge(a)
            return assets

    def delete_asset(self, asset_id: int, delete_file: bool = False) -> None:
        """Xóa asset khỏi DB và tùy chọn xóa file."""
        with get_session() as session:
            asset = session.get(Asset, asset_id)
            if asset is None:
                return
            file_path = Path(asset.file_path)
            session.delete(asset)
        if delete_file and file_path.exists():
            file_path.unlink()
            logger.info(f"Xóa asset file: {file_path}")
