"""Generate the required password reset PDF for the knowledge base."""

from pathlib import Path

from fpdf import FPDF

CONTENT = """
PASSWORD RESET GUIDE
Adsparkx Customer Support

OVERVIEW
If you forgot your password or suspect unauthorized access, follow this guide
to securely reset your Adsparkx account credentials.

METHOD 1: SELF-SERVICE RESET
1. Go to https://app.adsparkx.io/login
2. Click "Forgot Password?"
3. Enter the email address associated with your account
4. Check your inbox for a reset link (expires in 60 minutes)
5. Click the link and create a new password meeting security requirements:
   - Minimum 12 characters
   - Uppercase, lowercase, number, and symbol required
6. Log in with your new password

METHOD 2: ADMIN-ASSISTED RESET (Enterprise)
Enterprise admins can force a password reset from Admin > Team > Select User >
Reset Password. The user receives an email with a temporary link valid for 24 hours.

METHOD 3: ACCOUNT RECOVERY WITHOUT EMAIL ACCESS
If you no longer have access to your registered email:
1. Contact support@adsparkx.io from a company domain email
2. Provide: full name, account ID, last four digits of payment method
3. Complete identity verification (24-48 hour processing)
4. A support agent will initiate a secure recovery workflow

TROUBLESHOOTING
- Reset email not received: Check spam/junk folders and email filters
- Link expired: Request a new reset from the login page
- "Invalid token" error: Ensure you are using the most recent reset email
- SSO users: Password reset applies only to local accounts; use your IdP for SSO login

SECURITY RECOMMENDATIONS
After resetting your password:
- Enable two-factor authentication (Account > Security > 2FA)
- Revoke unused API keys (Dashboard > Settings > API Keys)
- Review active sessions and sign out unknown devices

For urgent security concerns, email security@adsparkx.io immediately.
"""


def generate_pdf(output_path: Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for line in CONTENT.strip().split("\n"):
        safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
        pdf.cell(0, 6, safe_line, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(output_path))
    print(f"Generated {output_path}")


if __name__ == "__main__":
    generate_pdf(Path(__file__).resolve().parent.parent / "data" / "password_reset_guide.pdf")
