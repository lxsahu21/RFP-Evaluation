"""
Generates four fictional supplier RFP response PDFs for the same procurement
request (a customer-support ticketing platform migration), each with
deliberately different strengths, weaknesses, pricing, and evidence quality,
per the project brief. No real/confidential supplier data is used.
"""
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors

OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_rfps")
os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
h1 = styles["Heading1"]
h2 = styles["Heading2"]
body = ParagraphStyle("body", parent=styles["Normal"], spaceAfter=8, leading=14)


def build_pdf(filename: str, supplier_name: str, sections: list):
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    story = [Paragraph(f"RFP Response: {supplier_name}", h1), Spacer(1, 10)]
    story.append(Paragraph("Procurement request: Customer Support Ticketing Platform Migration", body))
    story.append(Spacer(1, 12))
    for title, paragraphs, table_data in sections:
        story.append(Paragraph(title, h2))
        for p in paragraphs:
            story.append(Paragraph(p, body))
        if table_data:
            t = Table(table_data, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(Spacer(1, 6))
            story.append(t)
            story.append(Spacer(1, 10))
    doc.build(story)
    print(f"Created {path}")


# ---------------------------------------------------------------------------
# 1) Apex Systems -- strong technical + security, higher price, moderate schedule
# ---------------------------------------------------------------------------
apex_sections = [
    ("Executive Summary", [
        "Apex Systems proposes a cloud-native migration of the customer support ticketing platform, "
        "built on a microservices architecture with horizontal auto-scaling. Our understanding is that "
        "the current system struggles with peak-hour load and lacks modern integration hooks.",
    ], None),
    ("Proposed Solution & Architecture", [
        "The solution uses a Kubernetes-based microservice architecture with dedicated services for "
        "ticket routing, SLA tracking, and reporting. We provide REST and GraphQL APIs, native "
        "integrations with Salesforce, Slack, and Zendesk import tooling, and a scalable event bus "
        "(Kafka) for real-time updates. Architecture is designed for 10x current transaction volume "
        "without re-platforming.",
    ], None),
    ("Implementation Plan", [
        "Delivery follows a 7-month phased plan: Discovery (4 weeks), Core Platform Build (12 weeks), "
        "Integration & Data Migration (8 weeks), UAT (3 weeks), Cutover & Hypercare (3 weeks). "
        "A dedicated team of 9 (2 architects, 4 engineers, 1 PM, 1 QA lead, 1 security engineer) is "
        "assigned full-time. Key risks (data migration integrity, integration downtime) each have a "
        "documented mitigation and rollback plan.",
    ], [
        ["Milestone", "Week", "Deliverable"],
        ["Discovery complete", "4", "Signed requirements & architecture doc"],
        ["Core platform beta", "16", "Internal beta environment"],
        ["Integrations complete", "24", "All 3rd-party integrations live in staging"],
        ["UAT sign-off", "27", "Client UAT approval"],
        ["Go-live", "30", "Production cutover"],
    ]),
    ("Commercial Value", [
        "Total project cost is $486,000, comprising $360,000 implementation, $66,000 first-year "
        "support, and $60,000 contingency (12%). Assumptions: client provides timely UAT feedback "
        "within 5 business days per cycle; existing data is in a migratable format (CSV/SQL export). "
        "Pricing is fixed-bid with change requests billed at $185/hour.",
    ], [
        ["Line item", "Cost (USD)"],
        ["Implementation", "$360,000"],
        ["First-year support (Year 1)", "$66,000"],
        ["Contingency (12%)", "$60,000"],
        ["Total", "$486,000"],
    ]),
    ("Security, Compliance & Risk Controls", [
        "Apex Systems is SOC 2 Type II and ISO 27001 certified. All data is encrypted at rest (AES-256) "
        "and in transit (TLS 1.3). We support role-based access control, full audit logging, and annual "
        "third-party penetration testing with results shared with the client. GDPR and CCPA data "
        "processing addenda are available on request. Our incident response SLA is 4 hours for "
        "critical severity.",
    ], None),
    ("Support Model, Experience & References", [
        "Post-launch support includes a 24/7 tier-1 helpdesk with a 1-hour critical response SLA. "
        "Apex Systems has completed 6 similar ticketing platform migrations in the last 4 years for "
        "mid-size enterprises (500-2000 support agents). Two references are available: a regional "
        "telecom provider and a national insurance company, both willing to speak to timeline "
        "adherence and platform stability.",
    ], None),
]

# ---------------------------------------------------------------------------
# 2) BrightPath Tech -- lowest price, fastest timeline, weak compliance detail
# ---------------------------------------------------------------------------
brightpath_sections = [
    ("Executive Summary", [
        "BrightPath Tech offers a fast, low-cost migration path using our existing SaaS ticketing "
        "product, configured to the client's workflows. We understand speed and budget are top "
        "priorities for this engagement.",
    ], None),
    ("Proposed Solution & Approach", [
        "We will configure our multi-tenant SaaS platform for the client's use case, using standard "
        "web forms and email-to-ticket conversion. Custom integrations beyond our standard connector "
        "library (Zendesk, Freshdesk import only) would require a separate scoping exercise not "
        "included in this proposal.",
    ], None),
    ("Timeline, Team & Milestones", [
        "We propose an aggressive 10-week timeline: Setup (2 weeks), Configuration (4 weeks), "
        "Data Import (2 weeks), Go-live (2 weeks). A team of 3 (1 solutions engineer, 1 PM, 1 support "
        "engineer, part-time) will deliver the project alongside other client accounts.",
    ], [
        ["Phase", "Duration"],
        ["Setup", "2 weeks"],
        ["Configuration", "4 weeks"],
        ["Data import", "2 weeks"],
        ["Go-live", "2 weeks"],
    ]),
    ("Pricing", [
        "Total cost: $118,000 for the first year, including setup and licensing for 200 agent seats. "
        "Assumes standard configuration only; custom workflow logic is out of scope. Renewal pricing "
        "for year 2 onward is subject to a separate quote.",
    ], [
        ["Line item", "Cost (USD)"],
        ["Setup & configuration", "$38,000"],
        ["Year 1 licensing (200 seats)", "$80,000"],
        ["Total Year 1", "$118,000"],
    ]),
    ("Security & Compliance", [
        "Our platform runs on major cloud infrastructure providers. We take data security seriously "
        "and follow industry best practices.",
    ], None),
    ("Support & Experience", [
        "Standard support is available via email during business hours (9am-6pm, Mon-Fri). "
        "BrightPath Tech has helped several small and mid-size companies move to our platform.",
    ], None),
]

# ---------------------------------------------------------------------------
# 3) NexaWorks -- balanced, strongest implementation plan and support model
# ---------------------------------------------------------------------------
nexaworks_sections = [
    ("Executive Summary", [
        "NexaWorks proposes a balanced migration approach combining a proven implementation "
        "methodology with a modern, extensible ticketing platform. Our focus is on de-risking delivery "
        "through disciplined project management and a strong post-launch support model.",
    ], None),
    ("Proposed Solution", [
        "The solution is built on a modular service-oriented architecture with a plugin system for "
        "integrations (Salesforce, Slack, Jira, and a generic webhook framework for anything else). "
        "The platform supports role-based dashboards, SLA automation, and configurable escalation "
        "rules.",
    ], None),
    ("Implementation Plan & Team", [
        "Our methodology uses 2-week sprints across a 6-month delivery: Sprint 0 (requirements & "
        "environment setup), Sprints 1-6 (core build), Sprints 7-9 (integrations), Sprints 10-11 (UAT "
        "and training), Sprint 12 (go-live and 2-week hypercare). The team includes a dedicated "
        "delivery manager, 5 engineers, 1 QA engineer, and a client success manager who stays engaged "
        "post-launch. Risk register is reviewed with the client bi-weekly, covering data migration, "
        "user adoption, and integration stability with named owners and mitigation steps for each.",
    ], [
        ["Sprint", "Focus", "Weeks"],
        ["0", "Requirements & setup", "2"],
        ["1-6", "Core platform build", "12"],
        ["7-9", "Integrations", "6"],
        ["10-11", "UAT & training", "4"],
        ["12", "Go-live & hypercare", "2"],
    ]),
    ("Commercial Value", [
        "Total price is $340,000, itemized below. Assumptions: client-side subject matter experts "
        "available approximately 10 hours/week during build; production data volume under 5M "
        "historical tickets. Change requests are estimated and quoted individually before work begins.",
    ], [
        ["Line item", "Cost (USD)"],
        ["Implementation", "$275,000"],
        ["Training & documentation", "$25,000"],
        ["First-year support", "$40,000"],
        ["Total", "$340,000"],
    ]),
    ("Security, Compliance & Risk Controls", [
        "NexaWorks maintains ISO 27001 certification and completes annual SOC 2 Type I audits, with "
        "Type II in progress (expected completion in 6 months). Data is encrypted in transit (TLS 1.2+) "
        "and at rest. Access control is role-based with mandatory MFA for admin accounts. A named "
        "security contact is assigned for the duration of the engagement.",
    ], None),
    ("Support Model, Experience & References", [
        "NexaWorks provides a dedicated client success manager plus a tiered support desk with a "
        "2-hour response SLA for critical issues, extending to 24/7 in year one at no extra cost. We "
        "have delivered 9 similar support-platform implementations in the past 3 years, including 3 "
        "in the same industry vertical as the client. Three references are provided, each available "
        "for a reference call within one week's notice, and each willing to discuss our post-launch "
        "support quality specifically.",
    ], None),
]

# ---------------------------------------------------------------------------
# 4) Orbit Digital -- strong experience/references, vague integration plan
# ---------------------------------------------------------------------------
orbit_sections = [
    ("Executive Summary", [
        "Orbit Digital brings deep domain experience in customer support transformations. We have "
        "delivered dozens of successful platform rollouts and bring that institutional knowledge to "
        "this engagement.",
    ], None),
    ("Proposed Solution", [
        "We will implement a leading ticketing platform tailored to the client's needs. Our team will "
        "work with the client to determine the best integration approach during the discovery phase; "
        "specific integration architecture and API details will be finalized once we better understand "
        "the client's existing systems.",
    ], None),
    ("Timeline, Team & Milestones", [
        "We estimate a 6 to 8 month timeline depending on scope finalized during discovery. The team "
        "will include senior consultants drawn from our broader delivery bench as needed throughout "
        "the project.",
    ], [
        ["Phase", "Estimated duration"],
        ["Discovery", "4-6 weeks"],
        ["Build", "12-20 weeks"],
        ["Testing & go-live", "4-6 weeks"],
    ]),
    ("Commercial Value", [
        "Estimated total investment is in the range of $300,000-$380,000 depending on final scope. "
        "A detailed price breakdown will be provided after discovery. Travel and expenses are billed "
        "separately at cost.",
    ], [
        ["Line item", "Estimated cost (USD)"],
        ["Discovery & scoping", "$40,000"],
        ["Implementation (range)", "$220,000 - $290,000"],
        ["Support (Year 1, estimate)", "$40,000 - $50,000"],
    ]),
    ("Security, Compliance & Risk Controls", [
        "Orbit Digital follows applicable data protection regulations and can accommodate client "
        "security requirements as they are defined during discovery. Formal certifications documentation "
        "is available upon signing.",
    ], None),
    ("Support Model, Experience & References", [
        "Orbit Digital has completed over 40 customer support platform engagements across 12 years in "
        "business, including several Fortune 500 clients. We provide five references from recent "
        "engagements in retail, healthcare, and financial services, all of whom rate our delivery "
        "teams highly for domain expertise and stakeholder communication. Standard support post-launch "
        "includes a named account manager and business-hours helpdesk.",
    ], None),
]


def main():
    build_pdf("Apex_Systems_RFP_Response.pdf", "Apex Systems", apex_sections)
    build_pdf("BrightPath_Tech_RFP_Response.pdf", "BrightPath Tech", brightpath_sections)
    build_pdf("NexaWorks_RFP_Response.pdf", "NexaWorks", nexaworks_sections)
    build_pdf("Orbit_Digital_RFP_Response.pdf", "Orbit Digital", orbit_sections)


if __name__ == "__main__":
    main()
