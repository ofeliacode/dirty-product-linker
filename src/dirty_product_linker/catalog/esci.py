"""Pure transformations for Amazon ESCI query-product judgments."""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal, cast

from dirty_product_linker.schemas import EsciLabel, QueryProductJudgment

SOURCE_ID = "milistu/amazon-esci-data"
SOURCE_REVISION = "3bf15ee2b5c6483fc3b96f8656d0989bf33a18b5"


class EsciRecordRejected(ValueError):
    """A source row that violates the documented ESCI contract."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class EsciImportResult:
    """Converted judgments plus auditable rejection counts."""

    read: int
    judgments: tuple[QueryProductJudgment, ...]
    rejection_reasons: dict[str, int]

    @property
    def accepted(self) -> int:
        return len(self.judgments)

    @property
    def rejected(self) -> int:
        return self.read - self.accepted


def _required_string(record: Mapping[str, object], field: str, reason: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EsciRecordRejected(reason)
    return value.strip()


def _required_int(record: Mapping[str, object], field: str, reason: str) -> int:
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EsciRecordRejected(reason)
    return value


def convert_esci_record(record: Mapping[str, object]) -> QueryProductJudgment:
    """Convert one raw ESCI query row while retaining its official split."""

    locale = _required_string(record, "product_locale", "invalid_locale").casefold()
    if locale not in {"us", "es", "jp"}:
        raise EsciRecordRejected("invalid_locale")

    split = _required_string(record, "split", "invalid_split").casefold()
    if split not in {"train", "test"}:
        raise EsciRecordRejected("invalid_split")

    try:
        label = EsciLabel(
            _required_string(record, "esci_label", "invalid_label").upper()
        )
    except ValueError as error:
        raise EsciRecordRejected("invalid_label") from error

    return QueryProductJudgment(
        source_example_id=_required_int(record, "example_id", "invalid_example_id"),
        source_query_id=_required_int(record, "query_id", "invalid_query_id"),
        query=_required_string(record, "query", "missing_query"),
        source_product_id=_required_string(record, "product_id", "missing_product_id"),
        locale=cast(Literal["us", "es", "jp"], locale),
        label=label,
        source_split=cast(Literal["train", "test"], split),
        source_revision=SOURCE_REVISION,
    )


def import_esci_records(
    records: Iterable[Mapping[str, object]],
) -> EsciImportResult:
    """Convert ESCI rows and count every rejected row by stable reason."""

    judgments: list[QueryProductJudgment] = []
    rejection_reasons: Counter[str] = Counter()
    read = 0

    for record in records:
        read += 1
        try:
            judgments.append(convert_esci_record(record))
        except EsciRecordRejected as error:
            rejection_reasons[error.reason] += 1

    return EsciImportResult(
        read=read,
        judgments=tuple(judgments),
        rejection_reasons=dict(sorted(rejection_reasons.items())),
    )
