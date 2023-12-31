Load extra client authentication or trusted CA certificates into the default Home Assistant TLS contexts.

```yaml
extra_tls_certificates:
  client:
    - cert: config/HomeAssistant.cert.pem
      key: config/HomeAssistant.key.pem
      password: !secret homeassistant_client_cert_pw

  ca:
    - config/InternalCA.cert.pem
```
