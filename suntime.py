__filename__ = "sunrise.py"
__author__ = "Bob Mottram"
__credits__ = ["Krzysztof Stopa", "Andrey Kobyshev",
               "Matthias", "Hadrien Bertrand"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Environment Simulation"

# see https://github.com/SatAgro/suntime

import calendar
import math
import datetime
from dateutil import tz

TO_RAD = math.pi/180.0


class SunTimeException(Exception):

    def __init__(self, message):
        super(SunTimeException, self).__init__(message)


class Sun:
    """
    Approximated calculation of sunrise and sunset datetimes. Adapted from:
    https://stackoverflow.com/questions/19615350/
    calculate-sunrise-and-sunset-times-for-a-given-gps-coordinate-
    within-postgresql
    """
    def __init__(self, lat, lon):
        self._lat = lat
        self._lon = lon

    def get_local_sunrise_time(self, date=None, local_time_zone=tz.tzlocal()):
        """
        Get sunrise time for local or custom time zone.
        :param date: Reference date. Today if not provided.
        :param local_time_zone: Local or custom time zone.
        :return: Local time zone sunrise datetime
        """
        date = datetime.date.today() if date is None else date
        sr1 = self._calc_sun_time(date, True)
        if sr1 is None:
            raise SunTimeException('The sun never rises on this location ' +
                                   '(on the specified date)')
        return sr1.astimezone(local_time_zone)

    def get_local_sunset_time(self, date=None, local_time_zone=tz.tzlocal()):
        """
        Get sunset time for local or custom time zone.
        :param date: Reference date
        :param local_time_zone: Local or custom time zone.
        :return: Local time zone sunset datetime
        """
        date = datetime.date.today() if date is None else date
        ss1 = self._calc_sun_time(date, False)
        if ss1 is None:
            raise SunTimeException('The sun never sets on this location ' +
                                   '(on the specified date)')
        return ss1.astimezone(local_time_zone)

    def _calc_sun_time(self, date, is_rise_time=True, zenith=90.8):
        """
        Calculate sunrise or sunset date.
        :param date: Reference date
        :param is_rise_time: True if you want to calculate sunrise time.
        :param zenith: Sun reference zenith
        :return: UTC sunset or sunrise datetime
        :raises: SunTimeException when there is no sunrise and sunset
        on given location and date
        """
        # is_rise_time == False, returns sunsetTime
        day = date.day
        month = date.month
        year = date.year

        # 1. first calculate the day of the year
        num1 = math.floor(275 * month / 9)
        num2 = math.floor((month + 9) / 12)
        num3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
        num = num1 - (num2 * num3) + day - 30

        # 2. convert the longitude to hour value and calculate
        # an approximate time
        lng_hour = self._lon / 15

        if is_rise_time:
            tim = num + ((6 - lng_hour) / 24)
        else:
            # sunset
            tim = num + ((18 - lng_hour) / 24)

        # 3. calculate the Sun's mean anomaly
        mean_anom = (0.9856 * tim) - 3.289

        # 4. calculate the Sun's true longitude
        true_long = mean_anom + (1.916 * math.sin(TO_RAD*mean_anom)) + \
            (0.020 * math.sin(TO_RAD * 2 * mean_anom)) + 282.634
        true_long = self._force_range(true_long, 360)

        # 5a. calculate the Sun's right ascension

        ras = (1/TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD * true_long))
        ras = self._force_range(ras, 360)

        # 5b. right ascension value needs to be in the same quadrant as L
        lquadrant = (math.floor(true_long / 90)) * 90
        ra_quadrant = (math.floor(ras / 90)) * 90
        ras = ras + (lquadrant - ra_quadrant)

        # 5c. right ascension value needs to be converted into hours
        ras = ras / 15

        # 6. calculate the Sun's declination
        sin_dec = 0.39782 * math.sin(TO_RAD * true_long)
        cos_dec = math.cos(math.asin(sin_dec))

        # 7a. calculate the Sun's local hour angle
        cosh = \
            (math.cos(TO_RAD * zenith) -
             (sin_dec * math.sin(TO_RAD * self._lat))) / \
            (cos_dec * math.cos(TO_RAD * self._lat))

        if cosh > 1:
            # The sun never rises on this location (on the specified date)
            return None
        if cosh < -1:
            # The sun never sets on this location (on the specified date)
            return None

        # 7b. finish calculating H and convert into hours

        if is_rise_time:
            hval = 360 - (1 / TO_RAD) * math.acos(cosh)
        else:
            # setting
            hval = (1 / TO_RAD) * math.acos(cosh)

        hval = hval / 15

        # 8. calculate local mean time of rising/setting
        mean_time = hval + ras - (0.06571 * tim) - 6.622

        # 9. adjust back to UTC
        utc = mean_time - lng_hour
        # UTC time in decimal format (e.g. 23.23)
        utc = self._force_range(utc, 24)

        # 10. Return
        ut_int = int(utc)
        hrs = self._force_range(ut_int, 24)
        minv = round((utc - ut_int) * 60, 0)
        if minv == 60:
            hrs += 1
            minv = 0

        # 10. check corner case https://github.com/SatAgro/suntime/issues/1
        if hrs == 24:
            hrs = 0
            day += 1

            if day > calendar.monthrange(year, month)[1]:
                day = 1
                month += 1

                if month > 12:
                    month = 1
                    year += 1

        return datetime.datetime(year, month, day, hrs,
                                 int(minv), tzinfo=tz.tzutc())

    @staticmethod
    def _force_range(value, max):
        # force v to be >= 0 and < max
        if value < 0:
            return value + max
        if value >= max:
            return value - max

        return value
