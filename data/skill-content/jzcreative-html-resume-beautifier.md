---
name: resume-beautifier
description: Create polished, privacy-safe A4 resume designs from structured resume content or existing resume files. Use when Codex needs to extract resume facts, remove personal example data, choose a visual style, generate an editable HTML resume, add client-side PNG/PDF export, audit for private information before open sourcing, or prepare a reusable resume-design workflow.
---

# Resume Beautifier

Use this skill to turn resume content into a polished A4 HTML resume while keeping personal data out of reusable templates and open-source artifacts.

## Core Workflow

1. **Extract facts without rewriting truth.**
   - Preserve names, dates, awards, roles, schools, companies, and claims exactly unless the user asks to edit them.
   - If the input is `.docx`, use the documents skill or `python-docx` to extract paragraphs/tables first.
   - If the input is HTML, treat the visible resume content as source data and ignore export UI/script controls.

2. **Normalize into JSON.**
   - Use `references/resume_schema.md` for the expected structure.
   - Keep personal content in the JSON input/output, not in the skill itself.
   - For open-source examples, replace real personal details with fictional placeholders.

3. **Choose a style.**
   - Use `references/theme_tokens.md` for available brand-inspired style tokens.
   - Do not claim a theme is an official brand implementation unless the user supplied the original brand guidelines or DESIGN.md.
   - Prefer restrained themes for formal resumes; use expressive themes only when the user's target audience fits.

4. **Generate HTML.**
   - Run `scripts/build_resume_html.py` with a resume JSON file.
   - The generated HTML is a self-contained A4 page with print CSS and client-side export buttons.
   - If a headshot is included, embed it as a data URI so export works from `file://`.
   - Treat export runtime assets the same way: if the page depends on `html2canvas`, download that browser-side script once and embed it into the delivered HTML instead of relying on CDN loading at open time.

5. **Export and verify.**
   - Treat self-contained export as a hard requirement for local `file://` delivery. Do not assume remote CDN access will be available when the user opens the HTML later.
   - Prefer browser-native rendering of the HTML. Avoid separately redrawing the resume in another PDF library unless browser export is blocked.
   - Use the HTML toolbar to export PNG/PDF from the rendered page, or use browser automation when available.
   - Visually inspect the result: no clipping, overlap, unexpected page breaks, stray design credits, or distorted headshots.
   - Before handing off the result, explicitly remind the user whether `html2canvas` has already been embedded into the HTML. If it has not, warn clearly that `file://` export may fail, buttons may appear unresponsive, or PDF export may produce tainted-canvas errors.

6. **Audit privacy before packaging.**
   - Run `scripts/audit_pii.py` on skill/repo files before publishing.
   - Remove real names, phone numbers, emails, addresses, portraits, and bespoke career facts from examples/templates.

## Non-Negotiable Export Rule

- For resumés delivered as local HTML files, do not leave `html2canvas` as a runtime CDN dependency.
- Download the browser-side `html2canvas` script once, embed it into the output HTML, and keep the export path self-contained.
- If a session ends before this is done, say so plainly in the final handoff instead of implying export is ready.

## Scripts

- `scripts/build_resume_html.py`: build a self-contained A4 resume HTML from JSON.
- `scripts/audit_pii.py`: scan files for likely emails, phone numbers, ID-like numbers, and user-provided denylist terms.

## References

- `references/resume_schema.md`: JSON schema and content mapping guidance.
- `references/theme_tokens.md`: available theme names and token rules.
- `references/export_workflow.md`: export and verification workflow for HTML, PNG, and PDF.

## Privacy Rules

- Never commit a user's real resume, photo, or contact details into the skill package.
- Keep examples fictional.
- If deriving the skill from a live resume, explicitly state that the reusable skill has been stripped of personal content.
- If publishing to GitHub, run the PII audit against the whole repo and show the result.
