## Configuration

Holidays node server has following configuration parameters, all of which are lists, separated by ";":

* includeHolidays - initially it is set to list of all known holidays. You can leave it as is, or clear it. When empty, this parameter will include all holidays.
* excludeHolidays - list of holidays you want to exclude (that is, your normal business day).
* weekend - initially set to "Saturday" and "Sunday". Change it if your normal weekend days are different.
* rules - rules are described below.

### Rules

Rules are ";" list, each consisting of `<date string>=<description>`. For instance:
*every December 1st=My Birthday;every May 15=My Wife's Birthday*

*IMPORTANT* to keep in mind, that these holidays created via rules are treated as normal holidays in include / exclude logic. So if you left include list explicit (default) and not empty, you need to add these as well. If your include list is empty, you don't need to do anything.

Date string can the the following:

* `<absolute date>` - this can be full date or partial date. If you don't specify a year, however, the year will be guessed and won't necessarily be what you expect.
* `every <weekday or partial date>`
* `every <weekday or partial date> from <date>`
* `every <weekday or partial date> to <date>`
* `every <weekday or partial date> from <date> to <date>`
* `every <nth> of the month`
* `every <nth> of the month from <date>`
* `every <nth> of the month to <date>`
* `every <nth> of the month from <date> to <date>`
