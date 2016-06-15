#!/usr/bin/python
"""Usage:
    check-consul-health.py node NODE DC
        [--addr=ADDR]
        [--CheckID=CheckID | --ServiceName=ServiceName]
        [--nagios-output]
        [--verbose]

Arguments:
    NODE  the consul node_name
    DC    the consul datacenter

Options:
    -h --help                  show this
    -v --verbose               verbose output
    -n --nagios-output         use Nagios plugin output (only useful when checking one service)
    --addr=ADDR                consul address [default: http://localhost:8500]
    --CheckID=CheckID          CheckID matcher
    --ServiceName=ServiceName  ServiceName matcher
"""

from docopt import docopt
import requests
import json
import traceback
import exceptions


def dump(it):
    if arguments['--verbose']:
        print it


def buildNodeUrl():
    url = "%(--addr)s/v1/health/node/%(NODE)s?dc=%(DC)s" % arguments
    dump("Url: " + url)
    return url


def getJsonFromUrl(url):
    r = requests.get(url)
    dump("Response: " + r.text)
    dump("Status code: " + str(r.status_code))
    r.raise_for_status()
    return r.json()


def printCheck(check):
    print "> %(Node)s:%(ServiceName)s:%(Name)s:%(CheckID)s:%(Status)s" % check


def printNagiosCheck(state, check):
    if len(check) == 1:
        print "%s" % (check[0]['Output'])


def processFailing(checks):
    filters = map(lambda field:
                  lambda x: arguments['--' + field] is None or x[field] == arguments['--'+field],
                  ['CheckID', 'ServiceName']
                  )

    filtered = filter(lambda x: all(f(x) for f in filters), checks)
    passing = filter(lambda x: x['Status'] == 'passing', filtered)
    warning = filter(lambda x: x['Status'] == 'warning', filtered)
    critical = filter(lambda x: x['Status'] == 'critical', filtered)

    if len(checks) == 0:
        print "There is no matching node!"
        return 1

    if len(filtered) == 0:
        print "There is no matching check!"
        return 1

    checkOutput = lambda x: x["Name"] + ":" + x["Output"]

    if arguments['--nagios-output']:
        if len(critical):
            printNagiosCheck("CRITICAL", critical)
        elif len(warning):
            printNagiosCheck("WARNING", warning)
        else:
            printNagiosCheck("OK", passing)
    if len(critical):
        print "|".join(map(checkOutput, critical))
        for check in critical:
            printCheck(check)
    if len(warning):
        print "|".join(map(checkOutput, warning))
        for check in warning:
            printCheck(check)
    if len(passing):
        print "Passing: %d" % (len(passing))
        for check in passing:
            printCheck(check)

    return 2 if len(critical) else 1 if len(warning) else 0


if __name__ == '__main__':
    try:
        arguments = docopt(__doc__)
        dump("Arguments: " + str(arguments))
        if arguments['node']:
            url = buildNodeUrl()
            json = getJsonFromUrl(url)
            exit(processFailing(json))
    except exceptions.SystemExit:
        raise
    except:
        traceback.print_exc()
        exit(3)
