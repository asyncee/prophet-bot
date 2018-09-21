import datetime as dt
import enum
from collections import namedtuple

from dateutil import rrule
from yargy import rule, and_, or_, Parser
from yargy.interpretation import fact
from yargy.predicates import gte, lte, normalized, dictionary, caseless

Hour = fact("Hour", ["hour"])  # get_time
Minute = fact("Minute", ["minute"])  # get_time
HourAndMinute = fact("HourAndMinute", ["hour", "minute"])  # get_time
Time = fact("Time", ["time"])  # get_time
TimeOfDay = fact("TimeOfDay", ["time"])  # get_time
AtTime = fact("AtTime", ["time", "time_of_day", "day"])
Date = fact("Date", ["year", "month", "day"])
DayName = fact("DayName", ["name"])


def to_int(value):
    if value is None:
        return
    return int(value)


class Hour(Hour):
    def get_time(self):
        return dt.time(self.hour, 0)


class Minute(Minute):
    def get_time(self):
        return dt.time(9, self.minute)  # default TODO: 9 to constants


class HourAndMinute(HourAndMinute):
    def get_time(self):
        return dt.time(self.hour.hour, self.minute.minute)


class Time(Time):
    def get_time(self):
        return self.time.get_time()


class Date(Date):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.year:
            self.year = dt.datetime.today().year + 1

    def get_date(self, current):
        return dt.date(
            self.year or current.year, self.month or current.month, self.day or current.day
        )


class AtTime(AtTime):
    def get_datetime(self, current) -> dt.datetime:
        time = self.default_time()
        date = current.date()

        if self.time:
            time = self.time.get_time()

        if self.day:
            date = self.day.get_date(current)

        time = self.prepare_time(time)

        return self.postprocess(current, self.combine(date, time))

    def postprocess(self, current, result):
        if current >= result:
            if (current - result).seconds < 60 * 60 * 24:

                shifted_result = result.replace(hour=hours_map_after[result.hour])

                # No time of day, try to shift hour (until next day maximum).
                if self.time_of_day is None and shifted_result > current:
                    return shifted_result

                # Time of day specified and it contains shifted hour.
                elif self.time_of_day.contains(shifted_result.hour):
                    return shifted_result

                # Shift one day forward.
                else:
                    return result + dt.timedelta(days=1)

        return result

    def combine(self, date, time):
        return dt.datetime.combine(date, time)

    def prepare_time(self, time):
        if self.time_of_day:
            time = time.replace(hour=self.time_of_day.prepare_hour(time.hour))
        return time

    def default_time(self):
        if self.time_of_day:
            return self.time_of_day.default_time()
        return dt.time(9, 0)


MONTHS = {
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}

# TODO: map to DayEnum directly instead of custom func
DAYS = {
    "понедельник": 1,
    "вторник": 2,
    "среда": 3,
    "четверг": 4,
    "пятница": 5,
    "суббота": 6,
    "воскресенье": 7,
    "воскресение": 7,
    "завтра": 8,
    "послезавтра": 9,
    "сегодня": 10,
}

hours_map_after = {
    1: 13,
    2: 14,
    3: 15,
    4: 16,
    5: 17,
    6: 18,
    7: 19,
    8: 20,
    9: 21,
    10: 22,
    11: 23,
    12: 0,
}


class TimeOfDayEnum(enum.Enum):
    MORNING = (4, 12)
    DAY = (12, 18)
    EVENING = (18, 24)
    NIGHT = (0, 4)

    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def contains(self, hour):
        return self.start <= hour < self.stop

    def before(self, hour):
        """Return True if current time of day before hour."""
        return self.stop <= hour

    def after(self, hour):
        """Return True if current time of day after hour."""
        return self.start >= hour

    def prepare_hour(self, hour):
        # 2 утра -> 02:00, 16 утра -> 16:00
        # 10 дня -> 10:00, 20 дня -> 20:00
        # 10 вечера -> 22:00, 2 вечера -> 2:00
        # 22 ночи -> 22:00, 10 ночи -> 22:00

        if self.contains(hour):
            return hour

        if self == self.MORNING:
            return hour

        if self == self.DAY:
            return hours_map_after[hour]

        if self == self.EVENING:
            if self.after(hour):
                return hours_map_after[hour]

            if self.before(hour):
                return hour

        if self == self.NIGHT:
            if self.after(hour):
                return hour

            if self.before(hour):
                return hours_map_after[hour]

        raise NotImplementedError

    def default_time(self) -> dt.time:
        if self == self.MORNING:
            return dt.time(9, 0)

        if self == self.DAY:
            return dt.time(14, 0)

        if self == self.EVENING:
            return dt.time(19, 0)

        if self == self.NIGHT:
            return dt.time(0, 0)

        raise NotImplementedError

    @classmethod
    def find(cls, hour) -> "TimeOfDayEnum":
        for tod in cls:
            if tod.contains(hour):
                return tod
        raise ValueError(f'Invalid hour: "{hour}"')


class DayEnum(enum.IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    TOMORROW = 8
    DAY_AFTER_TOMORROW = 9
    TODAY = 10

    def get_date(self, current):
        # Day of week
        if self.value <= self.SUNDAY:
            r_rule = iter(
                rrule.rrule(
                    rrule.DAILY, dtstart=current, byweekday=rrule.weekdays[self.value - 1], count=2
                )
            )
            next_date = next(r_rule)

            if next_date.date() == current.date():
                return next(r_rule)

            return next_date

        if self.value == self.TOMORROW:
            return current + dt.timedelta(days=1)

        if self.value == self.DAY_AFTER_TOMORROW:
            return current + dt.timedelta(days=2)

        if self.value == self.TODAY:
            return current

        raise NotImplementedError


TIMES_OF_DAY = {
    "утро": TimeOfDayEnum.MORNING,
    "утром": TimeOfDayEnum.MORNING,
    "день": TimeOfDayEnum.DAY,
    "днём": TimeOfDayEnum.DAY,
    "вечер": TimeOfDayEnum.EVENING,
    "вечером": TimeOfDayEnum.EVENING,
    "ночь": TimeOfDayEnum.NIGHT,
    "ночью": TimeOfDayEnum.NIGHT,
}


def time_of_day(value):
    if value is None:
        return
    return TIMES_OF_DAY[value]


def day(value):
    if value is None:
        return
    return DayEnum(DAYS[value])


# time
HOUR_WORD = rule(normalized("час"))
HOUR = rule(
    and_(gte(1), lte(24)).interpretation(Hour.hour.custom(to_int)), HOUR_WORD.optional()
).interpretation(Hour)

MINUTE_WORD = rule(normalized("минута"))
MINUTE = rule(
    and_(gte(0), lte(59)).interpretation(Minute.minute.custom(to_int)), MINUTE_WORD.optional()
).interpretation(Minute)

HOUR_MINUTE_SEPARATOR = or_(rule(":"), rule(" "), rule("-"))
DATE_SEPARATOR = or_(rule("-"), rule("."), rule("/"))

HOUR_AND_MINUTE = rule(
    HOUR.interpretation(HourAndMinute.hour),
    HOUR_MINUTE_SEPARATOR.optional(),
    MINUTE.interpretation(HourAndMinute.minute),
).interpretation(HourAndMinute)

TIME = or_(
    HOUR_AND_MINUTE.interpretation(Time.time),
    HOUR.interpretation(Time.time),
    MINUTE.interpretation(Time.time),
).interpretation(Time)

# date
DAY = or_(rule(and_(gte(1), lte(31)))).interpretation(Date.day.custom(to_int))
MONTH = and_(gte(1), lte(12)).interpretation(Date.month.custom(to_int))
YEAR = and_(gte(1), lte(2099)).interpretation(Date.year.custom(to_int))
YEAR_WORDS = or_(rule(caseless("г"), "."), rule(normalized("год")))
MONTH_NAME = dictionary(MONTHS).interpretation(Date.month.normalized().custom(MONTHS.__getitem__))
DATE = or_(
    rule(YEAR, DATE_SEPARATOR, MONTH, DATE_SEPARATOR, DAY),
    rule(DAY, DATE_SEPARATOR, MONTH_NAME, DATE_SEPARATOR, YEAR.optional(), YEAR_WORDS.optional()),
    rule(DAY, DATE_SEPARATOR, MONTH, DATE_SEPARATOR, YEAR.optional(), YEAR_WORDS.optional()),
    rule(DAY, MONTH_NAME, YEAR.optional(), YEAR_WORDS.optional()),
).interpretation(Date)

DAYNAME = dictionary(DAYS).interpretation(DayName.name.normalized().custom(day))

AT = or_(rule("в"), rule("во"))
AT_TIME_OF_DAY = dictionary(TIMES_OF_DAY).interpretation(
    TimeOfDay.time.normalized().custom(time_of_day)
)
EXACT_TIME = or_(
    # в (день) в время (время дня)
    # в понедельник в 10 утра
    # завтра в 11
    rule(
        AT.optional(),
        DAYNAME.interpretation(AtTime.day),
        AT,
        TIME.interpretation(AtTime.time),
        AT_TIME_OF_DAY.optional().interpretation(AtTime.time_of_day),
    ),
    # в время день (время дня)
    # в 10 завтра утром
    # в 10 завтра
    rule(
        AT,
        TIME.interpretation(AtTime.time),
        DAYNAME.optional().interpretation(AtTime.day),
        AT_TIME_OF_DAY.optional().interpretation(AtTime.time_of_day),
    ),
    # в день (время дня)
    # в субботу утром
    rule(
        AT,
        DAYNAME.interpretation(AtTime.day),
        AT_TIME_OF_DAY.optional().interpretation(AtTime.time_of_day),
    ),
    # дата в время (время дня)
    # 17.04.2018 в 9
    rule(
        DATE.interpretation(AtTime.day),
        AT,
        TIME.interpretation(AtTime.time),
        AT_TIME_OF_DAY.optional().interpretation(AtTime.time_of_day),
    ),
    # ... вечером
    # сходить в магазин вечером
    rule(
        DAYNAME.optional().interpretation(AtTime.day),
        AT_TIME_OF_DAY.interpretation(AtTime.time_of_day),
    ),
).interpretation(AtTime)


parser = Parser(EXACT_TIME)


Extract = namedtuple("Extract", "time, task, time_string, fact")


def extractor(string, moment=None) -> Extract:
    moment = moment or dt.datetime.now()

    matches = list(parser.findall(string))
    if not matches:
        return

    match = matches[0]

    time = match.fact.get_datetime(moment)
    task = (string[: match.span.start] + string[match.span.stop :]).strip()
    time_string = string[match.span.start : match.span.stop]
    return Extract(time, task, time_string, match.fact)


# print("---dates---")
# parser = Parser(DATE)
#
# for case in ["18.12.2018"]:
#     print(">>>", case)
#     matches = list(parser.findall(case))
#     if not matches:
#         print("!! no matches")
#
#     for match in matches:
#         print(match.fact)
