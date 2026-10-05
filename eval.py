import time

import search
import triage

# (ticket text, expected status, expected category or None to skip the category check)
CASES = [
    # Should be answered from the knowledge base
    ("How do I reset my password?", "auto_answered", "account_access"),
    ("Where can I download my invoice?", "auto_answered", "billing"),
    ("What plans do you offer and how much do they cost?", "auto_answered", "billing"),
    ("How do I turn on two-factor authentication?", "auto_answered", "account_access"),
    ("How do I export my data?", "auto_answered", "data_export"),
    ("What is the API rate limit on the Pro plan?", "auto_answered", "api"),
    ("How do I connect Jira and GitHub?", "auto_answered", "integrations"),
    ("How do I cancel my subscription?", "auto_answered", "billing"),
    ("How do I invite a new member to my workspace?", "auto_answered", "account_access"),
    ("How do I upgrade my plan?", "auto_answered", "billing"),
    ("What is your refund policy?", "auto_answered", "billing"),
    ("How does single sign-on work?", "auto_answered", "account_access"),
    ("I forgot my password and the reset email never arrived", "auto_answered", "account_access"),
    ("How long is the export download link valid?", "auto_answered", "data_export"),
    ("How many API requests per minute are allowed?", "auto_answered", "api"),
    ("Where do I change the billing contact on invoices?", "auto_answered", "billing"),
    # Must go to a human
    ("I was charged twice this month and I want a refund!!", "escalated", "billing"),
    ("I want my money back for the yearly plan", "escalated", "billing"),
    ("Can I get a refund for my yearly plan?", "escalated", "billing"),
    ("Someone hacked our account and stole data", "escalated", "security"),
    ("We think there was a data breach in our workspace", "escalated", "security"),
    ("I received a phishing email pretending to be Lumora", "escalated", "security"),
    ("Do you have a dark mode?", "escalated", "other"),
    ("Please add support for Trello", "escalated", "feature_request"),
    ("The app keeps crashing when I open a project", "escalated", "bug_report"),
    ("Our production server is down and we cannot work", "escalated", None),
    ("I will contact my lawyer if this is not fixed", "escalated", None),
    ("What is the weather like today?", "escalated", "other"),
]


def main():
    mode = "mock" if search.is_mock() else "gemini"
    print(f"Mode: {mode}, tickets: {len(CASES)}\n")

    status_ok = category_ok = category_total = 0
    must_escalate = escalated_right = wrong_auto = 0
    failures = []

    for text, want_status, want_category in CASES:
        got = triage.triage(text)
        if mode == "gemini":
            time.sleep(0.7)

        if got["status"] == want_status:
            status_ok += 1
        else:
            failures.append((text, f"status: wanted {want_status}, got {got['status']}", got["confidence"]))

        if want_category is not None:
            category_total += 1
            if got["category"] == want_category:
                category_ok += 1
            else:
                failures.append((text, f"category: wanted {want_category}, got {got['category']}", got["confidence"]))

        if want_status == "escalated":
            must_escalate += 1
            if got["status"] == "escalated":
                escalated_right += 1
            else:
                wrong_auto += 1

    n = len(CASES)
    print(f"Routing correct (answer vs escalate): {status_ok}/{n} = {100 * status_ok / n:.0f}%")
    print(f"Category correct: {category_ok}/{category_total} = {100 * category_ok / category_total:.0f}%")
    print(f"Tickets that needed a human and got one: {escalated_right}/{must_escalate} = {100 * escalated_right / must_escalate:.0f}%")
    print(f"Wrongly auto-answered: {wrong_auto}")

    if failures:
        print("\nFailures:")
        for text, problem, confidence in failures:
            print(f"- {text}\n    {problem} (confidence {confidence})")


if __name__ == "__main__":
    main()