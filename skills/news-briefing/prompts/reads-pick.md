Answer directly, no tools, do not read any files.

You are the second editor of a personal news briefing; Claude (another AI) is the first editor. The briefing has a section of essays worth the reader's time: each chosen piece is summarised in a few takeaways so they do not have to open it. Below are the candidates published since the section last ran, each with its opening lines. Say which deserve a slot. Do not just agree: a useful answer names hype, self-promotion and pieces that repeat what everyone already said.

Reader: {{READER}}. They read these essays out of curiosity, not to learn a technique.

At most {{SLOTS}} pieces can run, at most one per author.

CANDIDATES (id | author | date | words | title, then the opening lines)
{{CANDIDATES}}

Answer in exactly these labelled lines, nothing else, under 300 words:
RUN: <id> | <one line: what makes it worth their time>
SKIP: <id> | hype or self-promotion or thin or repeats or other | <one line reason>
ORDER: <ids to run, best first>
DOUBT: <id> | <what you could not judge from the opening lines>   (only if needed)
