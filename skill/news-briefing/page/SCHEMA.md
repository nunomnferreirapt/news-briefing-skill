# Edition file format

One JSON file per edition, `state/editions/YYYY-MM-DD.json` (a second edition on the same day adds `-2`). The skill writes it; `build.py` turns it into the page. No images inside: `build.py` fetches thumbnails at build time and publishes them as files beside the page. A `second_log` key (free form: each check's verdicts and whether Claude followed them) is kept in the file and not shown on the page.

```jsonc
{
  "edition": "2026-11-24",                 // id; also the key for the page's saved taps
  "learn": true,                           // false only for an edition that should not teach preferences (a design preview)
  "title": "News briefing, Tuesday 24 Nov 2026",
  "masthead": "Briefing · Amsterdam",      // from settings.md: the small line above the title
  "reader": "a reader in Amsterdam who follows ...",   // from settings.md: one line, used by the page's chat
  "second_editor": "Mistral",              // from settings.md: the second model's name, or null when none is set
  "covers": "Mon 23 Nov noon to Tue 24 Nov morning",
  "compiled": "2026-11-24T08:10:00+01:00",
  "read_minutes": 6,
  "lead": ["story-id", "story-id", "story-id"],   // the front page: [0] is the lead with the large photo, [1] and [2] the two seconds
  "big_picture": "Two or three sentences: the pattern across today's stories.",
  "sections": [
    {
      "id": "world",                       // the section ids from settings.md; the page colors the first four in order
      "name": "World",
      "stories": [ /* Story, see below; about 8 in the whole edition, 2 or 3 per section */ ],
      "briefs": [                          // one-liners; at most 5 in the whole edition
        { "text": "...", "sources": [{ "name": "NOS", "url": "https://..." }], "basis": "read" }  // basis: read | digest | headline
      ]
    }
  ],
  // only on the local section, beside stories and briefs:
  //   "rankings": [ { "name": "...", "publisher": "...", "date": "12 Nov", "summary": "Top names, and any company on the reader's watch list with its rank", "url": "https://..." } ],
  //   "events":   [ { "date": "Thu 3 Dec", "name": "...", "venue": "B. Amsterdam", "who": "founders and operators", "price": "free", "url": "https://..." } ],
  "long_view": {                           // one analysis piece per edition; see "The long view" in SKILL.md
    "question": "The question it answers",
    "title": "A headline that states the argument",
    "standfirst": "One or two sentences: the answer in short.",
    "read_minutes": 3,
    "body": ["Paragraph.", "Paragraph."],  // Claude's argument, 400 to 600 words; every fact from the evidence pack
    "claim": "The call that could prove wrong, with a date.",
    "agree": ["Where Claude and the second editor agree, one line each"],
    "second": { "position": "The second editor's final position in its own words, 60 words at most", "exchange": "two or three sentences: what each conceded and what is left between them", "settle": "what would settle the difference" },
    "earlier_call": null,                  // or "On 23 Nov this column said ... It held / did not hold."
    "reading": [ { "title": "...", "author": "...", "outlet": "Bruegel", "url": "https://...", "note": "what it argues, one line" } ],
    "draws_on": ["Headline of an earlier story (23 Nov)"],
    "tags": ["eu-politics", "long-view"]
  },
  "next_questions": [ { "id": "q1", "question": "...", "why": "one line on why now" } ],   // two or three; the reader may pick one on the page
  "threads": [ { "when": "Wed 25 Nov", "what": "..." } ],
  "deeper": [ "A question the reader could ask in a chat", "..." ],
  "making_of": {
    "second": {                            // omitted when no second editor is set
      "model": "mistral-large-4-0",
      "blind_scan": { "ran": true, "stories": 9, "only_second_kept": ["story-id"], "only_second_dropped": 2 },
      "selection": { "ran": true, "followed": 5, "overruled": 2 },
      "draft_check": { "ran": true, "flags": 3, "acted_on": 2 }
    },
    "limits": "Sources that could not be read this run, and anything else the reader should know."
  }
}
```

## Story

```jsonc
{
  "id": "cop31-no-deal",                   // kebab-case, unique in the edition
  "tags": ["climate", "diplomacy"],        // 1 to 3, from the tag list in state/preferences.md; add a new tag only when none fits
  "angle": "policy",                       // what kind of story: policy | decision | deal | money | markets | conflict | research | people | product | politics-poll
  "headline": "COP31 ends with no final text",
  "key": { "value": "190+", "label": "countries, no agreement" },   // the one fact in large type; null if none fits
  "summary": "Two or three short sentences a reader can stop after.",
  "what_happened": "Fuller account, from pages read this run.",
  "why_it_matters": "Context and stakes.",
  "my_read": "Claude's interpretation, labelled as such on the page.",
  "returning": null,                       // or { "since": "2026-11-23", "what_changed": "One line." } when the topic ran in the last 7 days
  "photo": { "page": "https://source-article-url", "credit": "NOS" },   // build.py takes the page's og:image; null if no real photo
  "visual": null,                          // a chart shown inside the story, see Visuals
  "coverage": {
    "kinds": ["public broadcaster", "wire agency"],
    "countries": ["NL", "UK", "TR"],
    "split": null,                         // or { "topic": "casualties", "a": { "source": "Reuters via Defense News", "says": "ten injured" }, "b": { "source": "Al Jazeera", "says": "one dead" } }
    "blind_spot": null                     // or one line: who is not covering it, e.g. "Only Dutch outlets so far"
  },
  "second_differs": null,                  // or { "note": "<= 25 words", "would_change_mind": "the evidence that would settle it" }
  "sources": [
    { "name": "NOS", "url": "https://...", "kind": "public broadcaster", "country": "NL", "basis": "read" }
  ]
}
```

- `coverage.kinds` and `countries` come from the sources actually used, looked up in `sources.md`. The page counts them.
- A `split` only when two named sources state different facts or readings of the same point. Different emphasis is not a split.
- `basis`: `read` (the page was read this run), `digest` (known only through a digest or newsletter), `headline` (headline or listing only).

## Photos and visuals

- `photo`: on every story where a source page has a real news photo (check it is not a logo). The front page shows it; without one, the tile shows `key` as a large number in the section color.
- `visual`: a chart inside the opened story, where a number, a comparison or a sequence carries it; null where none helps.

```jsonc
{ "type": "bars", "caption": "Friday's close", "unit": "%", "items": [ { "label": "Nvidia", "value": -14.0 } ] }   // "signed": false for shares or counts that are not changes (no + sign)
{ "type": "timeline", "items": [ { "date": "20 Nov", "text": "Missiles land in Poland" } ] }
{ "type": "compare", "items": [ { "label": "Monday", "value": 30, "of": 246, "text": "trains cancelled" } ] }
```
