"""API utils."""

import ipaddress
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_tls_certificate(
    device_uid: str, device_ip: str
) -> dict[str, str]:
    """Generate a self-signed TLS certificate with device IP in SAN.

    device_uid: the uid of the device.
    device_ip: the ip of the device.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MyCompany"),
            x509.NameAttribute(NameOID.COMMON_NAME, device_uid),
        ]
    )

    san_list = [x509.IPAddress(ipaddress.ip_address(device_ip))]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .sign(private_key, hashes.SHA256())
    )

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM).decode()

    return {"certificate": cert_pem, "private_key": private_key_pem}
