## Configuration

Holidays node server has following configuration parameters, all of which are lists, separated by ";":

* Include Holidays - List of holidays you want to be treated as days off. When empty, this parameter will include all holidays.
* Exclude Holidays - list of holidays you want to exclude (that is, your normal business day).
* Weekend - initially set to "Saturday" and "Sunday". Change it if your normal weekend days are different.
* Rules - rules are described below.

### Rules

Rules are a list, each item consisting of *description* and *date string*.
For instance:
* My Wife's Birthday
* every May 15

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
