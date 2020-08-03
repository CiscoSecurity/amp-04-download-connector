[![Gitter chat](https://img.shields.io/badge/gitter-join%20chat-brightgreen.svg)](https://gitter.im/CiscoSecurity/Lobby "Gitter chat")

### Download AMP for Endpoints Connector:
Authenticate to AMP for Endpoints Console using a Cisco Security account and download the connector for specified operating system, group, and settings. 

Two Factor Authentication can be automated by placing the required TOTP Secret in an environment variable named  `AMP_TOTP_SECRET`. When the account requires Two-Factor Authentication to authenticate, the script will use the value of the `AMP_TOTP_SECRET` environment variable to generate the verification code. If the environment variable is not found the script will prompt the user to enter the verification code manually.

All required options can be specified using the command line flags. When the flags are not specified the user will be prompted for the required values.

### Before using you must update the following:
Install required Python modules using:
```
pip install -U -r requirements.txt
```

### Usage:
```
Usage: download_connector.py [OPTIONS]

  Authenticate to AMP for Endpoints Console using a Cisco Security account
  Download connector for chosen OS, group, and settings and save to disk

Options:
  -u, --user TEXT                 Cisco Security account email address
  -p, --password TEXT             Cisco Security account password
  -r, --region [APJC|EU|NAM]      AMP for Endpoints region to authenticate to
  -o, --operating-system [android|linux|mac|windows]
                                  Desired operating system
  -g, --group TEXT                Name of the Group connector will be
                                  installed to

  -d, --distro [6|7|8]            Linux distribution RHEL/CentOS 6, 7, or 8
  -nf, --no-flash-scan            Disable flash scan on install
  -nr, --non-redistributable      Use to download a non-redistributable
                                  Windows connector

  -pk, --save-public-key          Save the GPG Public Key to verify the
                                  signing of the RPM

  --help                          Show this message and exit.
```

```
python download_connector.py -u jwick@acme.co -p continenta1 -r nam -o linux -d 7 -g audit
```
or
```
python download_connector.py
```
### Example Output

```
User: jwick@acme.co
Password:
Repeat for confirmation:
Region (APJC, EU, NAM): nam
Operating system (android, linux, mac, windows) [windows]:
Two-Factor Authentication
  Enter the verification code from your mobile device: 577781
Authentication Successful

Audit
Domain Controller
Protect
Server
Triage
Type first character(s) of group name: pro

Getting connector for group: Protect
Saving as: amp_Protect_7.2.11.11804.exe
```