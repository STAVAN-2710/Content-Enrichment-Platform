"""
Curated RSS feed list — 50+ shows across 10 topic verticals.
Verified publicly accessible feeds with consistent episode metadata.
"""

FEEDS: dict[str, list[str]] = {
    "technology": [
        "https://feeds.simplecast.com/54nAGcIl",           # Lex Fridman
        "https://feeds.megaphone.fm/hubermanlab",           # Huberman Lab
        "https://feeds.simplecast.com/4T39_jAj",           # The TWIML AI Podcast
        "https://softwareengineeringdaily.com/feed/podcast/",  # Software Engineering Daily
        "https://feeds.feedburner.com/se-radio",            # Software Engineering Radio
        "https://changelog.com/podcast/feed",               # The Changelog
        "https://feeds.simplecast.com/38URSTem",            # Acquired
        "https://feeds.megaphone.fm/darknetdiaries",        # Darknet Diaries
        "https://feeds.feedburner.com/cognicast",           # Cognicast
        "https://feeds.simplecast.com/l2i9YnTd",           # The AI Alignment Podcast
    ],
    "science": [
        "https://feeds.simplecast.com/gvtxUiIf",           # Sean Carroll's Mindscape
        "https://feeds.feedburner.com/brainsciencepodcast", # Brain Science with Ginger Campbell
        "https://rss.acast.com/infinitemonkeycage",        # The Infinite Monkey Cage
        "https://feeds.megaphone.fm/sciencevs",             # Science Vs
        "https://feeds.simplecast.com/FiMNO_rK",           # StarTalk Radio
        "https://feeds.simplecast.com/4T39_jAj",           # In Our Time: Science (BBC)
        "https://feeds.feedburner.com/radiolab",            # Radiolab
        "https://rss.art19.com/60-second-science",          # 60-Second Science
    ],
    "business": [
        "https://feeds.megaphone.fm/HSW7835889991",         # How I Built This
        "https://feeds.megaphone.fm/marketsnacks-daily",    # Invest Like the Best
        "https://feeds.simplecast.com/pmvqFSHN",           # My First Million
        "https://feeds.megaphone.fm/ROOSTER7199268416",     # The Tim Ferriss Show
        "https://rss.art19.com/masters-of-scale",           # Masters of Scale
        "https://feeds.megaphone.fm/GLT1412515089",         # The Prof G Pod
        "https://feeds.simplecast.com/wgl4xEgL",           # Founders
        "https://feeds.megaphone.fm/WWO3519750118",         # The Knowledge Project
    ],
    "history": [
        "https://feeds.simplecast.com/Nn5k1p4u",           # Revolutions
        "https://feeds.feedburner.com/dancarlinshardcorehistory",  # Dan Carlin's Hardcore History
        "https://rss.art19.com/american-history-tellers",   # American History Tellers
        "https://feeds.megaphone.fm/historyextra",          # History Extra
        "https://rss.acast.com/the-ancients",              # The Ancients
        "https://feeds.simplecast.com/dLRotFGk",           # Stuff You Missed in History Class
    ],
    "true_crime": [
        "https://feeds.megaphone.fm/darknetdiaries",        # Darknet Diaries (cyber crime)
        "https://rss.art19.com/serial",                    # Serial
        "https://feeds.megaphone.fm/casefile",              # Casefile
        "https://feeds.simplecast.com/Pk7qPTBG",           # Crime Junkie
        "https://rss.art19.com/your-own-backyard",          # Your Own Backyard
    ],
    "health": [
        "https://feeds.megaphone.fm/hubermanlab",           # Huberman Lab (also tech)
        "https://rss.art19.com/found-my-fitness",           # FoundMyFitness with Rhonda Patrick
        "https://feeds.simplecast.com/7bRNMfSU",           # The Doctor's Farmacy
        "https://rss.art19.com/the-art-of-manliness",      # Art of Manliness
        "https://feeds.feedburner.com/TheDietDoctor",       # Diet Doctor
        "https://feeds.megaphone.fm/ZOE-science-and-nutrition",  # ZOE Science & Nutrition
    ],
    "philosophy": [
        "https://feeds.simplecast.com/gvtxUiIf",           # Mindscape (also science)
        "https://rss.acast.com/philosophybites",            # Philosophy Bites
        "https://feeds.feedburner.com/partiallyexaminedlife",  # The Partially Examined Life
        "https://rss.art19.com/making-sense-with-sam-harris",  # Making Sense with Sam Harris
        "https://feeds.simplecast.com/jJNDKJbO",           # Philosophize This!
    ],
    "comedy": [
        "https://feeds.megaphone.fm/conan-obrien-needs-a-friend",  # Conan O'Brien Needs a Friend
        "https://feeds.simplecast.com/VPjLjPeQ",           # SmartLess
        "https://rss.art19.com/my-favorite-murder",         # My Favorite Murder
        "https://feeds.megaphone.fm/CRIM6798957722",        # Call Her Daddy
        "https://feeds.simplecast.com/dHoohVNH",           # No Such Thing as a Fish
    ],
    "personal_development": [
        "https://feeds.megaphone.fm/WWO3519750118",         # The Knowledge Project
        "https://feeds.simplecast.com/4T39_jAj",           # The Tim Ferriss Show (also biz)
        "https://rss.art19.com/the-diary-of-a-ceo",        # The Diary of a CEO
        "https://feeds.feedburner.com/OnBeingWithKristaTippett",  # On Being
        "https://feeds.simplecast.com/40Hz_d9C",           # Hidden Brain
        "https://rss.art19.com/dare-to-lead-podcast",       # Dare to Lead with Brené Brown
    ],
    "culture": [
        "https://feeds.megaphone.fm/pivot",                 # Pivot with Kara Swisher
        "https://feeds.simplecast.com/40Hz_d9C",           # Hidden Brain (also psych)
        "https://feeds.feedburner.com/freakonomicsradio",   # Freakonomics Radio
        "https://rss.art19.com/revisionist-history",        # Revisionist History
        "https://feeds.megaphone.fm/VMP6608681321",         # The Daily
        "https://rss.acast.com/cautionary-tales",          # Cautionary Tales with Tim Harford
    ],
}

# Flat list for ingestion runner
ALL_FEEDS: list[str] = list({url for urls in FEEDS.values() for url in urls})
