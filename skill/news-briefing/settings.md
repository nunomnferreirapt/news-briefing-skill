# Settings

Edit this file once. The skill reads it at the start of every run. Everything about you lives here and in `state/preferences.md`; nothing about you is in the steps.

## Reader

One line, written as "a reader who ...". It goes into the second editor's prompts and into the page's chat, so keep it to what you are happy to send to both models.

```
reader: a manager living in Amsterdam, Portuguese, interested in AI and technology, European and world politics, and the Netherlands and Portugal
masthead: Briefing · Amsterdam
```

## Sections

Three or four. The page colors the first four in this order. `id` is short and lower case; `name` is what the page shows; `scope` is what the researchers look for.

| id | name | scope |
|---|---|---|
| world | World | geopolitics, conflicts, diplomacy, economy |
| tech | Tech & AI | companies, models, policy, research, markets for tech |
| home | Netherlands & Portugal | politics, economy, society in both countries, roughly balanced; city news when it matters |

## Local section (optional)

A section about one local scene, with rankings and events beside the stories. Leave `id` empty to switch it off.

```
id: ams
name: Amsterdam tech
scope: startups and scale-ups in Amsterdam and the Netherlands: funding rounds, acquisitions, expansion, foreign companies opening an office, senior hires and layoffs, rankings
events: tech and startup events in Amsterdam in the next five weeks
watch list: (optional) company names to look out for. They are never sent to the second editor.
```

## Second editor (optional)

Another model that searches the news on its own, then checks Claude's selection and draft. Any model you can call from a shell command that takes a prompt file and prints the answer. Leave `command` empty to run without one; the page then says no second model checked the edition.

```
name: Mistral
model: mistral-large-4-0
command:
search: yes
```

- `command` is a shell command; `{prompt}` in it is replaced with the path of the filled prompt file, and `{turns}` with the turn limit the step names. The worked example is Mistral through its Vibe CLI in headless mode (`vibe -p ... --agent ask --max-turns {turns}`); check the CLI's own docs for where it writes the answer, and wrap it in a small script if the answer does not come out on stdout.
- `search: yes` when the model can search the web from that command; without search, the blind scan is skipped and the checks run on the text alone.
- Only public news text and the reader line go to the second editor, never `state/preferences.md`, taps or chat messages.

## Long view

```
paid subscriptions: none
```

A paywalled analysis piece counts only as "headline only" unless you list the publication here.
