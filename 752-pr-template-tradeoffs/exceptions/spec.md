# `spec` does not apply

No behavior change: only the guidance comments in the two PR templates change. wfctl install-config github still copies the shipped template the same way and only the text it copies differs, and no check reads the comments, since change_sections lists no new heading. No significant design decision: it is wording in a template, undone with one commit. No ownership change: the templates and opening-a-change keep the same owners, and the skill still keeps no section list.
