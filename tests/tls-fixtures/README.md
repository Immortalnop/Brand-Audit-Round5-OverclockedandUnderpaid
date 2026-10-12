# Public local test fixtures

These certificates and the server key are public, generated test data, valid for
localhost fixture testing only. Never install this CA in a system trust store or
use this key for deployment. The private CA signing key is not included. Runtime
code never loads these files automatically. The tests configure the CA explicitly
and bind the server only to loopback. Certificates expire in 2036; regenerate them
for future test maintenance without relaxing verification.
