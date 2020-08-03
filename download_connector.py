import os
import click
from amp_client import AMP
from amp_client import utilities


@click.command()
@click.option("-u", "--user", prompt=True, help="Cisco Security account email address")
@click.option(
    "-p",
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Cisco Security account password",
)
@click.option(
    "-r",
    "--region",
    prompt=True,
    type=click.Choice(["APJC", "EU", "NAM"], case_sensitive=False),
    help="AMP for Endpoints region to authenticate to",
)
@click.option(
    "-o",
    "--operating-system",
    prompt=True,
    default="windows",
    type=click.Choice(["android", "linux", "mac", "windows"], case_sensitive=False),
    help="Desired operating system",
)
@click.option("-g", "--group", help="Name of the Group connector will be installed to")
@click.option(
    "-d",
    "--distro",
    type=click.Choice(["6", "7", "8"]),
    help="Linux distribution RHEL/CentOS 6, 7, or 8",
)
@click.option(
    "-nf",
    "--no-flash-scan",
    type=bool,
    is_flag=True,
    default=True,
    help="Disable flash scan on install",
)
@click.option(
    "-nr",
    "--non-redistributable",
    type=bool,
    is_flag=True,
    default=True,
    help="Use to download a non-redistributable Windows connector",
)
@click.option(
    "-pk",
    "--save-public-key",
    type=bool,
    is_flag=True,
    help="Save the GPG Public Key to verify the signing of the RPM",
)
def main(**kwags):
    """ Authenticate to AMP for Endpoints Console using a Cisco Security account
    Download connector for chosen OS, group, and settings and save to disk
    """
    user = kwags.get("user")
    password = kwags.get("password")
    region = kwags.get("region")
    group = kwags.get("group")
    operating_system = kwags.get("operating_system")
    distro = kwags.get("distro")
    save_public_key = kwags.get("save_public_key")

    # Complete Linux chosen distribution
    if distro and distro in ("6", "7", "8"):
        distro = "RHEL/CentOS " + distro

    if operating_system.lower() == "linux" and not distro:
        distro = "RHEL/CentOS " + click.prompt(
            "Linux distribution RHEL/CentOS", type=click.Choice(["6", "7", "8"])
        )

    # Create AMP for Endpoints client, check for Two Factor Auth secret as an environment variable
    amp_client = AMP(user, password, region, os.getenv("AMP_TOTP_SECRET"))

    # Authenticate to AMP for Endpoints
    amp_client.authenticate()
    print("Authentication Successful")

    # Save Cisco GPG Public Key
    if save_public_key:
        response = amp_client.download_gpg_key()
        with open("cisco.gpg", "w") as file:
            file.write(response.text)

    # Get Download Connector page from AMP Console and parse elements from it
    download_connector_page = amp_client.get_download_connector_page()

    if distro:
        linux_variants = utilities.parse_linux_options(download_connector_page)
        kwags["linux_variant_id"] = linux_variants[distro]

    os_product_id_url_path = utilities.parse_os_product_id_url_path(
        download_connector_page, operating_system
    )

    groups = utilities.parse_group_names_and_ids(download_connector_page)

    # Check for valid Group, prompt if not provided
    if not group:
        chosen_group = utilities.check_input("", groups, groups)
    else:
        group_list = list(groups.keys())
        chosen_group = utilities.check_input(group, group_list, group_list)
    print("\nGetting connector for group:", chosen_group)
    group_id = groups[chosen_group]

    # Get JSON that contains the connector version numbers for each OS in the chosen group
    install_package_data = amp_client.get_install_package_data(group_id)
    install_package_data = install_package_data.json()
    connector_versions = {
        connector["platform"]: connector["version"]
        for connector in install_package_data["product_download_versions"]
    }

    # Get the URL to download the Connector
    download_params = utilities.generate_download_params(**kwags)
    response = amp_client.get_connector_url(
        os_product_id_url_path, group_id, **download_params
    )
    download_path = response.json()["download_url"]

    # Download Connector
    response = amp_client.get_from_amp(download_path)
    filename = utilities.parse_file_name_from_url(response)
    filename = f"{filename[:-4]}_{connector_versions[operating_system]}{filename[-4:]}"
    print("Saving as:", filename)
    with open(filename, "wb") as file:
        file.write(response.content)


if __name__ == "__main__":
    main()
