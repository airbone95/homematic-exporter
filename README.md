# homematic-exporter
exportes metrics from your CCU for Prometheus

## prequisite
* CCU
* XML-API enabled

## variables
you can set the following environment variables:
* `HOMEMATIC_CCU_URL` **required**: URL to your CCU. Should contain Protocol e.g. `https://192.168.0.1`
* `HOMEMATIC_DISABLE_HTTPS_VERIFY` *default: false*: disable verification of HTTPS-Cert
* `HOMEMATIC_DISABLE_HTTPS_WARNING` *default: false*: disable warning from urllib3 if certificate verification fails
* `HOMEMATIC_POLL_INTERVAL` *default: 30*: interval in seconds your CCU gets polled
* `HOMEMATIC_TOKEN`: SID to use for API-Connection