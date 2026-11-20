
import os
import xml.etree.ElementTree as ET
import smtplib
from email.message import EmailMessage
from html import escape

REPORT_FILE = "AWSTestExecutions/junit-results.xml"

# Read Pytest results
tree = ET.parse(REPORT_FILE)
root = tree.getroot()

test_cases = root.findall(".//testcase")

total = len(test_cases)
passed = failed = skipped = 0
rows = []

for test in test_cases:
    name = test.get("name", "Unknown")
    classname = test.get("classname", "")
    duration = float(test.get("time", 0))

    failure = test.find("failure")
    error = test.find("error")
    skip = test.find("skipped")

    if failure is not None or error is not None:
        status = "FAILED"
        failed += 1
        detail = failure if failure is not None else error
        message = detail.get("message", "Test failed")
    elif skip is not None:
        status = "SKIPPED"
        skipped += 1
        message = skip.get("message", "Skipped")
    else:
        status = "PASSED"
        passed += 1
        message = "-"

    rows.append(f"""
      <tr>
        <td>{escape(classname + '::' + name)}</td>
        <td>{status}</td>
        <td>{duration:.2f}s</td>
        <td>{escape(message[:300])}</td>
      </tr>
    """)

percentage = (passed / total * 100) if total else 0
overall = "PASSED" if failed == 0 else "FAILED"

html = f"""
<html>
<body style="font-family:Arial,sans-serif;">
<h2>AWS Infrastructure Testing - Execution Report</h2>

<h3>Execution Summary</h3>
<table border="1" cellpadding="8" cellspacing="0">
<tr><th>Metric</th><th>Result</th></tr>
<tr><td>Total Test Cases</td><td>{total}</td></tr>
<tr><td>Passed</td><td>{passed}</td></tr>
<tr><td>Failed</td><td>{failed}</td></tr>
<tr><td>Skipped</td><td>{skipped}</td></tr>
<tr><td>Pass Percentage</td><td>{percentage:.2f}%</td></tr>
<tr><td>Overall Status</td><td><b>{overall}</b></td></tr>
</table>

<h3>Detailed Test Results</h3>
<table border="1" cellpadding="8" cellspacing="0">
<tr>
<th>Test Case</th>
<th>Status</th>
<th>Duration</th>
<th>Details</th>
</tr>
{''.join(rows)}
</table>

<p>Platform: GitHub Actions / Ubuntu</p>
<p>Repository: AWS-Infrastructure-Testing</p>
<p>Regards,<br>QA Automation Team</p>
</body>
</html>
"""

# Prepare email
msg = EmailMessage()
msg["Subject"] = f"AWS Test Execution Report - {overall}"
msg["From"] = os.environ["MAIL_USERNAME"]
msg["To"] = os.environ["MAIL_TO"]
msg.set_content("Please view this email in an HTML-compatible email client.")
msg.add_alternative(html, subtype="html")

# Send email
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(
        os.environ["MAIL_USERNAME"],
        os.environ["MAIL_APP_PASSWORD"]
    )
    smtp.send_message(msg)

print("Test execution report emailed successfully.")
