# Engineering conventions

House rules for this repository. These are not suggestions; a change that
breaks one of them should not be merged.

## Errors returned to partners

1. **Every error carries a stable machine-readable `code`.** Partners branch
   on the code, never on the message. A response with only a human-readable
   string is not an acceptable error.

2. **Internal detail never leaves the building.** Stack traces, SQL, upstream
   URLs, vendor error text and exception class names must not appear in
   anything a partner can read.

3. **An error is logged once, at the boundary.** Do not log and re-raise.
   Duplicated log lines for a single failure make incidents unreadable.

4. **Retryable and permanent failures must be distinguishable.** A partner
   has to be able to tell from the response whether trying again will help.

## Money

5. All money is integer minor units (pence). No function returns a fraction.

## Storage

6. Anything cached or stored per partner is scoped by account id.
