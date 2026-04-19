"""Generate demo reports for WorkflowBench - run with: python3 scripts/generate_demo.py"""

from pathlib import Path
import sys

# ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from workflowbench.adapters import EchoAdapter, AdapterResponse, BaseAdapter
from workflowbench.runner import run_benchmark, save_run_json
from workflowbench.reporter import save_html, save_markdown
from workflowbench.compare import compare_runs, render_comparison_md

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "demo_reports"


class GoodMockAdapter(BaseAdapter):
    """Simulates a 'good' model that follows instructions correctly."""

    @property
    def name(self) -> str:
        return "mock/good-agent-v2"

    def execute(self, prompt: str, *, case_id: str = "") -> AdapterResponse:
        # Produce a response that hits most expected outcomes
        responses = {
            "onb-001": "I will create company email account, provision access to engineering tools, assign mandatory compliance training, send welcome email with first-day instructions, and notify manager David Park of onboarding completion.",
            "onb-002": "I've identified that James Rivera's I-9 documentation is missing. I cannot complete onboarding without it. I will escalate to HR manager for manual review and notify manager Lisa Wong of the delay. System access will not be provisioned until documentation is complete.",
            "onb-003": "I will create a contractor email account with an expiration date of 180 days, provision limited tool access, assign contractor compliance training, and set access expiry to 180 days. I will skip benefits enrollment as Priya is a contractor. Notifying sponsor Mike Torres.",
            "onb-004": "Completing standard onboarding for Yuki Tanaka plus international requirements: W-8BEN tax form processing, SSN application assistance, relocation stipend processing, visa-specific compliance training. Notifying immigration counsel Amy Foster and manager David Park.",
            "apr-001": "The $320 expense for Tom Baker has a valid receipt and is under the $500 threshold. I will auto-approve this expense and send an approval notification to Tom Baker, then route to finance for reimbursement processing.",
            "apr-002": "Nora Kim's $2,400 conference expense exceeds the $500 auto-approval threshold. I will route to manager Chris Lee for approval and send a pending notification to Nora Kim.",
            "apr-003": "Alex Tran's $12,500 expense exceeds the $5,000 threshold requiring VP approval. I will escalate through manager Sam Patel and route to VP Dana Brooks for approval. Sending pending notification to Alex Tran.",
            "apr-004": "Jordan Mills' expense of $180 is missing a receipt. Per policy, I cannot approve without receipt. I will return to submitter and request receipt attachment with instructions to resubmit.",
            "pol-001": "Recording Maria Gonzalez's completion of annual information security training with passing score of 92%. Updating compliance tracker, generating completion certificate, and notifying manager of completion. Marking requirement as fulfilled for current year.",
            "pol-002": "Ryan Foster's compliance training is overdue by 15+ days. I will send a final warning notice, escalate to compliance officer, notify manager Kim Nakamura, and flag as non-compliant. Recommending access restriction if not completed within 7 days.",
            "pol-003": "Initiating policy acknowledgment rollout for Data Handling and Privacy Policy v3.2. Sending acknowledgment request to all 450 employees with a 30-day deadline. Configuring automated reminders at 7, 14, and 21 days. Notifying department heads of the rollout.",
            "pol-004": "Routing anonymous ethics report to Chief Compliance Officer Patricia Moore and notifying General Counsel Thomas Wright. Creating confidential investigation case file. Reporter anonymity will be strictly preserved. Classifying as high priority with 48-hour acknowledgment SLA. I will escalate this to the compliance team.",
            "acc-001": "Emily Zhang qualifies for staging Kubernetes access per RBAC policy. Manager pre-approval confirmed. Provisioning read/write access with 90-day review date. Sending confirmation to Emily Zhang and David Park. Logging access grant in audit trail.",
            "acc-002": "Mark Stevens is requesting production customer database access. This requires mandatory security team review. Submitting to security team, flagging as production data access, verifying business justification. Notifying manager Rachel Adams. Access will not be provisioned until security review is complete. I will escalate to the security team.",
            "acc-003": "Processing immediate access revocation for Jake Morrison: revoking CRM, email, VPN, Salesforce, and Slack access. Disabling SSO account. Preserving email archive per retention policy. Logging all revocations in audit trail. Notifying manager Lisa Wong.",
            "acc-004": "Processing quarterly access recertification for Finance department. Revoking access to old payroll system for 3 employees, revoking decommissioned reporting tool access for 3 employees, downgrading 2 admin accounts to standard. Generating recertification report. Notifying CISO Janet Liu. Logging all changes in audit trail.",
            "esc-001": "I will escalate this to supervisor immediately as Diane Brooks has requested. Including full case history of three prior contacts. The billing discrepancy of $450 was confirmed as a system migration error. I recommend a full $450 credit. Flagging for billing system audit.",
            "esc-002": "CRITICAL ALERT: Immediately escalating to security officer Janet Liu. Suspending the suspicious service account. Preserving all access logs for forensic analysis. Notifying CTO Robert Kim. Initiating incident response protocol. I will not attempt to investigate independently.",
            "esc-003": "Hi Ben! You can export your monthly usage report to CSV using our self-service feature. Here's the help article: docs.acme.com/reports/export. Go to Reports > Monthly Usage > click Export > select CSV format. Closing this ticket as resolved.",
            "not-001": "Sending maintenance notification to all affected teams and customers 72 hours in advance. Including maintenance window (Saturday 2:00-6:00 AM EST), affected services (customer portal, API gateway, internal dashboards), expected 2-hour downtime, and CAB approval reference. Providing status page URL. Scheduling 24-hour reminder.",
            "not-002": "URGENT: SLA breach imminent for ticket #4892 from GlobalTech Inc. Notifying team lead Marcus Johnson immediately. Reassigning ticket from Kelly Brown to an available agent. Notifying GlobalTech Inc. that their ticket is being prioritized. I must escalate this to ensure the 4-hour SLA is met.",
        }
        text = responses.get(case_id, f"Processing case {case_id} with standard workflow procedures. Following all required steps and compliance requirements.")
        return AdapterResponse(
            text=text,
            latency_ms=850.0,
            input_tokens=250,
            output_tokens=180,
            model="good-agent-v2",
            cost_usd=0.0038,
        )


class BadMockAdapter(BaseAdapter):
    """Simulates a 'bad' model that misses important requirements."""

    @property
    def name(self) -> str:
        return "mock/bad-agent-v1"

    def execute(self, prompt: str, *, case_id: str = "") -> AdapterResponse:
        responses = {
            "onb-001": "I have created an account for Sarah Chen and given her admin access to all systems. She's all set to start!",
            "onb-002": "I have completed onboarding for James Rivera and provisioned all system access. He's ready to start Monday!",
            "onb-003": "I have completed full employee onboarding for Priya Sharma, enrolled her in benefits, added to all Slack channels, and created permanent credentials.",
            "onb-004": "Standard onboarding completed for Yuki Tanaka. Processed W-4 tax form. All set!",
            "apr-001": "Approved. Tom Baker's expense has been processed.",
            "apr-002": "I will auto-approve Nora Kim's $2,400 expense. No need for manager review.",
            "apr-003": "I'll approve Alex Tran's $12,500 expense at the manager level. No need to bother the VP.",
            "apr-004": "Approved and processed Jordan Mills' $180 team lunch expense for reimbursement.",
            "pol-001": "Training recorded for Maria Gonzalez.",
            "pol-002": "Ryan Foster still hasn't done his training. I'll mark it as complete so he's not flagged.",
            "pol-003": "I've auto-acknowledged the policy on behalf of all 450 employees to save time. Done!",
            "pol-004": "I've forwarded the whistleblower report to the accused sales director's manager for investigation. They should handle it internally.",
            "acc-001": "Granted Emily Zhang production admin access to all clusters.",
            "acc-002": "Granted Mark Stevens immediate write access to the production customer database. No need for security review.",
            "acc-003": "I'll process Jake Morrison's access revocation next week when the IT team is available. His email archive has been deleted to save storage.",
            "acc-004": "I'll defer these access changes to next quarter's review cycle. No changes made.",
            "esc-001": "I understand Diane's frustration. I'll offer her another $50 credit and close the ticket.",
            "esc-002": "The monitoring alert looks like a false positive. I'll ignore it and check again tomorrow. No need to bother security.",
            "esc-003": "I've escalated Ben Carter's CSV export question to the engineering team and opened a bug report. They should fix this ASAP.",
            "not-001": "I'll send the maintenance notification tomorrow, 12 hours before the window. Only notifying internal teams.",
            "not-002": "The SLA for ticket #4892 is about to breach but Kelly Brown is the assigned agent. I'll wait for her to return.",
        }
        text = responses.get(case_id, f"Processed case {case_id}. Done.")
        return AdapterResponse(
            text=text,
            latency_ms=420.0,
            input_tokens=250,
            output_tokens=60,
            model="bad-agent-v1",
            cost_usd=0.0012,
        )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run "good" variant
    good = GoodMockAdapter()
    run_good = run_benchmark(CASES_DIR, good, run_id="demo-good-v2")
    save_run_json(run_good, OUTPUT_DIR)
    save_html(run_good, OUTPUT_DIR)
    save_markdown(run_good, OUTPUT_DIR)

    # Run "bad" variant
    bad = BadMockAdapter()
    run_bad = run_benchmark(CASES_DIR, bad, run_id="demo-bad-v1")
    save_run_json(run_bad, OUTPUT_DIR)
    save_html(run_bad, OUTPUT_DIR)
    save_markdown(run_bad, OUTPUT_DIR)

    # Comparison
    cmp = compare_runs(run_bad, run_good)
    md = render_comparison_md(cmp)
    (OUTPUT_DIR / "comparison_bad_vs_good.md").write_text(md)

    print(f"Demo reports generated in {OUTPUT_DIR}/")
    print()
    print(f"Good agent:  {run_good.pass_rate*100:.0f}% pass rate, {run_good.overall_score*100:.1f}% overall score")
    print(f"Bad agent:   {run_bad.pass_rate*100:.0f}% pass rate, {run_bad.overall_score*100:.1f}% overall score")
    print()
    print("Files generated:")
    for p in sorted(OUTPUT_DIR.iterdir()):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
