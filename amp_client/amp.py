from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import requests
from amp_client import utilities


class AMP:

    session = requests.Session()

    def __init__(self, user, password, region, totp_secret=None):
        self.user = user
        self.password = password
        self.region = region
        self.console_url = utilities.region_mapping(region)
        self.base_url = f"https://{self.console_url}"
        self.authenticity_token = None
        self.totp_secret = totp_secret

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }

        self.session.headers.update(headers)

    def authenticate(self):
        """Authenticate to AMP for Endpoints using a Cisco Security Account and the SAML 2.0 Flow
        """

        # Start Cisco Security SAML Flow:
        response = self.session.get(f"https://{self.console_url}/")
        query_params = utilities.parse_samlrequest_query_params(response)

        # Parse HTML and extract Authenticity Token
        authenticity_token = utilities.parse_html_for_value(
            response, "input", {"name": "authenticity_token"}
        )

        # Authenticate to Cisco Security IdP
        data = {
            "authenticity_token": authenticity_token,
            "user[email]": self.user,
            "user[password]": self.password,
        }

        # Save the Cisco Security IdP hostname
        idp_host = urlsplit(response.url).netloc
        response = self.session.post(
            f"https://{idp_host}/session", params=query_params, data=data
        )

        # Enter Two Factor Authentication Verification Code if required
        if urlsplit(response.url).path == "/tfa/new":
            # Parse HTML and extract Form Action and Authenticity Token
            form_action = utilities.parse_html_for_value(
                response, "form", {"id": "tfa-login-form"}, "action"
            )
            authenticity_token = utilities.parse_html_for_value(
                response, "meta", {"name": "csrf-token"}, "content"
            )

            # Split URL into componenets and build URL with Form Action
            split_url = urlsplit(response.url)
            url = urlunsplit((split_url.scheme, split_url.netloc, form_action, "", ""))

            data = {
                "authenticity_token": authenticity_token,
                "tsv[verification_code]": utilities.get_totp(self.totp_secret),
                "tsv[remember]": 0,
            }

            response = self.session.post(url, data=data)

        # Parse HTML and extract Authenticity Token, SAMLResponse, and Form Action URL
        authenticity_token = utilities.parse_html_for_value(
            response, "input", {"name": "authenticity_token"}
        )
        samlresponse = utilities.parse_html_for_value(
            response, "input", {"name": "SAMLResponse"}
        )
        form_action = utilities.parse_html_for_value(
            response, "form", {"class": "user-invisible"}, "action"
        )

        # Complete Cisco Security SAML 2.0 flow
        data = {"authenticity_token": authenticity_token, "SAMLResponse": samlresponse}
        response = self.session.post(form_action, data=data)

        # Parse HTML and extract Authenticity Token that is used to interact with AMP Console
        authenticity_token = utilities.parse_html_for_value(
            response, "meta", {"name": "csrf-token"}, "content"
        )
        self.authenticity_token = authenticity_token

    def get_download_connector_page(self):
        """Gets the Download Connector page which is parsed for:
        Groups, Linux Product Variant IDs, and Connector Download Button Path
        """
        url_path = "/download_connector"
        return self.get_from_amp(url_path)

    def get_install_package_data(self, group_id):
        """Gets JSON that contains the connector version numbers for each OS in the chosen group
        Equivalent to selecting a group on the Download Connector page
        """
        url_path = f"/install_packages/group_data/{group_id}"
        return self.get_from_amp(url_path)

    def download_gpg_key(self):
        """Download the GPG Public Key used to verify the signing of the RPM connector
        """
        url_path = "/gpg_keys/cisco.gpg"
        return self.get_from_amp(url_path)

    def get_connector_url(self, path, group_id, **kwags):
        """Submits connector parameters to AMP and gets a the URL used to download the connector
        Equivalent to clicking the "Download" button on the Connector Download page
        """
        data = {
            "authenticity_token": self.authenticity_token,
            "group_id": group_id,
        }

        data.update(kwags)

        url = urljoin(self.base_url, path)
        response = self.session.post(url, data=data)

        return response

    def get_from_amp(self, path):
        """Downloads the connector install package
        """
        url = urljoin(self.base_url, path)
        response = self.session.get(url)
        return response
