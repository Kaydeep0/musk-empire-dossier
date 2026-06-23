"""Shared constants for alerts, LinkedIn, and pipeline triggers."""

MATERIAL_FORMS = {
    "4", "4/A", "3", "5",
    "SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A", "SCHEDULE 13G/A",
    "8-K", "8-K/A", "DEF 14A", "DEFA14A", "DEFM14A", "S-1", "S-4", "424B4", "424B5",
}

# LinkedIn posts only on forms that move the thesis (not every site rebuild).
LINKEDIN_FORMS = {
    "8-K", "8-K/A", "4", "4/A", "DEF 14A", "DEFA14A", "DEFM14A", "424B4", "424B5", "S-1", "S-4",
}

# Instant email reminders vs bundled in daily digest.
INSTANT_REMIND_DAYS = {1, 3}
DIGEST_REMIND_DAYS = {7}

SITE = "https://kaydeep0.github.io/musk-empire-dossier/"
