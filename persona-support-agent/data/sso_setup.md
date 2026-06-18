# Single Sign-On (SSO) Setup

## Supported Providers
- Okta
- Azure Active Directory
- Google Workspace
- OneLogin

## SAML Configuration
1. Admin > Security > SSO > Enable SAML 2.0
2. Download the Adsparkx SP metadata XML
3. Upload to your IdP and configure ACS URL: `https://app.adsparkx.io/saml/acs`
4. Map IdP attributes: `email`, `firstName`, `lastName`, `groups`
5. Test with a non-admin account before enforcing

## Just-in-Time Provisioning
New users are auto-created on first SSO login when JIT is enabled.
Default role: Viewer. Admins can set role mappings by IdP group.

## Troubleshooting SSO
- **SAML signature invalid**: Ensure IdP certificate is current
- **User not provisioned**: Check email attribute mapping
- **Redirect loop**: Verify ACS URL matches exactly (including https)

## Enterprise Support
SSO setup assistance is included with Enterprise plans. Schedule via your account manager.
