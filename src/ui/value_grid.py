from typing import Optional, Dict, Union
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

Number = Union[int, float]


class ValueGrid:
    def __init__(
        self,
        precision: int = 2,
        default_unit: str = "",
        units: Optional[Dict[str, str]] = None,
        per_key_precision: Optional[Dict[str, int]] = None,
        max_number_chars: int = 8,  # NEW: maximum number of characters before ellipsizing/scientific notation
    ) -> None:
        self.data_grid: Optional[QWidget] = None
        self.telemetry_data: Dict[str, Optional[str | Number]] = {
            "A0": 0.0,
            "A1": 0.0,
            "A2": 0.0,
            "B0": 0.0,
            "B1": 0.0,
            "B2": 0.0,
            "C0": 0.0,
            "C1": 0.0,
            "C2": 0.0,
        }
        self._labels: Dict[str, QLabel] = {}

        self.precision = int(precision)
        self.default_unit = default_unit
        self.units = units.copy() if units else {}
        self.per_key_precision = per_key_precision.copy() if per_key_precision else {}
        self.max_number_chars = int(max_number_chars)  # NEW

    def set_precision(self, precision: int) -> None:
        self.precision = int(precision)
        self._refresh_all_labels()

    def set_precision_for_key(self, key: str, precision: int) -> None:
        self.per_key_precision[key] = int(precision)
        self._refresh_label(key)

    def set_default_unit(self, unit: str) -> None:
        self.default_unit = unit
        self._refresh_all_labels()

    def set_unit_for_key(self, key: str, unit: str) -> None:
        self.units[key] = unit
        self._refresh_label(key)

    def set_units(self, units: Dict[str, str]) -> None:
        self.units = units.copy()
        self._refresh_all_labels()

    def set_max_number_chars(self, n: int) -> None:
        self.max_number_chars = int(n)
        self._refresh_all_labels()

    def _get_precision_for_key(self, key: str) -> int:
        return int(self.per_key_precision.get(key, self.precision))

    def _get_unit_for_key(self, key: str) -> str:
        return self.units.get(key, self.default_unit)

    def _shorten_number_text(
        self, raw_text: str, numeric_value: Optional[Number], precision: int
    ) -> str:
        if numeric_value is not None:
            try:
                val = float(numeric_value)
                abs_val = abs(val)

                if (abs_val != 0.0) and (
                    abs_val >= 10 ** (self.max_number_chars)
                    or abs_val < 10 ** -(precision + 2)
                ):
                    return f"{val:.{precision}e}"
            except Exception:
                pass

        if len(raw_text) > self.max_number_chars:
            cut = max(1, self.max_number_chars - 3)
            return raw_text[:cut] + "..."
        return raw_text

    def _format_value_html(self, key: str, value: Optional[Number]) -> str:
        if value is None:
            number_text = "-"
            unit_text = ""
            numeric_value = None
        else:
            p = self._get_precision_for_key(key)
            numeric_value = None
            try:
                numeric_value = float(value)
                number_text = f"{numeric_value:.{p}f}"
            except (TypeError, ValueError):
                number_text = str(value)

            unit_text = self._get_unit_for_key(key) or ""

        number_text = self._shorten_number_text(
            number_text, numeric_value, self._get_precision_for_key(key)
        )

        html = (
            f"<div style='text-align:center;'>"
            f"  <div style='font-size:32px; font-weight:700; line-height:1;'>{number_text}</div>"
            f"  <div style='font-size:14px; color:rgba(0,0,0,0.55); margin-top:4px;'>{unit_text}</div>"
            f"</div>"
        )
        return html

    def setup_gps_graph(self) -> QWidget:
        self.data_grid = QWidget()
        self.data_grid.setMinimumHeight(420)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        cols = [
            ["A0", "A1", "A2"],
            ["B0", "B1", "B2"],
            ["C0", "C1", "C2"],
        ]

        base_font = QFont("Arial", 10, QFont.Weight.Bold)

        for col_index, col_keys in enumerate(cols):
            for row_index, key in enumerate(col_keys):
                label = QLabel()
                label.setFont(base_font)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setFixedHeight(140)
                label.setFixedWidth(140)
                label.setTextFormat(Qt.TextFormat.RichText)  # allow HTML

                label.setWordWrap(True)
                label.setSizePolicy(
                    QSizePolicy.Policy.MinimumExpanding,
                    QSizePolicy.Policy.MinimumExpanding,
                )

                val = self.telemetry_data.get(key) or 0.0
                label.setText(self._format_value_html(key, val))

                grid_layout.addWidget(label, row_index, col_index)
                self._labels[key] = label

        # make rows/columns expand evenly
        for r in range(3):
            grid_layout.setRowStretch(r, 1)
        for c in range(3):
            grid_layout.setColumnStretch(c, 1)

        self.data_grid.setLayout(grid_layout)
        return self.data_grid

    def update_telemetry(self, key: str, value: Optional[str | Number]) -> None:
        if key not in self.telemetry_data:
            return

        self.telemetry_data[key] = value if value is not None else 0.0
        self._refresh_label(key)

    def _refresh_label(self, key: str) -> None:
        label = self._labels.get(key)
        if label:
            val = (
                self.telemetry_data.get(key)
                if self.telemetry_data.get(key) is not None
                else 0.0
            )
            label.setText(self._format_value_html(key, val))

    def _refresh_all_labels(self) -> None:
        for key in list(self._labels.keys()):
            self._refresh_label(key)
