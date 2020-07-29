import sqlite3, csv, argparse
from os import environ, remove
from shutil import copyfile
from datetime import datetime, timedelta

# TODO: parse info from downloads table
# TODO: check for os to check non-windows file paths (also chromium offshoots)

def chrome_history_to_csv(user=environ['USERNAME'],sourcedb=None, tempdb=None, outputcsv=None):
    if user is not None:
            sourcedb = r"C:\users\{0}\AppData\Local\Google\Chrome\User Data\Default\HISTORY".format(user)
            tempdb = r"c:\users\{0}\AppData\Local\Temp\HISTORY".format(user)
            outputcsv = r"{0}\desktop\{1}chrome_history.csv".format(environ['USERPROFILE'],(user + "_"))
    else:
        if sourcedb is None:
            sourcedb = r"{0}\AppData\Local\Google\Chrome\User Data\Default\HISTORY".format(environ['USERPROFILE'])
        if tempdb is None:
            tempdb = r"{0}\AppData\Local\Temp\HISTORY".format(environ['USERPROFILE'])
        if outputcsv is None:
            outputcsv = r"{0}\desktop\{1}chrome_history.csv".format(environ['USERPROFILE'],(environ['USERNAME'] + "_"))
    # currently, all times in UTC
    # this will be used to extract the core transition types
    CORE_MASK = 0xFF
    # constants and descriptions from the below
    # https://chromium.googlesource.com/chromium/+/trunk/content/public/common/page_transition_types.h
    transition_types = {
        0:"PAGE_TRANSITION_LINK",
        1:"PAGE_TRANSITION_TYPED",
        2:"PAGE_TRANSITION_AUTO_BOOKMARK",
        3:"PAGE_TRANSITION_AUTO_SUBFRAME",
        4:"PAGE_TRANSITION_MANUAL_SUBFRAME",
        5:"PAGE_TRANSITION_GENERATED",
        6:"PAGE_TRANSITION_AUTO_TOPLEVEL",
        7:"PAGE_TRANSITION_FORM_SUBMIT",
        8:"PAGE_TRANSITION_RELOAD",
        9:"PAGE_TRANSITION_KEYWORD",
        10:"PAGE_TRANSITION_KEYWORD_GENERATED"
    }
    transition_type_descriptions = {
        0:"User got to this page by clicking a link on another page.",
        1:"User got this page by typing the URL in the URL bar.",
        2:"User got to this page through a suggestion in the UI, for example, through the destinations page.",
        3:"This is a subframe navigation. This is any content that is automatically\
    loaded in a non-toplevel frame. For example, if a page consists of\
    several frames containing ads, those ad URLs will have this transition\
    type. The user may not even realize the content in these pages is a\
    separate frame, so may not care about the URL",
        4:"For subframe navigations that are explicitly requested by the user and\
    generate new navigation entries in the back/forward list.",
        5:"User got to this page by typing in the URL bar and selecting an entry\
    that did not look like a URL.  For example, a match might have the URL\
    of a Google search result page, but appear like 'Search Google for ...'.\
    These are not quite the same as TYPED navigations because the user\
    didn't type or see the destination URL.",
        6:"This is a toplevel navigation. This is any content that is automatically\
    loaded in a toplevel frame.  For example, opening a tab to show the ASH\
    screen saver, opening the devtools window, opening the NTP after the safe\
    browsing warning, opening web-based dialog boxes",
        7:"The user filled out values in a form and submitted it. NOTE that in\
    some situations submitting a form does not result in this transition\
    type. This can happen if the form uses script to submit the contents.",
        8:"The user 'reloaded' the page, either by hitting the reload button or by hitting enter in the address bar.",
        9:"The url was generated from a replaceable keyword other than the default\
    search provider. If the user types a keyword (which also applies to\
    tab-to-search) in the omnibox this qualifier is applied to the transition\
    type of the generated url.",
        10:"Corresponds to a visit generated for a keyword."
    }
    QUALIFIER_MASK = 0xFFFFFF00
    transition_qualifiers = {
        0x01000000:"PAGE_TRANSITION_FORWARD_BACK",
        0x02000000:"PAGE_TRANSITION_FROM_ADDRESS_BAR",
        0x04000000:"PAGE_TRANSITION_HOME_PAGE",
        0x10000000:"PAGE_TRANSITION_CHAIN_START",
        0x20000000:"PAGE_TRANSITION_CHAIN_END",
        0x40000000:"PAGE_TRANSITION_CLIENT_REDIRECT",
        0x80000000:"PAGE_TRANSITION_SERVER_REDIRECT",
        0xC0000000:"PAGE_TRANSITION_IS_REDIRECT_MASK"
    }
    transition_qualifier_descriptions = {
        0x01000000:"User used the Forward or Back button to navigate among browsing history.",
        0x02000000:"User used the address bar to trigger this navigation.",
        0x04000000:"User is navigating to the home page.",
        0x10000000:"The beginning of a navigation chain.",
        0x20000000:"The last transition in a redirect chain.",
        0x40000000:"Redirects caused by JavaScript or a meta refresh tag on the page.",
        0x80000000:"Redirects sent from the server by HTTP headers.",
        0xC0000000:"Used to test whether a transition involves a redirect."
    }
    derived_columns = ["transition_core","transition_qualifiers","transition_description","qualifiers_description"]
    # making a copy, sometimes fails when chrome has a handle on the file
    copyfile(sourcedb,tempdb)
    timeline_columns = ["url","title","visit_count","typed_count","last_visit_time","hidden","visit_time","from_visit","transition"]
    timeline_query = "SELECT urls.url, urls.title, urls.visit_count, urls.typed_count, urls.last_visit_time, urls.hidden, \
    visits.visit_time, visits.from_visit, visits.transition FROM urls, visits WHERE urls.id = visits.url ORDER BY visits.visit_time;"
    timeline = list()
    db = sqlite3.connect(tempdb)
    cursor = db.cursor()
    cursor.execute(timeline_query)
    timeline_results = cursor.fetchall()
    db.close()
    remove(tempdb)
    for result in timeline_results:
        entry = dict()
        for i in range(len(timeline_columns)):
            if "time" in timeline_columns[i]:
                # this is the time that chrome starts counting from
                entry[timeline_columns[i]] = (datetime(1601,1,1) + timedelta(microseconds=result[i])).isoformat()
            elif "transition" in timeline_columns[i]:
                qualifiers = list()
                qualifiers_description = list()
                for _, qmask in enumerate(transition_qualifiers):
                    if ((result[i] & QUALIFIER_MASK) & qmask) != 0:
                        qualifiers.append(transition_qualifiers[qmask])
                        qualifiers_description.append(transition_qualifier_descriptions[qmask])
                entry[timeline_columns[i]] = result[i]
                entry[derived_columns[0]] = transition_types[(result[i] & CORE_MASK)]
                entry[derived_columns[1]] = "**|**".join(qualifiers)
                entry[derived_columns[2]] = transition_type_descriptions[(result[i] & CORE_MASK)]
                entry[derived_columns[3]] = "**|**".join(qualifiers_description)
            else:
                entry[timeline_columns[i]] = result[i]
        timeline.append(entry)

    column_names = timeline_columns + derived_columns
    with open(outputcsv,"w",encoding="utf-8",newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(timeline)
        
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--user', type=str, metavar="STRING", default=environ['USERNAME'], help="The local username to parse chrom history for. (default: %USERNAME%)")
    parser.add_argument('-s', '--sourcedb', type=str, metavar="STRING", default=None, help="Explicit path to the HISTORY sqlite file for chrome.")
    parser.add_argument('-t', '--tempdb', type=str, metavar="STRING", default=None, help="Explicit path to copy the db to for processing to avoid handle conflicts.")
    parser.add_argument('-o', '--outputcsv', type=str, metavar="STRING", default=None, help="Explicit path to write the output to.")
    args = parser.parse_args()
    chrome_history_to_csv(user=args.user,sourcedb=args.sourcedb,tempdb=args.tempdb,outputcsv=args.outputcsv)

if __name__ == "__main__":
    main()