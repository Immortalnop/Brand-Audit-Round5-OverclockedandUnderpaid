"""Verified standard-library TLS with optional administrator-supplied CA roots."""
import os
import ssl
import sys


def create_context():
    context = ssl.create_default_context()
    # Permit legacy Diffie-Hellman parameters (e.g. 1024-bit) used by older servers without disabling certificate verification
    try:
        context.set_ciphers('DEFAULT@SECLEVEL=1')
    except ssl.SSLError:
        pass
    # Additional trust is an explicit local setting, never downloaded from a target.
    bundle = os.environ.get('AUDIT_CA_BUNDLE')
    if bundle:
        context.load_verify_locations(cafile=bundle)
    return context


def environment_summary():
    return {
        'python_version': sys.version.split()[0],
        'openssl_version': ssl.OPENSSL_VERSION,
        'connection_route': 'direct_validated_ip',
        'extra_ca_bundle_configured': bool(os.environ.get('AUDIT_CA_BUNDLE')),
        'openssl_ca_override_configured': any(os.environ.get(k) for k in ('SSL_CERT_FILE','SSL_CERT_DIR')),
        'proxy_environment_present': any(os.environ.get(k) for k in
            ('HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','https_proxy','http_proxy','all_proxy')),
        'proxy_policy': 'Environment proxies are not used by this pinned transport. Their presence does not prove interception.',
        'verification_policy': 'Default certificate-chain and hostname verification; no insecure fallback.',
    }
