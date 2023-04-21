from __future__ import annotations

__all__ = [
    "DateAttribute",
    "DurationAttribute",
    "RelativeDateAttribute",
    "RelativeDateDirection",
]

import dataclasses
from enum import Enum
from typing import Any, Dict, Optional
from typing_extensions import Self

from medkit.core import Attribute, dict_conv


@dataclasses.dataclass
class DateAttribute(Attribute):
    """
    Attribute representing an absolute date or time associated to a segment or
    entity.

    The date or time can be incomplete: each date/time component is optional but
    at least one must be provided.

    Attributes
    ----------
    uid:
        Identifier of the attribute
    label:
        Label of the attribute
    year:
        Year component of the date
    month:
        Month component of the date
    day:
        Day component of the date
    hour:
        Hour component of the time
    minute:
        Minute component of the time
    second:
        Second component of the time
    metadata:
        Metadata of the attribute
    """

    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    hour: Optional[int]
    minute: Optional[int]
    second: Optional[int]

    def __init__(
        self,
        label: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        super().__init__(label=label, metadata=metadata, uid=uid)

        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    def to_brat(self) -> str:
        return self.format()

    def to_spacy(self) -> str:
        return self.format()

    def format(self) -> str:
        """
        Return a string representation of the date with
        format YYYY-MM-DD for the date part and HH:MM:SS for the time part, if
        present. Missing components are replaced with question marks
        """

        formatted = ""
        if self.year is not None or self.month is not None or self.day is not None:
            if self.year is not None:
                formatted += f"{self.year:04}"
            else:
                formatted += "????"

            if self.month is not None:
                formatted += f"-{self.month:02}"
            else:
                formatted += "-??"

            if self.day is not None:
                formatted += f"-{self.day:02}"
            else:
                formatted += "-??"

        if self.hour is not None or self.minute is not None or self.second is not None:
            if formatted:
                formatted += " "
            if self.hour is not None:
                formatted += f"{self.hour:02}"
            else:
                formatted += "??"
            if self.minute is not None:
                formatted += f":{self.minute:02}"
            else:
                formatted += ":??"
            if self.second is not None:
                formatted += f"{self.second:02}"
            else:
                formatted += ":??"

        return formatted

    def to_dict(self) -> Dict[str, Any]:
        date_dict = dict(
            uid=self.uid,
            label=self.label,
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            second=self.seconds,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, date_dict)
        return date_dict

    @classmethod
    def from_dict(cls, date_dict: Dict[str, Any]) -> Self:
        return cls(
            uid=date_dict["uid"],
            label=date_dict["label"],
            year=date_dict["year"],
            month=date_dict["month"],
            day=date_dict["day"],
            hour=date_dict["hour"],
            minute=date_dict["minute"],
            second=date_dict["second"],
            metadata=date_dict["metadata"],
        )


@dataclasses.dataclass
class DurationAttribute(Attribute):
    """
    Attribute representing a time quantity associated to a segment or entity.

    Each date/time component is optional but at least one must be provided.

    Attributes
    ----------
    uid:
        Identifier of the attribute
    label:
        Label of the attribute
    direction:
        Direction the relative date. Ex: "2 years ago" correspond to the `PAST`
        direction and "in 2 weeks" to the `FUTURE` direction.
    years:
        Year component of the date quantity
    months:
        Month component of the date quantity
    weeks:
        Week component of the date quantity
    days:
        Day component of the date quantity
    hours:
        Hour component of the time quantity
    minutes:
        Minute component of the time quantity
    seconds:
        Second component of the time quantity
    metadata:
        Metadata of the attribute
    """

    years: int
    months: int
    weeks: int
    days: int
    hours: int
    minutes: int
    seconds: int

    def __init__(
        self,
        label: str,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        super().__init__(label=label, metadata=metadata, uid=uid)

        self.years = years
        self.months = months
        self.weeks = weeks
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def to_brat(self) -> str:
        return self.format()

    def to_spacy(self) -> str:
        return self.format()

    def format(self) -> str:
        """
        Return a string representation of the date/time offset.

        Ex: "1 year 10 months 2 days"
        """

        parts = []
        if self.years:
            parts.append(str(self.years) + " year" if self.years == 1 else " years")
        if self.months:
            parts.append(str(self.months) + " month" if self.months == 1 else " months")
        if self.weeks:
            parts.append(str(self.weeks) + " week" if self.weeks == 1 else " weeks")
        if self.days:
            parts.append(str(self.days) + " day" if self.days == 1 else " days")
        if self.hours:
            parts.append(str(self.hours) + " hour" if self.hours == 1 else " hours")
        if self.minutes:
            parts.append(
                str(self.minutes) + " minute" if self.minutes == 1 else " minutes"
            )
        if self.seconds:
            parts.append(
                str(self.seconds) + " second" if self.seconds == 1 else " seconds"
            )

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        duration_dict = dict(
            uid=self.uid,
            label=self.label,
            years=self.years,
            months=self.months,
            weeks=self.weeks,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, duration_dict)
        return duration_dict

    @classmethod
    def from_dict(cls, duration_dict: Dict[str, Any]) -> Self:
        return cls(
            uid=duration_dict["uid"],
            label=duration_dict["label"],
            years=duration_dict["years"],
            months=duration_dict["months"],
            weeks=duration_dict["weeks"],
            days=duration_dict["days"],
            hours=duration_dict["hours"],
            minutes=duration_dict["minutes"],
            seconds=duration_dict["seconds"],
            metadata=duration_dict["metadata"],
        )


class RelativeDateDirection(Enum):
    """Direction of a :class:`~.RelativeDateAttribute`"""

    PAST = "past"
    FUTURE = "future"


@dataclasses.dataclass
class RelativeDateAttribute(DurationAttribute):
    """
    Attribute representing a relative date or time associated to a segment or
    entity, ie a date/time offset from an (unknown) reference date/time, with a
    direction.

    At least one date/time component must be non-zero.

    Attributes
    ----------
    uid:
        Identifier of the attribute
    label:
        Label of the attribute
    direction:
        Direction the relative date. Ex: "2 years ago" corresponds to the `PAST`
        direction and "in 2 weeks" to the `FUTURE` direction.
    years:
        Year component of the date offset
    months:
        Month component of the date offset
    weeks:
        Week component of the date offset
    days:
        Day component of the date offset
    hours:
        Hour component of the time offset
    minutes:
        Minute component of the time offset
    seconds:
        Second component of the time offset
    metadata:
        Metadata of the attribute
    """

    direction: RelativeDateDirection
    years: int
    months: int
    weeks: int
    days: int
    hours: int
    minutes: int
    seconds: int

    def __init__(
        self,
        label: str,
        direction: RelativeDateDirection,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        super().__init__(
            label=label,
            years=years,
            months=months,
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            metadata=metadata,
            uid=uid,
        )

        self.direction = direction

    def format(self) -> str:
        """
        Return a string representation of the date/time offset
        Ex: "+ 1 year 10 months 2 days"
        """

        prefix = "+ " if self.direction is RelativeDateDirection.FUTURE else "- "
        return prefix + super().format()

    def to_brat(self):
        return self.format()

    def to_spacy(self):
        return self.format()

    def to_dict(self) -> Dict[str, Any]:
        date_dict = dict(
            uid=self.uid,
            label=self.label,
            direction=self.direction.value,
            years=self.years,
            months=self.months,
            weeks=self.weeks,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            metadata=self.metadata,
        )
        dict_conv.add_class_name_to_data_dict(self, date_dict)
        return date_dict

    @classmethod
    def from_dict(cls, date_dict: Dict[str, Any]) -> Self:
        return cls(
            uid=date_dict["uid"],
            label=date_dict["label"],
            direction=RelativeDateDirection(date_dict["direction"]),
            years=date_dict["years"],
            months=date_dict["months"],
            weeks=date_dict["weeks"],
            days=date_dict["days"],
            hours=date_dict["hours"],
            minutes=date_dict["minutes"],
            seconds=date_dict["seconds"],
            metadata=date_dict["metadata"],
        )
