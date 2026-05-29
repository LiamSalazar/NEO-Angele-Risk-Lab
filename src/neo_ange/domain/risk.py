"""Risk score and explanation domain entities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

COMPONENT_FIELDS = [
    "physical_risk_component",
    "orbital_risk_component",
    "approach_risk_component",
    "sentry_risk_component",
    "uncertainty_risk_component",
    "data_quality_component",
]


@dataclass(slots=True)
class RiskScore:
    """Experimental risk-priority score and component breakdown."""

    object_key: str
    risk_score: float | None = None
    risk_score_0_100: float | None = None
    risk_category: str | None = None
    physical_risk_component: float | None = None
    orbital_risk_component: float | None = None
    approach_risk_component: float | None = None
    sentry_risk_component: float | None = None
    uncertainty_risk_component: float | None = None
    data_quality_component: float | None = None
    score_version: str | None = None
    scored_at_utc: str | None = None

    def component_breakdown(self) -> dict[str, float | None]:
        """Return score components keyed by component column name."""
        return {field_name: getattr(self, field_name) for field_name in COMPONENT_FIELDS}

    def dominant_components(self, top_n: int = 3) -> list[dict[str, Any]]:
        """Return the largest non-null score components."""
        components = [
            {"component": name, "value": float(value)}
            for name, value in self.component_breakdown().items()
            if value is not None
        ]
        components.sort(key=lambda item: item["value"], reverse=True)
        return components[: max(top_n, 0)]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class RiskExplanation:
    """Human and technical explanation of an experimental score."""

    object_key: str
    risk_score_0_100: float | None = None
    risk_category: str | None = None
    main_drivers: list[dict[str, Any]] = field(default_factory=list)
    protective_factors: list[dict[str, Any]] = field(default_factory=list)
    data_limitations: list[str] = field(default_factory=list)
    short_explanation: str | None = None
    technical_explanation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def as_markdown(self) -> str:
        """Render a compact markdown explanation for reports."""
        lines = [
            f"# Risk explanation: {self.object_key}",
            "",
            f"Score: {self.risk_score_0_100}",
            f"Category: {self.risk_category}",
            "",
            self.short_explanation or "",
            "",
            "## Main drivers",
        ]
        if self.main_drivers:
            lines.extend(
                f"- {item.get('factor', item.get('component', 'driver'))}: " f"{item.get('value')}"
                for item in self.main_drivers
            )
        else:
            lines.append("- No dominant driver found in the available data.")
        lines.append("")
        lines.append("## Protective factors")
        if self.protective_factors:
            lines.extend(
                f"- {item.get('factor', item.get('component', 'factor'))}: "
                f"{item.get('interpretation', item.get('value'))}"
                for item in self.protective_factors
            )
        else:
            lines.append("- No explicit protective factors identified.")
        lines.append("")
        lines.append("## Data limitations")
        if self.data_limitations:
            lines.extend(f"- {limitation}" for limitation in self.data_limitations)
        else:
            lines.append("- No major limitations detected by the explanation service.")
        if self.technical_explanation:
            lines.extend(["", "## Technical note", self.technical_explanation])
        return "\n".join(lines).strip() + "\n"
