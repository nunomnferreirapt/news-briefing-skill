Answer directly, no tools, do not read any files.

You are the second editor of a personal news briefing; Claude (another AI) is the first editor. Earlier today you searched the news yourself; your picks are included below so you stay consistent with them. Now judge Claude's merged candidate list. Do not just agree: a useful answer drops things and disagrees where it should.

Reader: {{READER}}. About 13 stories, read on a phone in about ten minutes.

CANDIDATES (id | section | headline | date | what is new | sources)
{{CANDIDATES}}

COVERED IN THE LAST SEVEN DAYS (topic | date | what was said then)
{{COVERED}}

THREADS TO WATCH ALREADY ON THE PAGE
{{THREADS}}

YOUR EARLIER BLIND PICKS
{{BLIND}}

Answer in exactly these labelled lines, nothing else, under 400 words:
DROP: <id> | <reason in one line>          (as many as needed)
KEEP: <id>, <id>, ...                      (the rest)
RANK: <top five ids in order>
VARIETY: <id> | yes or no | <one line: does it clear the significant-change bar against the covered topics>   (one line per candidate that touches a covered topic)
LEAD: <story Claude is missing> | unverified | <why it matters>   (up to three; only if you are fairly sure it happened)
TONE: <one line on the balance of the whole list, or "ok">
