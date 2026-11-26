# Settings

The skill reads this file at the start of every run. Everything about you lives here and in `state/preferences.md`; nothing about you is in the steps.

You do not have to edit it by hand. While the line below says `not done`, the first `/news-briefing` asks you a few questions, fills this file in, trims `sources.md` to your countries, and then makes the first edition. You can change anything here later.

```
setup: not done
```

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
| home | Netherlands & Portugal | politics, economy, society in both countries; city news when it matters |

## Local section (optional)

A section about one local scene, with rankings and events beside the stories. Leave `id` empty to switch it off.

```
id: scene
name: Amsterdam tech
scope: startups and scale-ups in Amsterdam and the Netherlands: funding rounds, acquisitions, expansion, foreign companies opening an office, senior hires and layoffs, rankings
events: tech and startup events in Amsterdam in the next five weeks
```

## Search (optional)

Fill this in if you are looking for a job or a move and want the briefing to say what the news means for that search. It switches on two things: a "For your search" note on local section stories, and "Career reading", essays about the job market and roles, under the local section. Leave `seeking` empty to switch both off. Nothing here is ever sent to the second editor.

```
seeking:
watch list:
```

- `seeking`: one or two lines on the role, the seat and the kind of company, for example "a senior data engineer role at a climate-tech company in Lisbon".
- `watch list`: optional company names, comma-separated. Stories about them are looked for first and marked "On your list".

## Worth reading

Essays by a few writers you choose, each read whole and reduced to takeaways, so you do not have to open them. The writers are the rows under "Worth reading" in `sources.md`. Set `worth reading: off` to leave the section out.

```
worth reading: on
```

## Second editor (optional)

Another model that searches the news on its own, then checks Claude's selection, the draft, and the Worth reading pieces. Any model you can call from a shell command that takes a prompt file and prints the answer. Leave `command` empty to run on Claude alone; the page then says no second model checked the edition.

```
name:
model:
command:
search: no
```

- `command` is a shell command; `{prompt}` in it is replaced with the path of the filled prompt file, and `{turns}` with the turn limit the step names. It runs from the `out/second/` folder, so the model never sees the rest of this folder.
- The worked example is Mistral through its Vibe CLI, with Vibe installed and signed in. `--agent ask` is its read-only agent (it can search the web, but not change files), and `--max-price` caps what one call can spend:

  ```
  name: Mistral
  model: mistral-large-4-0
  command: vibe -p "$(cat {prompt})" --agent ask --max-turns {turns} --max-price 0.50 --model mistral-large-4-0
  search: yes
  ```

  Flags can change between Vibe versions; `vibe --help` has the current ones.
- Any other CLI works the same way: Codex, Gemini, or a local model through Ollama. `search: yes` only when the model can search the web from that command; without search, the blind scan is skipped and the checks run on the text alone.
- Only public news text, essay text and the reader line go to the second editor, never `state/preferences.md`, taps, chat messages, the search block or the watch list.

## Long view

```
paid subscriptions: none
```

A paywalled analysis piece counts only as "headline only" unless you list the publication here.

## Nightly run (optional)

The time the scheduled run starts, if you install it (see the README). It builds the edition but cannot publish it: the next time you type `/news-briefing` it is published first.

```
nightly: 06:00
```
