from urllib.parse import urlsplit
from urllib.parse import parse_qsl

import pyotp
from bs4 import BeautifulSoup


def prompt_for_group_name():
    """Prompt user for group name
    """
    return input("Type first character(s) of group name: ")


def get_groups_starting_with(user_input, groups):
    """Return list of group names that start with the characters provided
    """
    return [group for group in groups if group.lower().startswith(user_input.lower())]


def get_exact_match(user_input, groups):
    """Return an exact match from the groups
    """
    lower_groups = [group.lower() for group in groups]
    if user_input.lower() in lower_groups:
        return groups[lower_groups.index(user_input.lower())]


def check_input(user_input, groups, original_groups):
    """Check user input against group names matching on the first characters of the group name
    If more than one name starts with the characters provided, present a list of matching names
    If no group name starts with the characters provided, present the full list
    """
    user_input = user_input.strip()

    exact_match = get_exact_match(user_input, groups)
    if exact_match:
        return exact_match

    matching_groups = get_groups_starting_with(user_input, groups)

    if len(matching_groups) == 1:
        return matching_groups[0]

    groups = original_groups if len(matching_groups) == 0 else matching_groups
    print()
    print("\n".join(sorted(groups)))
    return check_input(prompt_for_group_name(), groups, original_groups)


def region_mapping(region):
    """Map the user supplied region to the hostname for the AMP for Endpoints console
    """
    region_map = {
        "apjc": "console.apjc.amp.cisco.com",
        "eu": "console.eu.amp.cisco.com",
        "nam": "console.amp.cisco.com",
    }
    return region_map[region.lower()]


def get_totp(totp_secret):
    """ Check if Two Factor Verification Code can be generated automatically. If not, prompt user to enter the code
    """
    if totp_secret:
        verification_code = generate_totp(totp_secret)
    else:
        verification_code = input(
            "Two-Factor Authentication\n  Enter the verification code from your mobile device: "
        )

    return verification_code


def generate_totp(totp_secretp):
    """Return current OTP
    """
    amp_totp = pyotp.TOTP(totp_secretp)
    return amp_totp.now()


def parse_html_for_value(response, name, attrs, get="value"):
    """Take response object and parse HTML for a specific value
    """
    soup = BeautifulSoup(response.text, features="html.parser")
    return soup.find(name, attrs).get(get)


def parse_samlrequest_query_params(response):
    """Extract Query Params from SAML 2.0 Flow remove un-needed parameters and return SAMLRequest
    """
    query_params = dict(parse_qsl(urlsplit(response.url).query))
    del query_params["SigAlg"]
    del query_params["Signature"]
    return query_params


def parse_os_product_id_url_path(response, platform):
    """Parse Download Connector Page for URL path from OS / Platform download button
    """
    soup = BeautifulSoup(response.text, features="html.parser")
    data_platform = {"data-platform": platform}
    button_class = {"class": "btn btn-default download"}
    platform_div = soup.find("div", data_platform)
    platform_url = platform_div.find("button", button_class).get("data-url")
    return platform_url


def parse_linux_options(response):
    """Parse Download Connector Page for Linux product variant GUIDs
    """
    soup = BeautifulSoup(response.text, features="html.parser")
    linux_options = soup.find("div", {"class": "product-variants"}).find_all("option")
    return {option.text: option.attrs["value"] for option in linux_options}


def parse_group_names_and_ids(response):
    """Parse Download Connector Page for Group names and IDs
    """
    soup = BeautifulSoup(response.text, features="html.parser")
    group_options = soup.find("div", {"class": "select-group"}).find_all("option")
    groups = {option.text: option.attrs["value"] for option in group_options}
    return groups


def generate_download_params(**kwags):
    """Generate parameters used when building connector for download
    """
    connector_params = {}
    if kwags.get("non_redistributable"):
        connector_params["WindowsProduct[installer_type]"] = 2

    if kwags.get("no_flash_scan"):
        flash_scan = {
            "WindowsProduct[scan_on_install]": "1",
            "MacProduct[scan_on_install]": "1",
            "LinuxProduct[scan_on_install]": "1",
        }

        connector_params.update(flash_scan)

    if kwags.get("linux_variant_id"):
        connector_params["LinuxProduct[product_variant_id]"] = kwags["linux_variant_id"]

    return connector_params


def parse_file_name_from_url(response):
    """Parse URL for connector file name
    """
    split_url = urlsplit(response.url)
    filename = split_url.path.split("/")[-1:][0]
    return filename
