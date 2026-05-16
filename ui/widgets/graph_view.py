"""Graph view widget cho FEAT-01 Phase C/D.

Phase C:
- Tìm node
- Highlight hàng xóm 1-hop/2-hop
- Fit-to-view

Phase D:
- Gom cụm theo tag
- Lưu layout cục bộ
- Virtualize khi đồ thị lớn
"""
from __future__ import annotations

import math
from collections import defaultdict, deque

from PySide6.QtCore import QPointF, QRectF, Qt, QStringListModel, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QCheckBox,
    QCompleter,
    QComboBox,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.graph_service import GraphEdge, GraphSnapshot, GraphService
from core.services.settings_service import SettingsService
from core.utils.logger import get_logger

logger = get_logger()


class _GraphCanvas(QGraphicsView):
    """Canvas đồ thị hỗ trợ pan/zoom."""

    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QBrush(QColor("#F7F9FD")))
        self.setStyleSheet("QGraphicsView { background-color: #F7F9FD; border: 1px solid #D0D4E8; }")

    def wheelEvent(self, event) -> None:  # noqa: N802
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class _GraphNodeItem(QGraphicsItem):
    """Node đa hình: circle (concept/synthesis/board), square (source), triangle (internal #)."""

    SHAPE_CIRCLE = "circle"
    SHAPE_SQUARE = "square"
    SHAPE_TRIANGLE = "triangle"

    def __init__(
        self,
        *,
        note_id: int,
        source_id: int | None,
        center: QPointF,
        radius: float,
        fill: QColor,
        shape: str = SHAPE_CIRCLE,
        on_select,
        on_open,
        on_move_end,
    ) -> None:
        super().__init__()
        self.setPos(center)
        self.note_id = note_id
        self.source_id = source_id
        self._radius = radius
        self._shape = shape
        self._base_fill = QColor(fill)
        self._on_select = on_select
        self._on_open = on_open
        self._on_move_end = on_move_end

        self._label: QGraphicsSimpleTextItem | None = None
        self._full_title: str = ""
        self._hover_bg: QGraphicsRectItem | None = None
        self._hover_text: QGraphicsSimpleTextItem | None = None

        self._pen = QPen(QColor("#374151"), 1.2)
        self._brush = QBrush(QColor(fill))

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2.0)
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        r = self._radius + 3
        return QRectF(-r, -r, r * 2, r * 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # noqa: N802
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        r = self._radius
        if self._shape == self.SHAPE_SQUARE:
            painter.drawRect(QRectF(-r, -r, r * 2, r * 2))
        elif self._shape == self.SHAPE_TRIANGLE:
            poly = QPolygonF([
                QPointF(0.0, -r),
                QPointF(r, r * 0.85),
                QPointF(-r, r * 0.85),
            ])
            painter.drawPolygon(poly)
        else:  # SHAPE_CIRCLE
            painter.drawEllipse(QRectF(-r, -r, r * 2, r * 2))

    def add_label(self, text: str, *, full: bool = False) -> None:
        self._full_title = text
        display = text if full else ((text[:15] + "…") if len(text) > 15 else text)
        self._label = QGraphicsSimpleTextItem(display, self)
        font = QFont()
        font.setPointSize(7)
        self._label.setFont(font)
        br = self._label.boundingRect()
        y_off = (self._radius * 0.85 + 4) if self._shape == self.SHAPE_TRIANGLE else (self._radius + 4)
        self._label.setPos(-br.width() / 2, y_off)
        self._label.setBrush(QBrush(QColor("#1A1A2E")))

    def hoverEnterEvent(self, event) -> None:  # noqa: N802
        self._show_hover_label()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802
        self._hide_hover_label()
        super().hoverLeaveEvent(event)

    def _show_hover_label(self) -> None:
        scene = self.scene()
        if not self._full_title or scene is None or self._hover_bg is not None:
            return
        font = QFont()
        font.setPointSize(9)
        text_item = QGraphicsSimpleTextItem(self._full_title)
        text_item.setFont(font)
        text_item.setBrush(QBrush(QColor("#1A1A2E")))
        br = text_item.boundingRect()
        pad = 5
        pos = self.scenePos() + QPointF(self._radius + 6, -br.height() / 2)
        bg = QGraphicsRectItem(QRectF(-pad, -pad, br.width() + 2 * pad, br.height() + 2 * pad))
        bg.setBrush(QBrush(QColor("#FFF7E8")))
        bg.setPen(QPen(QColor("#E7B96C"), 0.8))
        bg.setPos(pos)
        bg.setZValue(14)
        text_item.setPos(pos)
        text_item.setZValue(15)
        scene.addItem(bg)
        scene.addItem(text_item)
        self._hover_bg = bg
        self._hover_text = text_item

    def _hide_hover_label(self) -> None:
        for item in (self._hover_bg, self._hover_text):
            if item is not None and item.scene() is not None:
                item.scene().removeItem(item)
        self._hover_bg = None
        self._hover_text = None

    def set_visual_state(self, state: str) -> None:
        """Đổi style theo trạng thái: selected, near, dim, normal."""
        fill = QColor(self._base_fill)
        if state == "selected":
            self._pen = QPen(QColor("#1C2233"), 2.4)
            self._brush = QBrush(fill.lighter(120))
            self.setZValue(4.0)
            if self._label is not None:
                self._label.setBrush(QBrush(QColor("#111827")))
        elif state == "near":
            self._pen = QPen(fill.darker(150), 1.8)
            self._brush = QBrush(fill)
            self.setZValue(3.0)
            if self._label is not None:
                self._label.setBrush(QBrush(QColor("#1E40AF")))
        elif state == "dim":
            fill.setAlpha(55)
            self._pen = QPen(QColor("#C7D0E2"), 1.0)
            self._brush = QBrush(fill)
            self.setZValue(1.0)
            if self._label is not None:
                self._label.setBrush(QBrush(QColor("#9AA3B2")))
        else:
            self._pen = QPen(QColor("#374151"), 1.2)
            self._brush = QBrush(QColor(self._base_fill))
            self.setZValue(2.0)
            if self._label is not None:
                self._label.setBrush(QBrush(QColor("#1A1A2E")))
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._on_select is not None:
            self._on_select(self.note_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._on_open is not None:
            self._on_open(self.note_id, self.source_id)
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)
        if self._on_move_end is not None:
            self._on_move_end(self.note_id, self.scenePos())


class GraphViewWidget(QWidget):
    """Widget hiển thị graph note-link hoàn chỉnh cho FEAT-01."""

    note_open_requested = Signal(int)
    source_open_requested = Signal(int)

    _NOTE_TYPE_OPTIONS = [
        ("Tất cả", None),
        ("Ghi chú nguồn", "source_note"),
        ("Ghi chú khái niệm", "concept_note"),
        ("Ghi chú tổng hợp", "synthesis_note"),
        ("Ghi chú board", "board_note"),
    ]

    _HOP_OPTIONS = [
        ("Không", 0),
        ("1-hop", 1),
        ("2-hop", 2),
    ]

    _TYPE_COLORS = {
        "source_note": QColor("#4A6CF7"),
        "concept_note": QColor("#20A39E"),
        "synthesis_note": QColor("#F29E4C"),
        "board_note": QColor("#8E7DBE"),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = GraphService()
        self._settings = SettingsService()

        self._scene = QGraphicsScene(self)
        self._scene.setBackgroundBrush(QBrush(QColor("#F7F9FD")))
        self._snapshot = GraphSnapshot()

        self._node_items: dict[int, _GraphNodeItem] = {}
        self._edge_items: list[tuple[GraphEdge, QGraphicsLineItem]] = []
        self._adjacency: dict[int, set[int]] = {}
        self._selected_note_id: int | None = None

        self._layout_positions = self._load_layout_positions()

        self._build_ui()
        self.refresh_graph()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Bộ lọc chính
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self._combo_note_type = QComboBox()
        for label, value in self._NOTE_TYPE_OPTIONS:
            self._combo_note_type.addItem(label, value)
        self._combo_note_type.currentIndexChanged.connect(self.refresh_graph)
        filter_row.addWidget(QLabel("Loại:"))
        filter_row.addWidget(self._combo_note_type)

        self._edit_tag = QLineEdit()
        self._edit_tag.setPlaceholderText("Tag")
        self._edit_tag.returnPressed.connect(self.refresh_graph)
        self._edit_tag.setMaximumWidth(160)
        self._tag_completer = QCompleter([], self)
        self._tag_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._tag_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._edit_tag.setCompleter(self._tag_completer)
        filter_row.addWidget(QLabel("Tag:"))
        filter_row.addWidget(self._edit_tag)

        self._edit_source_id = QLineEdit()
        self._edit_source_id.setPlaceholderText("AA01")
        self._edit_source_id.setMaximumWidth(110)
        self._edit_source_id.returnPressed.connect(self.refresh_graph)
        filter_row.addWidget(QLabel("Source:"))
        filter_row.addWidget(self._edit_source_id)

        self._btn_refresh = QPushButton("Làm mới")
        self._btn_refresh.clicked.connect(self.refresh_graph)
        filter_row.addWidget(self._btn_refresh)

        self._btn_fit = QPushButton("Fit")
        self._btn_fit.setToolTip("Thu vừa đồ thị vào khung nhìn")
        self._btn_fit.clicked.connect(self._fit_to_scene)
        filter_row.addWidget(self._btn_fit)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # UX + tối ưu
        ux_row = QHBoxLayout()
        ux_row.setSpacing(6)

        self._edit_search = QLineEdit()
        self._edit_search.setPlaceholderText("Tìm node theo title/slug/tag")
        self._edit_search.returnPressed.connect(self._on_search_node)
        ux_row.addWidget(self._edit_search)

        self._btn_search = QPushButton("Tìm node")
        self._btn_search.clicked.connect(self._on_search_node)
        ux_row.addWidget(self._btn_search)

        self._combo_hops = QComboBox()
        for label, value in self._HOP_OPTIONS:
            self._combo_hops.addItem(label, value)
        self._combo_hops.setCurrentIndex(2)  # 2-hop
        self._combo_hops.currentIndexChanged.connect(self._apply_highlight)
        ux_row.addWidget(QLabel("Highlight:"))
        ux_row.addWidget(self._combo_hops)

        self._chk_cluster_by_tag = QCheckBox("Gom cụm theo tag")
        self._chk_cluster_by_tag.toggled.connect(self.refresh_graph)
        ux_row.addWidget(self._chk_cluster_by_tag)

        self._chk_include_isolated = QCheckBox("Bao gồm isolated nodes")
        self._chk_include_isolated.setChecked(True)
        self._chk_include_isolated.toggled.connect(self.refresh_graph)
        ux_row.addWidget(self._chk_include_isolated)

        self._chk_virtualize = QCheckBox("Virtualize")
        ux_row.addWidget(self._chk_virtualize)

        self._combo_max_nodes = QComboBox()
        for n in [120, 180, 260, 360]:
            self._combo_max_nodes.addItem(str(n), n)
        ux_row.addWidget(QLabel("Max node:"))
        ux_row.addWidget(self._combo_max_nodes)

        self._btn_save_layout = QPushButton("Lưu layout")
        self._btn_save_layout.clicked.connect(self._save_layout_now)
        ux_row.addWidget(self._btn_save_layout)

        self._btn_clear_layout = QPushButton("Xóa layout")
        self._btn_clear_layout.clicked.connect(self._clear_layout_current)
        ux_row.addWidget(self._btn_clear_layout)

        layout.addLayout(ux_row)

        self._canvas = _GraphCanvas(self._scene)
        self._canvas.setMinimumHeight(420)
        layout.addWidget(self._canvas, stretch=1)

        self._lbl_status = QLabel("Sẵn sàng")
        layout.addWidget(self._lbl_status)

        # Khôi phục preference virtualize của người dùng
        self._restore_virtualize_preferences()
        self._chk_virtualize.toggled.connect(self._on_virtualize_pref_changed)
        self._combo_max_nodes.currentIndexChanged.connect(self._on_max_nodes_pref_changed)

    def refresh_graph(self) -> None:
        """Load graph snapshot từ service và render lên canvas."""
        note_type = self._combo_note_type.currentData()
        tag = self._edit_tag.text().strip() or None

        source_raw = self._edit_source_id.text().strip()
        source_code = source_raw if source_raw else None

        limit_nodes = None
        if self._chk_virtualize.isChecked():
            limit_nodes = self._combo_max_nodes.currentData()

        include_isolated = self._chk_include_isolated.isChecked()

        snapshot = self._service.build_graph(
            note_type=note_type,
            tag=tag,
            source_code=source_code,
            include_isolated=include_isolated,
            limit_nodes=limit_nodes,
        )

        self._snapshot = snapshot
        self._adjacency = self._build_adjacency(snapshot.edges)

        if self._selected_note_id is not None:
            exists = any(n.note_id == self._selected_note_id for n in snapshot.nodes)
            if not exists:
                self._selected_note_id = None

        self._render_snapshot(snapshot)

    def _render_snapshot(self, snapshot: GraphSnapshot) -> None:
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()

        if not snapshot.nodes:
            self._lbl_status.setText("Không có dữ liệu đồ thị theo bộ lọc hiện tại.")
            return

        positions = self._build_node_positions(snapshot)

        # Tính degree (số cạnh mỗi node)
        degree_map: dict[int, int] = {n.note_id: 0 for n in snapshot.nodes}
        for edge in snapshot.edges:
            degree_map[edge.from_note_id] = degree_map.get(edge.from_note_id, 0) + 1
            degree_map[edge.to_note_id] = degree_map.get(edge.to_note_id, 0) + 1

        # Edges vẽ trước
        for edge in snapshot.edges:
            p1 = positions.get(edge.from_note_id)
            p2 = positions.get(edge.to_note_id)
            if p1 is None or p2 is None:
                continue
            line_item = self._scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), self._edge_pen(edge))
            line_item.setZValue(0.0)
            self._edge_items.append((edge, line_item))

        # Nodes vẽ sau
        for node in snapshot.nodes:
            pos = positions[node.note_id]

            # Xác định hình dạng và màu
            if node.note_type == "source_note":
                shape = _GraphNodeItem.SHAPE_SQUARE
                color = self._TYPE_COLORS.get("source_note", QColor("#3F88C5"))
            elif (
                node.note_type == "concept_note"
                and node.title
                and node.title.startswith("#")
            ):
                shape = _GraphNodeItem.SHAPE_TRIANGLE
                color = QColor("#4A6CF7")  # xanh dương cho internal
            else:
                shape = _GraphNodeItem.SHAPE_CIRCLE
                color = self._TYPE_COLORS.get(node.note_type, QColor("#999999"))

            # Kích cỡ node theo degree
            degree = degree_map.get(node.note_id, 0)
            radius = min(14.0 + degree * 3.5, 36.0)

            item = _GraphNodeItem(
                note_id=node.note_id,
                source_id=node.source_id,
                center=pos,
                radius=radius,
                fill=color,
                shape=shape,
                on_select=self._on_node_selected,
                on_open=self._on_node_open,
                on_move_end=self._on_node_move_end,
            )

            # Label
            if node.note_type == "source_note":
                label_text = node.source_code or node.title or f"Note {node.note_id}"
                item.add_label(label_text, full=False)
            else:
                label_text = node.title or f"Note {node.note_id}"
                item.add_label(label_text, full=True)

            # Tooltip
            src_display = (
                node.source_code
                or (str(node.source_id) if node.source_id is not None else "-")
            )
            tags_text = f"\nTags: {', '.join(node.tags)}" if node.tags else ""
            item.setToolTip(
                f"{node.title}\nType: {node.note_type}\nNote ID: {node.note_id}"
                f"\nSource: {src_display}{tags_text}"
                "\nTip: click để highlight, double-click để mở."
            )

            self._scene.addItem(item)
            self._node_items[node.note_id] = item

        rect = self._scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self._scene.setSceneRect(rect)
        self._fit_to_scene()
        self._apply_highlight()

        status = f"Nút: {len(snapshot.nodes)} | Cạnh: {len(snapshot.edges)}"
        if snapshot.is_virtualized:
            status += f" | Virtualize: {len(snapshot.nodes)}/{snapshot.virtualized_from}"
        self._lbl_status.setText(status)
        self._reload_tag_suggestions()

    def _build_node_positions(self, snapshot: GraphSnapshot) -> dict[int, QPointF]:
        if self._chk_cluster_by_tag.isChecked():
            positions = self._build_cluster_positions(snapshot)
        else:
            positions = self._build_circle_positions(snapshot)

        # Ưu tiên layout đã lưu cục bộ
        for node in snapshot.nodes:
            saved = self._layout_positions.get(str(node.note_id))
            if (
                isinstance(saved, list)
                and len(saved) == 2
                and isinstance(saved[0], (int, float))
                and isinstance(saved[1], (int, float))
            ):
                positions[node.note_id] = QPointF(float(saved[0]), float(saved[1]))
        return positions

    def _build_circle_positions(self, snapshot: GraphSnapshot) -> dict[int, QPointF]:
        node_count = len(snapshot.nodes)
        positions: dict[int, QPointF] = {}
        if node_count == 1:
            positions[snapshot.nodes[0].note_id] = QPointF(0.0, 0.0)
            return positions

        radius = max(180.0, 40.0 * node_count)
        step = (2.0 * math.pi) / node_count
        for idx, node in enumerate(snapshot.nodes):
            angle = idx * step
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions[node.note_id] = QPointF(x, y)
        return positions

    def _build_cluster_positions(self, snapshot: GraphSnapshot) -> dict[int, QPointF]:
        groups: dict[str, list] = defaultdict(list)
        for node in snapshot.nodes:
            key = node.tags[0] if node.tags else "(không tag)"
            groups[key].append(node)

        cluster_keys = sorted(groups.keys())
        cluster_count = len(cluster_keys)
        if cluster_count <= 1:
            return self._build_circle_positions(snapshot)

        cluster_ring_radius = max(220.0, 140.0 * cluster_count)
        positions: dict[int, QPointF] = {}

        for c_idx, key in enumerate(cluster_keys):
            center_angle = (2.0 * math.pi * c_idx) / cluster_count
            cx = cluster_ring_radius * math.cos(center_angle)
            cy = cluster_ring_radius * math.sin(center_angle)

            members = groups[key]
            if len(members) == 1:
                positions[members[0].note_id] = QPointF(cx, cy)
                continue

            local_radius = max(85.0, 28.0 * len(members))
            local_step = (2.0 * math.pi) / len(members)
            for m_idx, node in enumerate(members):
                ang = local_step * m_idx
                x = cx + local_radius * math.cos(ang)
                y = cy + local_radius * math.sin(ang)
                positions[node.note_id] = QPointF(x, y)

        return positions

    def _build_adjacency(self, edges: list[GraphEdge]) -> dict[int, set[int]]:
        adjacency: dict[int, set[int]] = defaultdict(set)
        for edge in edges:
            adjacency[edge.from_note_id].add(edge.to_note_id)
            adjacency[edge.to_note_id].add(edge.from_note_id)
        return dict(adjacency)

    def _on_node_selected(self, note_id: int) -> None:
        self._selected_note_id = note_id
        self._apply_highlight()

    def _on_node_open(self, note_id: int, source_id: int | None) -> None:
        if source_id is not None:
            self.source_open_requested.emit(source_id)
        else:
            self.note_open_requested.emit(note_id)

    def _on_node_move_end(self, note_id: int, scene_pos: QPointF) -> None:
        self._layout_positions[str(note_id)] = [round(scene_pos.x(), 2), round(scene_pos.y(), 2)]
        self._save_layout_positions()

    def _apply_highlight(self) -> None:
        if not self._node_items:
            return

        if self._selected_note_id is None or self._selected_note_id not in self._node_items:
            for item in self._node_items.values():
                item.set_visual_state("normal")
            for edge, edge_item in self._edge_items:
                edge_item.setPen(self._edge_pen(edge, emphasized=False))
                edge_item.setOpacity(0.85)
            return

        hops = int(self._combo_hops.currentData())
        visible_set = self._neighbors_with_depth(self._selected_note_id, hops)

        for note_id, item in self._node_items.items():
            if note_id == self._selected_note_id:
                item.set_visual_state("selected")
            elif note_id in visible_set:
                item.set_visual_state("near")
            else:
                item.set_visual_state("dim")

        for edge, edge_item in self._edge_items:
            endpoints_visible = (
                edge.from_note_id in visible_set and edge.to_note_id in visible_set
            )
            if endpoints_visible:
                edge_item.setPen(self._edge_pen(edge, emphasized=True))
                edge_item.setOpacity(0.95)
            else:
                edge_item.setPen(self._edge_pen(edge, emphasized=False))
                edge_item.setOpacity(0.08)

    def _neighbors_with_depth(self, start_note_id: int, depth: int) -> set[int]:
        visited: set[int] = {start_note_id}
        if depth <= 0:
            return visited

        queue = deque([(start_note_id, 0)])
        while queue:
            node_id, d = queue.popleft()
            if d >= depth:
                continue
            for nxt in self._adjacency.get(node_id, set()):
                if nxt in visited:
                    continue
                visited.add(nxt)
                queue.append((nxt, d + 1))
        return visited

    def _edge_pen(self, edge: GraphEdge, emphasized: bool = False) -> QPen:
        color = QColor("#6B7A99")
        if edge.link_type == "wikilink":
            color = QColor("#4A6CF7")
        elif edge.link_type == "manual":
            color = QColor("#20A39E")

        # Độ dày theo weight: weight=1→1.0px, mỗi +1 thêm 0.5px, tối đa +4px
        weight = getattr(edge, "weight", 1)
        base_width = 1.0 + min((weight - 1) * 0.5, 4.0)
        width = base_width * 1.5 if emphasized else base_width
        return QPen(color, width)

    def _fit_to_scene(self) -> None:
        if self._scene.items():
            rect = self._scene.itemsBoundingRect().adjusted(-24, -24, 24, 24)
            self._canvas.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _on_search_node(self) -> None:
        query = self._edit_search.text().strip().lower()
        if not query:
            return

        target = None
        for node in self._snapshot.nodes:
            haystack = " ".join([node.title or "", node.slug or "", " ".join(node.tags)]).lower()
            if query in haystack:
                target = node
                break

        if target is None:
            self._lbl_status.setText(f"Không tìm thấy node cho từ khóa: {query}")
            return

        self._selected_note_id = target.note_id
        self._apply_highlight()

        item = self._node_items.get(target.note_id)
        if item is not None:
            self._canvas.centerOn(item)

        self._lbl_status.setText(
            f"Đã chọn node: {target.title} (note_id={target.note_id})"
        )

    def _reload_tag_suggestions(self) -> None:
        """Nạp danh sách tag từ TagService vào autocomplete."""
        try:
            from core.services.tag_service import TagService
            tags = sorted({str(t.name) for t in TagService().list_tags()})
            self._tag_completer.setModel(QStringListModel(tags, self._tag_completer))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Không thể nạp tag suggestions cho Graph view: {exc}")

    def _load_layout_positions(self) -> dict[str, list[float]]:
        raw = self._settings.get("graph_layout_positions", {})
        if isinstance(raw, dict):
            return raw
        return {}

    def _restore_virtualize_preferences(self) -> None:
        virtualize_default = bool(self._settings.get("graph_virtualize_default", True))
        max_nodes_default = int(self._settings.get("graph_virtualize_max_nodes", 120))

        self._chk_virtualize.setChecked(virtualize_default)

        idx = self._combo_max_nodes.findData(max_nodes_default)
        self._combo_max_nodes.setCurrentIndex(idx if idx >= 0 else 0)

    def _on_virtualize_pref_changed(self, checked: bool) -> None:
        self._settings.set("graph_virtualize_default", bool(checked))
        self.refresh_graph()

    def _on_max_nodes_pref_changed(self, _index: int) -> None:
        current = int(self._combo_max_nodes.currentData())
        self._settings.set("graph_virtualize_max_nodes", current)
        self.refresh_graph()

    def _save_layout_positions(self) -> None:
        self._settings.set("graph_layout_positions", self._layout_positions)

    def _save_layout_now(self) -> None:
        for note_id, item in self._node_items.items():
            pos = item.scenePos()
            self._layout_positions[str(note_id)] = [round(pos.x(), 2), round(pos.y(), 2)]
        self._save_layout_positions()
        self._lbl_status.setText("Đã lưu layout cục bộ cho Graph view.")

    def _clear_layout_current(self) -> None:
        for node in self._snapshot.nodes:
            self._layout_positions.pop(str(node.note_id), None)
        self._save_layout_positions()
        self._selected_note_id = None
        self.refresh_graph()
        self._lbl_status.setText("Đã xóa layout lưu cho các node đang hiển thị.")
