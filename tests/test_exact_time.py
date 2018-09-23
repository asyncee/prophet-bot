import datetime as dt

import pytest

from exact_time import extractor

cases = [
    (
        dt.datetime(2018, 1, 1, 12, 0),
        [
            (
                "послать презентацию завтра в 10 утра",
                "завтра в 10 утра",
                dt.datetime(2018, 1, 2, 10, 0),
            ),
            ("завтра в 15 в налоговую", "завтра в 15", dt.datetime(2018, 1, 2, 15, 0)),
            ("в налоговую в 15 завтра утром", "в 15 завтра утром", dt.datetime(2018, 1, 2, 15, 0)),
            ("в налоговую завтра в 15", "завтра в 15", dt.datetime(2018, 1, 2, 15, 0)),
            ("завтра в 10 оплатить услуги", "завтра в 10", dt.datetime(2018, 1, 2, 10, 0)),
            ("в среду в 11:15 в налоговую", "в среду в 11:15", dt.datetime(2018, 1, 3, 11, 15)),
            ("напомни постирать в 20:15", "в 20:15", dt.datetime(2018, 1, 1, 20, 15)),
            ("напомни погладить в 10", "в 10", dt.datetime(2018, 1, 1, 22, 0)),
            (
                "подготовиться к мероприятию в субботу вечером",
                "в субботу вечером",
                dt.datetime(2018, 1, 6, 19, 0),
            ),
            (
                "подготовиться к мероприятию в понедельник в 20:00",
                "в понедельник в 20:00",
                dt.datetime(2018, 1, 8, 20, 0),
            ),
            (
                "подготовиться к мероприятию завтра в 20:00",
                "завтра в 20:00",
                dt.datetime(2018, 1, 2, 20, 0),
            ),
            ("в 8 вечера доделать работу", "в 8 вечера", dt.datetime(2018, 1, 1, 20, 0)),
            ("23 мая в 15-10 на почту", "23 мая в 15-10", dt.datetime(2019, 5, 23, 15, 10)),
            (
                "17.04.2018 в 9 поздравить коллегу с днем рождения",
                "17.04.2018 в 9",
                dt.datetime(2018, 4, 17, 9, 0),
            ),
            ("во вторник сходить к врачу", "во вторник", dt.datetime(2018, 1, 2, 9, 0)),
            ("электричка в 6 вечера", "в 6 вечера", dt.datetime(2018, 1, 1, 18, 0)),
            ("электричка в 6 утра", "в 6 утра", dt.datetime(2018, 1, 2, 6, 0)),
            ("электричка в 2 ночи", "в 2 ночи", dt.datetime(2018, 1, 2, 2, 0)),
            ("электричка в 2 дня", "в 2 дня", dt.datetime(2018, 1, 1, 14, 0)),
            (
                "завтра в 10 утра накормить кошку",
                "завтра в 10 утра",
                dt.datetime(2018, 1, 2, 10, 0),
            ),
            ("сходить в магазин вечером", "вечером", dt.datetime(2018, 1, 1, 19, 0)),
            (
                "сходить в магазин сегодня вечером",
                "сегодня вечером",
                dt.datetime(2018, 1, 1, 19, 0),
            ),
            ("сходить в магазин завтра днём", "завтра днём", dt.datetime(2018, 1, 2, 14, 0)),
            ("Покушать в воскресенье", "в воскресенье", dt.datetime(2018, 1, 7, 9, 0)),
            (
                "напомни проснуться завтра утром в 10:35",
                "завтра утром в 10:35",
                dt.datetime(2018, 1, 2, 10, 35),
            ),
            ("поесть с утра", "с утра", dt.datetime(2018, 1, 2, 9, 0)),
            ("поесть с вечера", "с вечера", dt.datetime(2018, 1, 1, 19, 0)),
            ("поесть с 11 утра", "с 11 утра", dt.datetime(2018, 1, 2, 11, 0)),
            ("напомни проснуться завтра с утра", "завтра с утра", dt.datetime(2018, 1, 2, 9, 0)),
            ("напомни завтра с утра проснуться", "завтра с утра", dt.datetime(2018, 1, 2, 9, 0)),
            ("напомни проснуться завтра утром", "завтра утром", dt.datetime(2018, 1, 2, 9, 0)),

            ("завтра в налоговую в 10 часов", "завтра в 10 часов", dt.datetime(2018, 1, 2, 10, 0)),
            ("в субботу в налоговую в 10 часов", "в субботу в 10 часов", dt.datetime(2018, 1, 6, 10, 0)),
        ],
    )
]


# Dynamically generate test functions for each test time.
for test_time, cases in cases:

    @pytest.mark.parametrize("case, case_time, moment", cases)
    def f(case, case_time, moment):
        extract = extractor(case, moment=test_time)
        print('\n', extract.match.fact)
        assert extract is not None

        assert moment == extract.time
        assert case_time == extract.time_string

    globals()[f"test_cases_{test_time.isoformat()}"] = f
