#!/usr/bin/python3

import sqlite3, csv, argparse, sys
from chromium_constants import CORE_MASK, transition_types, transition_type_descriptions, QUALIFIER_MASK, transition_qualifiers, \
transition_qualifier_descriptions, download_danger_types, download_danger_descriptions, download_interrupt_reason_types, \
download_interrupt_reason_descriptions, download_state_types
from os import environ, remove, path
from shutil import copyfile
from datetime import datetime, timedelta
from pytz import timezone as get_timezone
from pytz import utc
from tzlocal import get_localzone

def chromium_history_to_csv(user=None,curruser=False, sourcedb=None, tempdb=None, outputdir=None, timezone='local'):
    """
    Parses the specified chromium History db to extract download and url history information.
    Defaults to look for chrome's history, but can override with 'sourcedb' param to specify the
    History file for any chromium base browser such as edge, brave, vivaldi, and more
    """
    if user is None and curruser is False and sourcedb is None:
        raise ValueError("Must specify a sourcedb path, explicit user, or curruser flag")
    if "win32" in sys.platform:
        if curruser:
            user = environ['USERNAME']
        if sourcedb is None:
            # Win10/7/vista
            sourcedb = r"C:\users\{0}\AppData\Local\Google\Chrome\User Data\Default\HISTORY".format(user)
            # checking if xp, this is valid in theory not tested
            if not path.exists(sourcedb):
                sourcedb = r"C:\Documents and Settings\{0}\Local Settings\Application Data\Google\Chrome\User Data\Default\HISTORY".format(user)
        if tempdb is None:    
            tempdb = r"c:\users\{0}\AppData\Local\Temp\HISTORY".format(environ['USERNAME'])
        if outputdir is None:
            outputdir = r"{0}\desktop".format(environ['USERPROFILE'])
    else:
        # assumes a nix variant
        if curruser:
            user = environ['USER']
        if sourcedb is None:
            sourcedb = r"/home/{0}/.config/google-chrome/Default/History".format(user)
            if not path.exists(sourcedb):
                sourcedb = r"/home/{0}/.config/chromium/Default/History".format(user)
        if tempdb is None:    
            tempdb = r"/tmp/HISTORY"
        if outputdir is None:
            outputdir = r"/home/{0}/Desktop".format(environ['USER'])
    url_history_csv = r"{0}\{1}chromium_history.csv".format(outputdir,user+"_" if user is not None else '')
    download_history_csv = r"{0}\{1}chromium_download_history.csv".format(outputdir,user+"_" if user is not None else '')
    # get the timezone
    if timezone == 'local':
        tz = get_localzone()
    else:
        tz = get_timezone(timezone)
    # making a copy, sometimes fails when browser has a handle on the file
    copyfile(sourcedb,tempdb)
    url_columns = ["url","title","visit_count","typed_count","last_visit_time","hidden"]#,"visit_time","from_visit","transition"]
    url_derived_columns = ["transition_core","transition_qualifiers","transition_description","qualifiers_description"]
    visit_columns = ["visit_time","from_visit","transition","visit_duration"]
    url_visits_columns = url_columns + visit_columns
    # there's also hash and transient columns, but don't seem to populate
    download_columns = ["current_path","target_path","start_time","received_bytes","total_bytes","state","danger_type","interrupt_reason",
        "end_time","opened","last_access_time","referrer","tab_url","tab_referrer_url","last_modified","mime_type","original_mime_type"]
    download_derived_columns = ["danger desc","interrupt desc"]
    download_all_columns = download_columns + download_derived_columns
    # can join the urls table with the keyword_search_terms table on url.id=keyword_search_terms.url_id, but doesn't really give more info
    # can join the urls table with the segments table on url.id=segments.url_id, but again not much more info
    timeline_query = "SELECT {0}, {1} FROM urls, visits WHERE urls.id = visits.url ORDER BY visits.visit_time DESC;".format(
        ", ".join(["urls."+col for col in url_columns]),", ".join(["visits."+col for col in visit_columns]))
    downloads_query = "SELECT {0} FROM downloads ORDER BY start_time DESC;".format(", ".join(download_columns))
    timeline = list()
    downloads = list()
    db = sqlite3.connect(tempdb)
    cursor = db.cursor()
    cursor.execute(timeline_query)
    timeline_results = cursor.fetchall()
    cursor.execute(downloads_query)
    download_results = cursor.fetchall()
    db.close()
    remove(tempdb)
    for result in timeline_results:
        entry = dict()
        for i in range(len(url_visits_columns)):
            if "time" in url_visits_columns[i] and len(str(result[i])) == 17:
                # this is the time that chromium starts counting from
                converted_time = (datetime(1601,1,1) + timedelta(microseconds=result[i]))
                entry[url_visits_columns[i]] = utc.localize(converted_time,is_dst=None).astimezone(tz).isoformat()
            elif "transition" in url_visits_columns[i]:
                qualifiers = list()
                qualifiers_description = list()
                for _, qmask in enumerate(transition_qualifiers):
                    if ((result[i] & QUALIFIER_MASK) & qmask) != 0:
                        qualifiers.append(transition_qualifiers[qmask])
                        qualifiers_description.append(transition_qualifier_descriptions[qmask])
                entry[url_visits_columns[i]] = result[i]
                entry[url_derived_columns[0]] = transition_types[(result[i] & CORE_MASK)]
                entry[url_derived_columns[1]] = "**|**".join(qualifiers)
                entry[url_derived_columns[2]] = transition_type_descriptions[(result[i] & CORE_MASK)]
                entry[url_derived_columns[3]] = "**|**".join(qualifiers_description)
            else:
                entry[url_visits_columns[i]] = result[i]
        timeline.append(entry)

    for result in download_results:
        entry = dict()
        for i in range(len(download_columns)):
            if "time" in download_columns[i] and len(str(result[i])) == 17:
                converted_time = (datetime(1601,1,1) + timedelta(microseconds=result[i]))
                entry[download_columns[i]] = utc.localize(converted_time,is_dst=None).astimezone(tz).isoformat()
            elif "state" in download_columns[i]:
                entry[download_columns[i]] = download_state_types[result[i]]
            elif "danger_type" in download_columns[i]:
                entry[download_columns[i]] = download_danger_types[result[i]]
                entry[download_derived_columns[0]] = download_danger_descriptions[result[i]]
            elif "interrupt_reason" in download_columns[i] and result[i] != 0:
                entry[download_columns[i]] = download_interrupt_reason_types[result[i]]
                entry[download_derived_columns[1]] = download_interrupt_reason_descriptions[result[i]]
            else:
                entry[download_columns[i]] = result[i]
        downloads.append(entry)

    column_names = url_visits_columns + url_derived_columns
    with open(url_history_csv,"w",encoding="utf-8",newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(timeline)
    
    with open(download_history_csv,"w",encoding="utf-8",newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=download_all_columns)
        writer.writeheader()
        writer.writerows(downloads)
        
def main():
    parser = argparse.ArgumentParser(
        add_help=False,
        description=
        '''Parse and extract url browsing history and download history from any chromium-based browser's'''
        '''user history sqlite db handling constant interpretation and tz conversion.''',
        formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=40)
    )

    parser.add_argument('-u', '--user', type=str, metavar="STRING", default=None, help="The local username to parse chromium browser history for. (default: USERNAME)")
    parser.add_argument('-c', '--curruser', action='store_true', help="Will pull the currently logged in user's chromium history if specified.")
    parser.add_argument('-s', '--sourcedb', type=str, metavar="STRING", default=None, help="Explicit path to the HISTORY sqlite file for chromium-based browser.")
    parser.add_argument('-t', '--tempdb', type=str, metavar="STRING", default=None, help="Explicit path to copy the db to for processing to avoid handle conflicts.")
    parser.add_argument('-o', '--outputdir', type=str, metavar="STRING", default=None, help="Directory to write the output to.")
    parser.add_argument('-z', '--timezone', type=str, metavar="STRING", default="local", help="Timezone to convert to in format COUNTRY/REGION or UTC. (default: local)")
    
    if len(sys.argv) < 2 or sys.argv[1] in ('-h','--help'):
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    chromium_history_to_csv(user=args.user,curruser=args.curruser,sourcedb=args.sourcedb,tempdb=args.tempdb,outputdir=args.outputdir,timezone=args.timezone)
    sys.exit(0)


if __name__ == "__main__":
    main()