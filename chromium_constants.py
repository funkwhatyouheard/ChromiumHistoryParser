#!/usr/bin/python

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
# constants from components/download/public/common/download_danger_type.h
# https://source.chromium.org/chromium/chromium/src/+/master:components/download/public/common/download_danger_type.h?originalUrl=https:%2F%2Fcs.chromium.org%2F
download_danger_types = {
    0:"DOWNLOAD_DANGER_TYPE_NOT_DANGEROUS",
    1:"DOWNLOAD_DANGER_DANGEROUS_FILE",
    2:"DOWNLOAD_DANGER_DANGEROUS_URL",
    3:"DOWNLOAD_DANGER_TYPE_DANGEROUS_CONTENT",
    4:"DOWNLOAD_DANGER_TYPE_MAYBE_DANGEROUS_CONTENT",
    5:"DOWNLOAD_DANGER_TYPE_UNCOMMON_CONTENT",
    6:"DOWNLOAD_DANGER_TYPE_USER_VALIDATED",
    7:"DOWNLOAD_DANGER_TYPE_DANGEROUS_HOST",
    8:"DOWNLOAD_DANGER_TYPE_POTENTIALLY_UNWANTED",
    9:"DOWNLOAD_DANGER_TYPE_WHITELISTED_BY_POLICY",
    10:"DOWNLOAD_DANGER_TYPE_ASYNC_SCANNING",
    11:"DOWNLOAD_DANGER_TYPE_BLOCKED_PASSWORD_PROTECTED",
    12:"DOWNLOAD_DANGER_TYPE_BLOCKED_TOO_LARGE",
    13:"DOWNLOAD_DANGER_TYPE_SENSITIVE_CONTENT_WARNING",
    14:"DOWNLOAD_DANGER_TYPE_SENSITIVE_CONTENT_BLOCK",
    15:"DOWNLOAD_DANGER_TYPE_DEEP_SCANNED_SAFE",
    16:"DOWNLOAD_DANGER_TYPE_DEEP_SCANNED_OPENED_DANGEROUS",
    17:"DOWNLOAD_DANGER_TYPE_PROMPT_FOR_SCANNING",
    18:"DOWNLOAD_DANGER_TYPE_BLOCKED_UNSUPPORTED_FILETYPE"
}
download_danger_descriptions = {
    0:"The download is safe.",
    1:"A dangerous file to the system (e.g.: a pdf or extension from places other than gallery).",
    2:"Safebrowsing download service shows this URL leads to malicious file download.",
    3:"SafeBrowsing download service shows this file content as being malicious.",
    4:"The content of this download may be malicious (e.g., extension is exe but SafeBrowsing has not finished checking the content).",
    5:"SafeBrowsing download service checked the contents of the download, but didn't have enough data to determine whether it was malicious.",
    6:"The download was evaluated to be one of the other types of danger, but the user told us to go ahead anyway.",
    7:"SafeBrowsing download service checked the contents of the download and didn't have data on this specific file, but the file was served\
from a host known to serve mostly malicious content.",
    8:"Applications and extensions that modify browser and/or computer settings",
    9:"Download URL whitelisted by enterprise policy.",
    10:"Download is pending a more detailed verdict.",
    11:"Download is password protected, and should be blocked according to policy.",
    12:"Download is too large, and should be blocked according to policy. See the BlockLargeFileTransfer policy for details.",
    13:"Download deep scanning identified sensitive content, and recommended warning the user.",
    14:"Download deep scanning identified sensitive content, and recommended blocking the file.",
    15:"Download deep scanning identified no problems.",
    16:"Download deep scanning identified a problem, but the file has already been opened by the user.",
    17:"The user is enrolled in the Advanced Protection Program, and the server has recommended this file be deep scanned.",
    18:"The download has a file type that is unsupported for deep scanning, and should be blocked according to policy. See\
the BlockUnsupportedFiletypes policy for details."
}
# constants from components/download/public/common/download_interrupt_reason_values.h
# https://source.chromium.org/chromium/chromium/src/+/master:components/download/public/common/download_interrupt_reason_values.h;bpv=0;bpt=1?originalUrl=https:%2F%2Fcs.chromium.org%2F
download_interrupt_reason_types = {
    1:"FILE_FAILED",
    2:"FILE_ACCESS_DENIED",
    3:"FILE_NO_SPACE",
    5:"FILE_NAME_TOO_LONG",
    6:"FILE_TOO_LARGE",
    7:"FILE_VIRUS_INFECTED",
    10:"FILE_TRANSIENT_ERROR",
    11:"FILE_BLOCKED",
    12:"FILE_SECURITY_CHECK_FAILED",
    13:"FILE_TOO_SHORT",
    14:"FILE_HASH_MISMATCH",
    15:"FILE_SAME_AS_SOURCE",
    20:"NETWORK_FAILED",
    21:"NETWORK_TIMEOUT",
    22:"NETWORK_DISCONNECTED",
    23:"NETWORK_SERVER_DOWN",
    24:"NETWORK_INVALID_REQUEST",
    30:"SERVER_FAILED",
    31:"SERVER_NO_RANGE",
    33:"SERVER_BAD_CONTENT",
    34:"SERVER_UNAUTHORIZED",
    35:"SERVER_CERT_PROBLEM",
    36:"SERVER_FORBIDDEN",
    37:"SERVER_UNREACHABLE",
    38:"SERVER_CONTENT_LENGTH_MISMATCH",
    39:"SERVER_CROSS_ORIGIN_REDIRECT",
    40:"USER_CANCELED",
    41:"USER_SHUTDOWN",
    50:"CRASH"
}
download_interrupt_reason_descriptions = {
    1:"Generic file operation failure.",
    2:"The file cannot be accessed due to security restrictions.",
    3:"There is not enough room on the drive.",
    5:"The directory or file name is too long.",
    6:"The file is too large for the file system to handle.",
    7:"The file contains a virus",
    10:"The file was in use.; Too many files are opened at once.; We have run out of memory.",
    11:"The file was blocked due to local policy.",
    12:"An attempt to check the safety of the download failed due to unexpected reasons. See http://crbug.com/153212",
    13:"An attempt was made to seek past the end of a file in openin a file (as part of resuming a previously interrupted download).",
    14:"The partial file didn't match the expected hash.",
    15:"The source and the target of the download were the same.",
    20:"Generic network failure.",
    21:"The network operation timed out.",
    22:"The network connection has been lost.",
    23:"The server has gone down.",
    24:"The network request was invalid. This may be due to the original URL or a redirected URL having an unsupported scheme, being \
an invalid URL or being disallowed by policy.",
    30:"The server indicates that the operation has failed (generic).",
    31:"The server does not support range requests.",
    33:"The server does not have the requested data.",
    34:"Server didn't authorize access to resource.",
    35:"Server certificate problem.",
    36:"Server access forbidden.",
    37:"Unexpected server response. This might indicate that the responding server may not be the intended server.",
    38:"The server sent fewer bytes than the content-length header.",
    39:"An unexpected cross-origin redirect happened.",
    40:"The user canceled the download.",
    41:"The user shut down the browser.",
    50:"The browser crashed."
}
# should be defined here... components/download/public/common/download_item.h
# https://source.chromium.org/chromium/chromium/src/+/master:components/download/public/common/download_item.h;bpv=0;bpt=1?originalUrl=https:%2F%2Fcs.chromium.org%2F 
# testing/guessing on these
download_state_types = {
    0:"IN_PROGRESS",
    1:"COMPLETE",
    2:"CANCELLED",
    3:"INTERRUPTED"
}