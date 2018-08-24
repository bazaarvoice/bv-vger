from __future__ import division
import datetime
import time

class TimeIntervalCalculator(object):
    def __init__(self, dateUntil, dateSince, days):
        today = datetime.datetime.today()
        # if both query parameters are provided
        if (dateSince and dateUntil):
            if (dateSince > dateUntil):
                # This is an error! Raise exception.
                # Caller should handle exception appropriately
                raise ValueError('Given dateSince:{} is later than dateUntil:{}'.format(dateSince, dateUntil))
            # convert string into datetime
            dateSince = datetime.datetime.strptime(dateSince, '%Y-%m-%d')
            dateUntil = datetime.datetime.strptime(dateUntil, '%Y-%m-%d')
        else :
            days = int(days) if days else 90
            if dateUntil:
                dateUntil = datetime.datetime.strptime(dateUntil, '%Y-%m-%d')
                # If dateUntil specified later than today
                if (dateUntil > today):
                    dateUntil = today
                # If only dateUntil is given, calculate dateSince
                dateSince = dateUntil - datetime.timedelta(days)
            elif dateSince:
                dateSince = datetime.datetime.strptime(dateSince, '%Y-%m-%d')
                # If only dateSince is given, calculate dateUntil
                dateUntil = dateSince + datetime.timedelta(days)
            else:
                # If neither dateUntil nor dateSince parameters specified,
                # set dateUntil to today,
                # set dateSince to days prior to dateUntil
                dateUntil = today
                dateSince = dateUntil - datetime.timedelta(days)

        # Adjust dateSince to earliest Monday within the specified time interval
        self.dateSince = self.next_weekday(dateSince,0)

        # If dateUntil specified later than today
        if (dateUntil > today):
            dateUntil = today

        # Round dateUntil to previous Sunday Midnight
        self.dateUntil = dateUntil - datetime.timedelta(days=dateUntil.weekday())

    def decrementDateSinceWeeks(self, dateSinceWeekSetback=0):
        # Decrement dateSince by dateSinceWeekSetback
        self.dateSince = self.dateSince - datetime.timedelta(weeks=dateSinceWeekSetback)

    def next_weekday(self, initialDate, weekday):
        days_ahead = weekday - initialDate.weekday()
        if days_ahead < 0: # Target day already happened this week
            days_ahead += 7
        returnDate = initialDate + datetime.timedelta(days=days_ahead)
        return returnDate

    def getDateUntil(self):
        return self.dateUntil.replace(hour=0,minute=0,second=0, microsecond=0)

    def getDateSince(self):
        return self.dateSince.replace(hour=0,minute=0,second=0, microsecond=0)

    def getDateUntilInt(self):
        return time.mktime(self.getDateUntil().timetuple())

    def getDateSinceInt(self):
        return time.mktime(self.getDateSince().timetuple())

    @staticmethod
    def weekend_converter(d):
        if d.weekday() == 5:
            d += datetime.timedelta(days=1)
        return d.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def workday_diff(start, end):
        weekend = [5, 6]  # Monday is 0
        both_weekend = end.weekday() in weekend and start.weekday() in weekend
        is_weekend = end.weekday() in weekend or start.weekday() in weekend
        if start.weekday() in weekend:
            start = TimeIntervalCalculator.weekend_converter(start)
        if end.weekday() in weekend:
            end = TimeIntervalCalculator.weekend_converter(end)
        total_weekend_days = ((end - start).days // 7) * 2 + is_weekend - both_weekend
        if start.weekday() > end.weekday() and not is_weekend:
            total_weekend_days += 2

        workday_diff_delta = datetime.timedelta(seconds=(end - start).total_seconds()) - datetime.timedelta(total_weekend_days)
        return workday_diff_delta.days + workday_diff_delta.seconds / 86400
