import datetime
import ipaddress
import os
import socket
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_self_signed_cert():
    cert_dir = os.path.dirname(__file__)
    key_path = os.path.join(cert_dir, "key.pem")
    cert_path = os.path.join(cert_dir, "cert.pem")
    
    if os.path.exists(key_path) and os.path.exists(cert_path):
        print("Certificates already exist.")
        return

    print("Generating self-signed SSL certificate...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"3DGS Local Server"),
    ])
    
    alt_names = [
        x509.DNSName(u"localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    
    try:
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        for ip in local_ips:
            try:
                alt_names.append(x509.IPAddress(ipaddress.ip_address(ip)))
            except:
                pass
    except:
        pass

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName(alt_names),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    print("SSL Certificates (cert.pem, key.pem) generated successfully!")

if __name__ == "__main__":
    generate_self_signed_cert()
