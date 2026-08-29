"""
Generates twenty fictional supplier RFP response PDFs for the same procurement
request (a customer-support ticketing platform migration). Each supplier has a
distinct profile (price, timeline, technical depth, compliance maturity,
experience level) so LLM scoring and peer ranking produce meaningful,
differentiated results. No real/confidential supplier data is used.
"""
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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


def make_sections(p: dict) -> list:
    """Builds the standard 6-section proposal from a supplier profile dict."""
    return [
        ("Executive Summary", [p["summary"]], None),
        ("Proposed Solution & Architecture", [p["solution"]], None),
        ("Implementation Plan, Team & Milestones", [p["implementation"]], p.get("milestones_table")),
        ("Commercial Value", [p["pricing_text"]], p.get("pricing_table")),
        ("Security, Compliance & Risk Controls", [p["security"]], None),
        ("Support Model, Experience & References", [p["support"]], None),
    ]


# ---------------------------------------------------------------------------
# 20 supplier profiles -- deliberately varied strengths/weaknesses so
# evaluation and ranking produce differentiated, realistic results.
# ---------------------------------------------------------------------------
SUPPLIERS = [
    dict(name="Apex Systems", summary="Apex Systems proposes a cloud-native migration built on a microservices architecture with horizontal auto-scaling, addressing current peak-hour load issues.",
         solution="Kubernetes-based microservices with dedicated ticket routing, SLA tracking, and reporting services. REST/GraphQL APIs, native Salesforce/Slack/Zendesk integrations, and a Kafka event bus. Designed for 10x current volume without re-platforming.",
         implementation="7-month phased plan: Discovery (4wk), Core Build (12wk), Integration & Migration (8wk), UAT (3wk), Cutover & Hypercare (3wk). Dedicated team of 9 including 2 architects and a security engineer. Documented mitigation and rollback plans for each key risk.",
         milestones_table=[["Milestone","Week","Deliverable"],["Discovery complete","4","Signed architecture doc"],["Core platform beta","16","Internal beta"],["Integrations complete","24","Staging integrations live"],["Go-live","30","Production cutover"]],
         pricing_text="Total cost $486,000: $360,000 implementation, $66,000 first-year support, $60,000 contingency (12%). Fixed-bid; change requests at $185/hour.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$360,000"],["Year 1 support","$66,000"],["Contingency","$60,000"],["Total","$486,000"]],
         security="SOC 2 Type II and ISO 27001 certified. AES-256 at rest, TLS 1.3 in transit. RBAC, full audit logging, annual third-party pen testing shared with client. 4-hour critical incident SLA.",
         support="24/7 tier-1 helpdesk, 1-hour critical SLA. 6 similar migrations completed in 4 years for mid-size enterprises. Two references available (telecom, insurance).",
         experience=8.5, days_ago=19),
    dict(name="BrightPath Tech", summary="BrightPath Tech offers a fast, low-cost migration using our existing SaaS ticketing product configured to the client's workflows.",
         solution="Multi-tenant SaaS platform configured via standard web forms and email-to-ticket conversion. Custom integrations beyond Zendesk/Freshdesk import require separate scoping, not included here.",
         implementation="Aggressive 10-week timeline: Setup (2wk), Configuration (4wk), Data Import (2wk), Go-live (2wk). Team of 3 (part-time), shared across other client accounts.",
         milestones_table=[["Phase","Duration"],["Setup","2 weeks"],["Configuration","4 weeks"],["Data import","2 weeks"],["Go-live","2 weeks"]],
         pricing_text="Total Year 1 cost $118,000 for 200 agent seats, standard configuration only. Renewal pricing quoted separately.",
         pricing_table=[["Line item","Cost (USD)"],["Setup & configuration","$38,000"],["Year 1 licensing (200 seats)","$80,000"],["Total Year 1","$118,000"]],
         security="Runs on major cloud infrastructure providers. Follows industry best practices for data security.",
         support="Standard email support, business hours only (9am-6pm Mon-Fri). Has helped several small/mid-size companies migrate.",
         experience=5.0, days_ago=21),
    dict(name="NexaWorks", summary="NexaWorks proposes a balanced migration combining a proven implementation methodology with an extensible ticketing platform, focused on de-risking delivery.",
         solution="Modular service-oriented architecture with a plugin system for integrations (Salesforce, Slack, Jira, generic webhooks). Role-based dashboards, SLA automation, configurable escalation rules.",
         implementation="2-week sprints over 6 months: Sprint 0 (setup), Sprints 1-6 (core build), 7-9 (integrations), 10-11 (UAT/training), 12 (go-live/hypercare). Dedicated delivery manager, 5 engineers, QA engineer, client success manager engaged post-launch. Bi-weekly risk register review.",
         milestones_table=[["Sprint","Focus","Weeks"],["0","Setup","2"],["1-6","Core build","12"],["7-9","Integrations","6"],["10-11","UAT & training","4"],["12","Go-live","2"]],
         pricing_text="Total price $340,000. Assumes 10hr/week client SME availability during build; production volume under 5M historical tickets.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$275,000"],["Training & docs","$25,000"],["Year 1 support","$40,000"],["Total","$340,000"]],
         security="ISO 27001 certified; SOC 2 Type I complete, Type II in progress (6 months). TLS 1.2+, RBAC with mandatory admin MFA. Named security contact for engagement duration.",
         support="Dedicated client success manager plus tiered support, 2-hour critical SLA, extending to 24/7 in year one at no cost. 9 similar implementations in 3 years, 3 references willing to discuss support quality.",
         experience=7.5, days_ago=20),
    dict(name="Orbit Digital", summary="Orbit Digital brings deep domain experience in customer support transformations, having delivered dozens of successful platform rollouts.",
         solution="Will implement a leading ticketing platform tailored to client needs. Specific integration architecture finalized during discovery once existing systems are better understood.",
         implementation="Estimated 6-8 months depending on scope finalized during discovery. Senior consultants drawn from broader delivery bench as needed.",
         milestones_table=[["Phase","Estimated duration"],["Discovery","4-6 weeks"],["Build","12-20 weeks"],["Testing & go-live","4-6 weeks"]],
         pricing_text="Estimated total investment $300,000-$380,000 depending on final scope. Detailed breakdown provided after discovery. Travel/expenses billed at cost.",
         pricing_table=[["Line item","Estimated cost (USD)"],["Discovery & scoping","$40,000"],["Implementation (range)","$220,000 - $290,000"],["Year 1 support (est.)","$40,000 - $50,000"]],
         security="Follows applicable data protection regulations; can accommodate client security requirements as defined during discovery. Certification documentation available upon signing.",
         support="Over 40 platform engagements across 12 years, including Fortune 500 clients. Five references from retail, healthcare, financial services. Named account manager, business-hours helpdesk.",
         experience=9.0, days_ago=18),
    dict(name="Vertex Cloud Solutions", summary="Vertex Cloud Solutions proposes a modern, API-first ticketing replacement with strong DevOps automation and CI/CD-driven delivery.",
         solution="Serverless architecture on managed cloud functions, event-driven ticket workflows, native webhook framework, and an open API spec published for client-side extension.",
         implementation="16-week timeline using 2-week sprints: environment setup, 3 build sprints, 2 integration sprints, 1 UAT sprint, go-live. Small senior team of 4 (2 engineers, 1 PM, 1 QA), all dedicated full-time.",
         milestones_table=[["Sprint","Focus","Weeks"],["0","Setup","2"],["1-3","Core build","6"],["4-5","Integrations","4"],["6","UAT & go-live","4"]],
         pricing_text="Total cost $265,000, fixed-bid, includes 6 months of support. Assumes client uses one of our 5 pre-built connector templates; custom connectors quoted separately.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$220,000"],["6-month support","$45,000"],["Total","$265,000"]],
         security="SOC 2 Type I certified (Type II planned next year). Data encrypted at rest and in transit. Standard RBAC; no dedicated security contact named for this engagement.",
         support="Business-hours support with 4-hour response SLA. Completed 3 similar migrations in the past 2 years, primarily for early-stage tech companies. One reference available.",
         experience=6.0, days_ago=17),
    dict(name="Meridian Support Systems", summary="Meridian Support Systems offers an enterprise-grade ticketing platform with a strong focus on regulated industries and audit-heavy environments.",
         solution="Monolithic-but-modular architecture optimized for auditability: every state change is logged immutably. Native integrations with major CRMs; custom integrations via a dedicated professional services team.",
         implementation="9-month conservative timeline prioritizing risk reduction: Discovery (6wk), Build (20wk), Compliance validation (4wk), UAT (4wk), Go-live (2wk). Team of 11 including a dedicated compliance officer.",
         milestones_table=[["Milestone","Week","Deliverable"],["Discovery sign-off","6","Requirements doc"],["Build complete","26","Feature-complete build"],["Compliance validation","30","Audit report"],["Go-live","36","Production cutover"]],
         pricing_text="Total cost $610,000, reflecting the compliance-heavy scope. Includes a dedicated compliance officer for the full engagement.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$480,000"],["Compliance validation","$70,000"],["Year 1 support","$60,000"],["Total","$610,000"]],
         security="ISO 27001, SOC 2 Type II, and HIPAA-ready controls. Immutable audit logs, field-level encryption, quarterly third-party audits. Named CISO liaison for the engagement.",
         support="24/7 support with 1-hour critical SLA and a dedicated technical account manager. 15 similar engagements in regulated industries (healthcare, finance) over 8 years. Four references, all in regulated sectors.",
         experience=9.5, days_ago=22),
    dict(name="Swift Helpdesk Co", summary="Swift Helpdesk Co provides the fastest and most affordable path to a modern ticketing system, ideal for budget-conscious teams.",
         solution="Pre-configured SaaS template with minimal customization. Standard integrations only (email, one CRM of choice). No custom development included.",
         implementation="6-week timeline: Setup (1wk), Configuration (2wk), Data import (1wk), Training (1wk), Go-live (1wk). Single implementation consultant assigned part-time.",
         milestones_table=[["Phase","Duration"],["Setup","1 week"],["Configuration","2 weeks"],["Data import","1 week"],["Training & go-live","2 weeks"]],
         pricing_text="Total Year 1 cost $72,000 for up to 150 seats. No customization included; add-ons priced separately.",
         pricing_table=[["Line item","Cost (USD)"],["Setup","$12,000"],["Year 1 licensing","$60,000"],["Total","$72,000"]],
         security="Standard cloud provider security. No specific certifications mentioned.",
         support="Email support only, 48-hour response target. First enterprise-scale migration for this vendor; no references provided.",
         experience=3.0, days_ago=15),
    dict(name="Highland Data Partners", summary="Highland Data Partners proposes a data-first migration emphasizing clean historical data migration and long-term reporting capability.",
         solution="Ticketing platform paired with a dedicated analytics warehouse, enabling deep historical reporting and trend analysis not available in most out-of-box tools.",
         implementation="20-week plan with heavy emphasis on data migration validation: Discovery (3wk), Data mapping & cleansing (6wk), Platform build (7wk), UAT (2wk), Go-live (2wk). Team of 6, including 2 dedicated data engineers.",
         milestones_table=[["Milestone","Week","Deliverable"],["Data mapping complete","9","Validated data map"],["Platform build complete","16","Feature-complete build"],["Go-live","20","Production cutover"]],
         pricing_text="Total cost $398,000, with roughly 40% allocated to data migration and validation work given the reporting focus.",
         pricing_table=[["Line item","Cost (USD)"],["Data migration & validation","$159,000"],["Platform implementation","$180,000"],["Year 1 support","$59,000"],["Total","$398,000"]],
         security="SOC 2 Type I certified. Data encrypted at rest; access control via SSO integration. Compliance certifications available on request but not yet finalized.",
         support="Business-hours support with a 6-hour response SLA. 5 similar data-heavy migrations completed in the last 3 years. Two references available, both citing strong reporting outcomes.",
         experience=6.5, days_ago=16),
    dict(name="Northstar Integration Group", summary="Northstar Integration Group specializes in complex, multi-system integrations for organizations with a large existing tool ecosystem.",
         solution="Integration-hub architecture connecting the new ticketing platform to 12+ existing internal systems via a custom middleware layer. Highly configurable but requires significant upfront integration mapping.",
         implementation="Estimated 8-10 months; exact duration depends on the number of legacy systems requiring integration, to be finalized after a technical discovery workshop. Team size scales with integration count (estimated 7-14 people).",
         milestones_table=[["Phase","Estimated duration"],["Technical discovery","4-6 weeks"],["Middleware build","16-24 weeks"],["Integration testing","8-12 weeks"],["Go-live","2-4 weeks"]],
         pricing_text="Base implementation estimated at $410,000, with each additional legacy system integration priced at $18,000-$35,000 depending on complexity. Final total to be confirmed after discovery.",
         pricing_table=[["Line item","Estimated cost (USD)"],["Base implementation","$410,000"],["Per-system integration","$18,000 - $35,000 each"],["Year 1 support (est.)","$55,000"]],
         security="Certifications vary by underlying platform components used; a consolidated security posture document will be provided during discovery. No unified certification held by Northstar itself.",
         support="Support model depends on final integration architecture; typically a dedicated integration engineer plus standard business-hours helpdesk. 7 similar multi-system integration projects completed. Three references available.",
         experience=7.0, days_ago=14),
    dict(name="Clearline Software", summary="Clearline Software offers a transparent, no-surprises implementation with clearly itemized pricing and a strong self-service documentation culture.",
         solution="Standard modular ticketing platform with a well-documented public API and a marketplace of pre-built, community-maintained integrations. Custom work is scoped and billed transparently as add-ons.",
         implementation="12-week timeline: Setup (2wk), Core configuration (5wk), Integrations from marketplace (3wk), UAT (1wk), Go-live (1wk). Team of 5, with a named point of contact throughout.",
         milestones_table=[["Phase","Duration"],["Setup","2 weeks"],["Core configuration","5 weeks"],["Integrations","3 weeks"],["UAT & go-live","2 weeks"]],
         pricing_text="Total cost $210,000, fully itemized with no bundled ambiguity. Every line item, including support tiers, is priced individually in the attached rate card.",
         pricing_table=[["Line item","Cost (USD)"],["Setup & configuration","$140,000"],["Marketplace integrations (3)","$30,000"],["Year 1 support (Standard tier)","$40,000"],["Total","$210,000"]],
         security="SOC 2 Type I certified. Standard encryption at rest and in transit. Security whitepaper available; no named security contact for this engagement size.",
         support="Extensive self-service documentation plus business-hours chat support, 8-hour SLA. 4 similar implementations completed. Two references, both citing pricing transparency as a strength.",
         experience=5.5, days_ago=13),
    dict(name="Pinnacle Enterprise Systems", summary="Pinnacle Enterprise Systems proposes a premium, fully white-glove implementation designed for large, complex organizations with zero tolerance for disruption.",
         solution="Enterprise architecture with dedicated failover infrastructure, active-active multi-region deployment, and a custom SLA-backed uptime guarantee (99.99%). Deep customization available across the entire platform.",
         implementation="10-month timeline with extensive parallel-running period before full cutover: Discovery (6wk), Build (20wk), Parallel run (8wk), Full cutover (2wk), Hypercare (4wk). Large dedicated team of 14 across engineering, QA, and change management.",
         milestones_table=[["Milestone","Week","Deliverable"],["Discovery complete","6","Signed requirements"],["Build complete","26","Feature-complete build"],["Parallel run complete","34","Validated parallel run report"],["Full cutover","36","Production cutover"]],
         pricing_text="Total cost $725,000, reflecting the premium white-glove scope, multi-region infrastructure, and extended parallel-run period.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$540,000"],["Multi-region infrastructure setup","$95,000"],["Year 1 premium support","$90,000"],["Total","$725,000"]],
         security="ISO 27001, SOC 2 Type II, PCI-DSS Level 1 certified. Dedicated security operations center, 24/7 monitoring, quarterly penetration testing, named CISO-level contact.",
         support="24/7/365 white-glove support with 30-minute critical SLA and a dedicated pod of support engineers. 20+ enterprise migrations completed over 15 years. Five references, all Fortune 1000 companies.",
         experience=9.8, days_ago=25),
    dict(name="Sagewell Consulting", summary="Sagewell Consulting proposes a pragmatic, mid-market-focused migration balancing cost discipline with solid technical fundamentals.",
         solution="Standard cloud-hosted ticketing platform with role-based workflows and the top 5 most commonly requested integrations pre-built (Slack, Salesforce, Jira, Zendesk import, generic email).",
         implementation="14-week timeline: Discovery (2wk), Build (7wk), Integration (3wk), UAT (1wk), Go-live (1wk). Team of 6 with a named delivery lead.",
         milestones_table=[["Phase","Duration"],["Discovery","2 weeks"],["Build","7 weeks"],["Integration","3 weeks"],["UAT & go-live","2 weeks"]],
         pricing_text="Total cost $255,000. Assumes client uses at least 3 of the 5 pre-built integrations; additional custom integrations quoted at $15,000 each.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$205,000"],["Year 1 support","$50,000"],["Total","$255,000"]],
         security="SOC 2 Type I certified. TLS in transit, encryption at rest. Standard RBAC. Annual internal security review, no third-party pen test mentioned.",
         support="Business-hours support, 4-hour response SLA. 5 similar mid-market migrations in 3 years. Two references available.",
         experience=6.8, days_ago=12),
    dict(name="Ironclad Secure Systems", summary="Ironclad Secure Systems specializes in high-security deployments for clients in defense, government, and critical infrastructure sectors.",
         solution="On-premises or private-cloud deployment option (no shared multi-tenant infrastructure). Air-gapped deployment available. Custom hardened OS images and strict change-control process for all updates.",
         implementation="11-month timeline reflecting security hardening and accreditation steps: Discovery & threat modeling (8wk), Build (24wk), Security accreditation (6wk), UAT (4wk), Go-live (2wk). Team of 10 including 2 dedicated security engineers.",
         milestones_table=[["Milestone","Week","Deliverable"],["Threat model sign-off","8","Threat model document"],["Build complete","32","Hardened build"],["Accreditation complete","38","Accreditation report"],["Go-live","44","Production cutover"]],
         pricing_text="Total cost $890,000, reflecting private/air-gapped infrastructure, security accreditation work, and dedicated security engineering staff.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation & hardening","$650,000"],["Security accreditation","$140,000"],["Year 1 support","$100,000"],["Total","$890,000"]],
         security="FedRAMP-aligned controls, ISO 27001, SOC 2 Type II. Air-gap capable. Dedicated security team with named leads for encryption, access control, and incident response.",
         support="24/7 cleared support staff, 15-minute critical SLA for accredited environments. 10 similar high-security deployments in 6 years. Three references, all government/defense sector (details available under NDA).",
         experience=9.2, days_ago=23),
    dict(name="QuickDesk Solutions", summary="QuickDesk Solutions offers an ultra-fast, no-frills deployment of our off-the-shelf ticketing product, ideal for teams that need to go live immediately.",
         solution="Out-of-the-box SaaS product with almost no configuration; relies on the client adapting workflows to the tool rather than the reverse. Two integrations included (email, one CRM).",
         implementation="4-week timeline: Setup (1wk), Data import (1wk), Training (1wk), Go-live (1wk). One implementation specialist assigned part-time alongside other accounts.",
         milestones_table=[["Phase","Duration"],["Setup","1 week"],["Data import","1 week"],["Training","1 week"],["Go-live","1 week"]],
         pricing_text="Total Year 1 cost $58,000 for up to 100 seats. Minimal customization included; most changes require a paid change order.",
         pricing_table=[["Line item","Cost (USD)"],["Setup","$8,000"],["Year 1 licensing","$50,000"],["Total","$58,000"]],
         security="Basic cloud security practices followed. No formal certifications currently held.",
         support="Community forum plus email support, no formal SLA stated. This would be among the vendor's first mid-size enterprise clients; no references provided.",
         experience=2.5, days_ago=11),
    dict(name="Beacon Field Services", summary="Beacon Field Services brings strong domain expertise from field-service and support operations, tailoring the ticketing platform for hybrid remote/on-site support teams.",
         solution="Ticketing platform extended with mobile field-technician workflows, GPS-tagged ticket updates, and offline-mode support for technicians in low-connectivity areas.",
         implementation="18-week timeline: Discovery (3wk), Core build (8wk), Mobile app customization (4wk), UAT (2wk), Go-live (1wk). Team of 7 including a dedicated mobile developer.",
         milestones_table=[["Milestone","Week","Deliverable"],["Discovery complete","3","Requirements doc"],["Core build complete","11","Feature-complete web build"],["Mobile customization complete","15","Field mobile app"],["Go-live","18","Production cutover"]],
         pricing_text="Total cost $312,000, including the mobile field-technician module which is not offered by most competitors.",
         pricing_table=[["Line item","Cost (USD)"],["Core platform","$180,000"],["Mobile field module","$90,000"],["Year 1 support","$42,000"],["Total","$312,000"]],
         security="SOC 2 Type I certified. Mobile app uses device-level encryption; standard TLS for API traffic. No dedicated security contact for this engagement.",
         support="Business-hours support with 6-hour SLA, extending to on-call for field-critical issues. 4 similar field-service migrations completed. Two references, both in utilities/field-service sectors.",
         experience=6.2, days_ago=10),
    dict(name="Fortify Cyber Solutions", summary="Fortify Cyber Solutions leads with security-by-design principles, positioning this migration as an opportunity to modernize both support tooling and the client's overall security posture.",
         solution="Zero-trust architecture with per-request authentication, continuous access evaluation, and a built-in vulnerability scanning pipeline integrated into the deployment process.",
         implementation="16-week timeline: Discovery & security baseline (3wk), Build (9wk), Security testing (2wk), UAT (1wk), Go-live (1wk). Team of 8 including 3 dedicated security specialists.",
         milestones_table=[["Milestone","Week","Deliverable"],["Security baseline set","3","Baseline document"],["Build complete","12","Feature-complete build"],["Security testing complete","14","Pen test report"],["Go-live","16","Production cutover"]],
         pricing_text="Total cost $445,000, with roughly a third of the budget allocated specifically to security architecture and testing work.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$300,000"],["Security architecture & testing","$95,000"],["Year 1 support","$50,000"],["Total","$445,000"]],
         security="ISO 27001, SOC 2 Type II certified. Zero-trust network model, continuous vulnerability scanning, quarterly red-team exercises. Dedicated CISO liaison for the engagement.",
         support="24/7 support with 1-hour critical SLA. 8 similar security-focused migrations in 5 years. Three references, all citing strong security posture improvements post-migration.",
         experience=8.0, days_ago=9),
    dict(name="Riverside Managed IT", summary="Riverside Managed IT proposes bundling this migration with an ongoing managed IT services relationship, offering long-term cost efficiency over a standalone project.",
         solution="Standard mid-tier ticketing platform, deployed and then fully managed by Riverside's team going forward, including proactive monitoring and monthly optimization reviews.",
         implementation="13-week timeline: Setup (3wk), Configuration (6wk), UAT (2wk), Go-live (2wk). Team of 5, transitioning to a smaller ongoing managed-services team post-launch.",
         milestones_table=[["Phase","Duration"],["Setup","3 weeks"],["Configuration","6 weeks"],["UAT","2 weeks"],["Go-live","2 weeks"]],
         pricing_text="Implementation cost $175,000, plus an ongoing managed services fee of $8,000/month thereafter (not included in the Year 1 total below, shown separately).",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$175,000"],["Ongoing managed services","$8,000/month"],["Year 1 implementation total","$175,000"]],
         security="SOC 2 Type I certified. Standard encryption and RBAC. Security posture reviewed as part of monthly managed-services check-ins rather than a one-time audit.",
         support="Fully managed support model, 4-hour response SLA, included as part of the managed-services fee. 6 similar migrations paired with managed services in 4 years. Two references available.",
         experience=6.0, days_ago=8),
    dict(name="Catalyst Digital Works", summary="Catalyst Digital Works proposes a rapid MVP-first approach, delivering core ticketing functionality quickly and iterating with the client afterward.",
         solution="Lean initial build covering core ticket creation, routing, and basic reporting, with an agreed post-launch roadmap for additional features (SLA automation, advanced analytics) delivered in later phases.",
         implementation="8-week MVP timeline: Discovery (1wk), MVP build (5wk), UAT (1wk), Go-live (1wk), followed by a separately-scoped Phase 2. Team of 4 for the MVP phase.",
         milestones_table=[["Phase","Duration"],["Discovery","1 week"],["MVP build","5 weeks"],["UAT & go-live","2 weeks"]],
         pricing_text="MVP phase cost $135,000. Phase 2 (SLA automation, advanced analytics) estimated separately at $90,000-$120,000 once scoped with the client post-launch.",
         pricing_table=[["Line item","Cost (USD)"],["MVP implementation","$135,000"],["Year 1 support (MVP scope)","$28,000"],["Total (MVP only)","$163,000"]],
         security="Standard cloud security practices; SOC 2 Type I in progress at time of proposal. Full compliance certifications targeted for completion post-MVP.",
         support="Business-hours support during MVP phase, 8-hour SLA. 3 similar MVP-first engagements completed. One reference available.",
         experience=5.2, days_ago=7),
    dict(name="Summit Professional Services", summary="Summit Professional Services offers a consulting-led migration emphasizing change management and user adoption alongside the technical implementation.",
         solution="Standard ticketing platform implementation paired with a formal organizational change management (OCM) workstream: stakeholder mapping, communications plan, and structured training program.",
         implementation="15-week timeline: Discovery & stakeholder mapping (3wk), Build (7wk), OCM & training design (3wk, parallel), UAT (1wk), Go-live & adoption support (1wk). Team of 7 including a dedicated OCM lead.",
         milestones_table=[["Milestone","Week","Deliverable"],["Stakeholder map complete","3","Stakeholder & comms plan"],["Build complete","10","Feature-complete build"],["Training materials complete","13","Training curriculum"],["Go-live","15","Production cutover"]],
         pricing_text="Total cost $298,000, including the dedicated change-management and training workstream often omitted by competitors.",
         pricing_table=[["Line item","Cost (USD)"],["Implementation","$210,000"],["Change management & training","$58,000"],["Year 1 support","$30,000"],["Total","$298,000"]],
         security="SOC 2 Type I certified. Standard encryption at rest and in transit. No dedicated security contact named for this engagement.",
         support="Business-hours support, 6-hour SLA, plus a 30-day post-launch adoption support period included at no extra cost. 5 similar engagements with formal OCM completed. Two references, both praising adoption outcomes.",
         experience=7.2, days_ago=6),
    dict(name="Delta Response Technologies", summary="Delta Response Technologies proposes a hybrid approach combining a proven commercial platform with light custom development for the client's most unique workflow needs.",
         solution="Commercial ticketing platform as the core, extended with a small custom module for the client's unique escalation workflow, built and maintained by Delta's engineering team.",
         implementation="17-week timeline: Discovery (3wk), Core platform setup (5wk), Custom module development (6wk), UAT (2wk), Go-live (1wk). Team of 7, including 2 developers dedicated to the custom module.",
         milestones_table=[["Milestone","Week","Deliverable"],["Discovery complete","3","Requirements doc"],["Core setup complete","8","Configured core platform"],["Custom module complete","14","Escalation module"],["Go-live","17","Production cutover"]],
         pricing_text="Total cost $370,000, with the custom escalation module accounting for roughly 30% of the budget.",
         pricing_table=[["Line item","Cost (USD)"],["Core platform setup","$150,000"],["Custom escalation module","$150,000"],["Year 1 support","$70,000"],["Total","$370,000"]],
         security="SOC 2 Type I certified for the core platform; the custom module inherits the same infrastructure security controls. No separate audit of the custom module has been performed.",
         support="Business-hours support with 4-hour SLA; custom module bugs handled by the original development team, extending response times for that component. 4 similar hybrid custom/commercial engagements completed. Two references available.",
         experience=6.9, days_ago=5),
]


def profile_to_sections(p: dict) -> list:
    return make_sections(p)


def main():
    for p in SUPPLIERS:
        filename = p["name"].replace(" ", "_") + "_RFP_Response.pdf"
        build_pdf(filename, p["name"], profile_to_sections(p))
    print(f"\nGenerated {len(SUPPLIERS)} supplier RFP PDFs in {OUT_DIR}")

    # Also emit a metadata CSV so it's easy to pre-fill the Streamlit upload
    # form (submission date, experience rating) without retyping by hand.
    import csv
    from datetime import date, timedelta
    meta_path = os.path.join(OUT_DIR, "_supplier_metadata.csv")
    with open(meta_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["supplier_name", "filename", "submission_date", "experience_rating"])
        for p in SUPPLIERS:
            filename = p["name"].replace(" ", "_") + "_RFP_Response.pdf"
            sub_date = (date.today() - timedelta(days=p["days_ago"])).isoformat()
            writer.writerow([p["name"], filename, sub_date, p["experience"]])
    print(f"Wrote metadata reference sheet: {meta_path}")


if __name__ == "__main__":
    main()
