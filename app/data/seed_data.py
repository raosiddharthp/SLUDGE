"""Synthetic seed data for the SLUDGE POC. Every person and event is fictional.

Three source systems, as in the design doc's As-Is architecture:
  app_events -> Member App      (no drop-off telemetry in the real estate)
  crm_notes  -> Contact Centre CRM (agent note + raw transcript excerpt)
  core_txns  -> Core Banking    (transactions, direct debits)

vulnerability_flag is None on every CRM record on purpose: that is the
gap SLUDGE exists to close.
"""

SEED = {
    "members": [
        {"member_id": "M-1001", "name": "Eve Moneypenny", "age": 34, "products": ["current_account", "joint_savings"]},
        {"member_id": "M-1002", "name": "Percy Vere", "age": 71, "products": ["current_account"]},
        {"member_id": "M-1003", "name": "Penny Wise", "age": 82, "products": ["current_account", "savings"]},
        {"member_id": "M-1004", "name": "Dr. Grace Underwood", "age": 44, "products": ["current_account", "loan"]},
        {"member_id": "M-1005", "name": "Sam Ordinary", "age": 39, "products": ["current_account"]},  # control: expect no finding
    ],
    "app_events": [
        {"ts": "2026-11-01T18:20:00Z", "member_id": "M-1001", "event": "login", "step": "home", "outcome": "ok"},
        {"ts": "2026-11-01T18:21:00Z", "member_id": "M-1001", "event": "view_statement", "step": "statements", "outcome": "ok"},
        {"ts": "2026-10-29T02:41:00Z", "member_id": "M-1002", "event": "view_balance", "step": "home", "outcome": "ok"},
        {"ts": "2026-11-02T03:12:00Z", "member_id": "M-1002", "event": "view_balance", "step": "home", "outcome": "ok"},
        {"ts": "2026-11-04T02:58:00Z", "member_id": "M-1002", "event": "view_balance", "step": "home", "outcome": "ok"},
        {"ts": "2026-10-28T14:02:00Z", "member_id": "M-1003", "event": "add_payee", "step": "otp_entry", "outcome": "code_expired"},
        {"ts": "2026-10-28T14:20:00Z", "member_id": "M-1003", "event": "add_payee", "step": "verify_identity", "outcome": "abandoned"},
        {"ts": "2026-10-29T10:05:00Z", "member_id": "M-1003", "event": "add_payee", "step": "otp_entry", "outcome": "code_expired"},
        {"ts": "2026-10-30T11:40:00Z", "member_id": "M-1003", "event": "add_payee", "step": "verify_identity", "outcome": "abandoned"},
        {"ts": "2026-11-09T19:00:00Z", "member_id": "M-1004", "event": "login", "step": "home", "outcome": "ok"},
        {"ts": "2026-11-08T08:30:00Z", "member_id": "M-1005", "event": "login", "step": "home", "outcome": "ok"},
        {"ts": "2026-11-08T08:31:00Z", "member_id": "M-1005", "event": "add_payee", "step": "confirm", "outcome": "ok"},
    ],
    "crm_notes": [
        {"call_id": "C-2001", "member_id": "M-1001", "ts": "2026-10-06T10:15:00Z", "agent": "Agent A",
         "agent_note": "Caller asked to remove partner from joint direct debits. Advised to send death certificate.",
         "transcript_excerpt": ["CALLER: I need my partner taken off the direct debits. He died last week.",
                                "AGENT: I'm sorry to hear that. Please send the death certificate."],
         "vulnerability_flag": None},
        {"call_id": "C-2002", "member_id": "M-1001", "ts": "2026-10-21T14:40:00Z", "agent": "Agent B",
         "agent_note": "Caller chasing certificate status. ID verified, address updated.",
         "transcript_excerpt": ["AGENT: Can I ask what this is about?",
                                "CALLER: I've told your people this already. My partner died. I don't want to say it again."],
         "vulnerability_flag": None},
        {"call_id": "C-2003", "member_id": "M-1001", "ts": "2026-11-05T09:05:00Z", "agent": "Agent C",
         "agent_note": "Caller asking about closing joint savings. Forms sent.",
         "transcript_excerpt": ["AGENT: And what's the reason for closing the account?",
                                "CALLER: My partner died. That's three times I've said it now."],
         "vulnerability_flag": None},
        {"call_id": "C-2004", "member_id": "M-1002", "ts": "2026-11-03T11:00:00Z", "agent": "Agent D",
         "agent_note": "Caller received returned direct debit letter. DD re-presented.",
         "transcript_excerpt": ["AGENT: Is everything alright with money or health at the moment?",
                                "CALLER: No, I'm perfectly fine. It's just an admin slip."],
         "vulnerability_flag": None},
        {"call_id": "C-2005", "member_id": "M-1003", "ts": "2026-11-02T15:30:00Z", "agent": "Agent E",
         "agent_note": "Caller could not set up payee in app. Payee created by phone after ID&V.",
         "transcript_excerpt": ["CALLER: I've tried your app four times. I can't read the small writing and the code runs out.",
                                "CALLER: There is nothing wrong with my head. Your app is impossible."],
         "vulnerability_flag": None},
        {"call_id": "C-2006", "member_id": "M-1004", "ts": "2026-03-10T13:10:00Z", "agent": "Agent F",
         "agent_note": "Payment holiday approved for 3 months. Reason code: OTHER.",
         "transcript_excerpt": ["CALLER: I've just been diagnosed with breast cancer and I start treatment next week. I can't work.",
                                "AGENT: I'll arrange a three month payment holiday."],
         "vulnerability_flag": None},
        {"call_id": "C-2007", "member_id": "M-1004", "ts": "2026-11-09T16:20:00Z", "agent": "Agent G",
         "agent_note": "Caller asking for another payment holiday. Reason not recorded.",
         "transcript_excerpt": ["AGENT: Can I ask the reason for the extension?",
                                "CALLER: I've already told you. I'm not doing this again."],
         "vulnerability_flag": None},
        {"call_id": "C-2008", "member_id": "M-1005", "ts": "2026-11-08T12:00:00Z", "agent": "Agent H",
         "agent_note": "Caller queried a card fee. Explained and waived.",
         "transcript_excerpt": ["CALLER: Why was I charged a fee on my card?",
                                "AGENT: That was a foreign transaction fee. I've waived it as a goodwill gesture."],
         "vulnerability_flag": None},
    ],
    "core_txns": [
        {"ts": "2026-10-03T00:00:00Z", "member_id": "M-1001", "type": "JOINT_ACCOUNT_DD", "amount_gbp": 96.00, "status": "PAID"},
        {"ts": "2026-09-01T00:00:00Z", "member_id": "M-1002", "type": "DD_COUNCIL_TAX", "amount_gbp": 187.00, "status": "PAID"},
        {"ts": "2026-10-01T00:00:00Z", "member_id": "M-1002", "type": "DD_COUNCIL_TAX", "amount_gbp": 187.00, "status": "RETURNED_UNPAID"},
        {"ts": "2026-11-01T00:00:00Z", "member_id": "M-1002", "type": "DD_WATER", "amount_gbp": 42.50, "status": "RETURNED_UNPAID"},
        {"ts": "2026-11-01T00:00:00Z", "member_id": "M-1003", "type": "DD_ENERGY", "amount_gbp": 61.20, "status": "PAID"},
        {"ts": "2026-03-12T00:00:00Z", "member_id": "M-1004", "type": "PAYMENT_HOLIDAY_START", "amount_gbp": 0.00, "status": "APPLIED"},
        {"ts": "2026-06-12T00:00:00Z", "member_id": "M-1004", "type": "PAYMENT_HOLIDAY_END", "amount_gbp": 0.00, "status": "APPLIED"},
        {"ts": "2026-10-12T00:00:00Z", "member_id": "M-1004", "type": "LOAN_PAYMENT", "amount_gbp": 245.00, "status": "PAID"},
        {"ts": "2026-10-28T00:00:00Z", "member_id": "M-1005", "type": "SALARY_CREDIT", "amount_gbp": 2480.00, "status": "PAID"},
        {"ts": "2026-11-01T00:00:00Z", "member_id": "M-1005", "type": "DD_ENERGY", "amount_gbp": 74.00, "status": "PAID"},
    ],
}
