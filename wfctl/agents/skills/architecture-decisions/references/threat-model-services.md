# Threat model: controls on services, APIs, and data stores

Read this guide when the control sits on a network service, an API, or a data
store, such as an authorization check, a rate limit, or a webhook's signature
check. It adds the prompts for step 2 and the principles for step 3 of
[`threat-model.md`](threat-model.md), which you've already read.

The method comes from the OWASP Threat Modeling Cheat Sheet
(https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html),
which recommends STRIDE for a technical design. The STRIDE table and the trust
boundary prompts are in the "Process: Threat Model First" section of
[`../../security-and-hardening/SKILL.md`](../../security-and-hardening/SKILL.md).
Read that section, not the whole skill, since the rest of it is a review
checklist.

## Paths to walk in step 2

1. Draw the trust boundaries the control sits on. OWASP's model shows "trust
   boundaries, data flows, data stores, processes, and the external entities."
   A path is a data flow that crosses the control.
2. Run each STRIDE category over each path, using the table in
   `security-and-hardening`. Each threat you find becomes a form: a concrete
   request or input, such as `GET /admin/users` with another user's session.
3. List the requests the control must keep serving, such as a user reading
   their own record. Those are the candidates for `Must let through`.

## Principles for step 3

1. Write each form as a request a test can send. A `Must keep catching` form
   that a test can't send can't be checked. The cheat sheet's review checklist
   asks, "Can the agreed upon mitigations be tested?"
2. Name the asset each form reaches, such as credentials, personal data, or an
   admin action. The impact of a form decides whether `Accepts` is an option.
3. For a transferred risk, such as a rate limit enforced by a proxy in front of
   the service, name that proxy and who owns it.

## Example

wfctl has no control of this kind, so there's no example record in its own arch
root yet.
