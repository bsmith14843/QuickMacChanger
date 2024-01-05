import argparse
import getpass
import netifaces
import re
import subprocess
import shlex
import platform
import sys

# ANSI escape codes for colors
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def validate_sudo_password(password):
    # Customize this function based on your specific password validation criteria
    min_password_length = 8
    return len(password) >= min_password_length

def get_sudo_password():
    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        sudo_password = getpass.getpass(prompt="Enter your password: ")

        if validate_sudo_password(sudo_password):
            return sudo_password
        else:
            attempts += 1
            print(f"{RED}Incorrect password. {max_attempts - attempts} attempts remaining.{RESET}")

    print(f"{RED}\nFailed to enter correct credentials. Exiting.{RESET}")
    sys.exit(1)

def is_valid_mac_address(mac_address):
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$')
    return bool(re.match(mac_pattern, mac_address))

def change_mac_address(interface, new_mac, sudo_password):
    down_command = f'sudo -S ifconfig {interface} down'
    subprocess.run(shlex.split(down_command), input=sudo_password.encode())

    system_platform = platform.system()
    if system_platform == 'Linux':
        change_command = f'sudo -S ip link set dev {interface} address {new_mac}'
    elif system_platform == 'Darwin':
        change_command = f'sudo -S ifconfig {interface} ether {new_mac}'
    else:
        print(f"Unsupported platform: {system_platform}")
        return -1, None, "Unsupported platform"

    result = subprocess.run(shlex.split(change_command), capture_output=True)

    up_command = f'sudo -S ifconfig {interface} up'
    subprocess.run(shlex.split(up_command), input=sudo_password.encode())

    return result.returncode, result.stdout.decode('utf-8'), result.stderr.decode('utf-8')

def display_predefined_macs():
    predefined_macs = [
        {'mac': '0C:47:C9:3E:08:B1', 'device': 'Amazon Fire TV Stick'},
        {'mac': '00:23:C2:15:C6:67', 'device': 'Samsung Smart TV'},
        {'mac': '9C:76:13:3B:8F:4E', 'device': 'Ring Doorbell'},
        {'mac': '40:B9:3C:58:50:AD', 'device': 'Hewlett Packard Printer'}
    ]

    print("Choose a predefined MAC address:")
    for i, entry in enumerate(predefined_macs, 1):
        print(f"{i}. {entry['mac']} - {entry['device']}")

    while True:
        choice = input("Enter the number corresponding to your choice: ")

        if choice.isdigit() and 1 <= int(choice) <= len(predefined_macs):
            return predefined_macs[int(choice) - 1]['mac']
        else:
            print(f"{RED}Invalid choice. Please enter one of the {len(predefined_macs)} listed.{RESET}")

def check_wireless_interface():
    interface_name = 'wlan0'

    if interface_name in netifaces.interfaces():
        addresses = netifaces.ifaddresses(interface_name)

        if netifaces.AF_LINK in addresses:
            mac_address = addresses[netifaces.AF_LINK][0]['addr']
            print(f"\nThe wireless interface is {GREEN}active{RESET}. The MAC address currently set on that interface is: {mac_address}\n")

            change_mac = input("Would you like to change your MAC address? (yes/no): ").lower()

            if change_mac in ['yes', 'y']:
                sudo_password = get_sudo_password()

                use_predefined_mac = input("\nWould you like to use a predefined MAC address? (yes/no): ").lower()

                if use_predefined_mac in ['yes', 'y']:
                    new_mac = display_predefined_macs()
                    if new_mac and is_valid_mac_address(new_mac):
                        print(f"\nChanging MAC address to: {new_mac}")
                        return_code, stdout, stderr = change_mac_address(interface_name, new_mac, sudo_password)
                        if return_code == 0:
                            print(GREEN + "\nMAC address changed successfully." + RESET)
                        else:
                            print(f"\n{RED}Failed to change MAC address. Error: {stderr}{RESET}")
                    else:
                        print(f"{RED}Invalid MAC address. Not making any changes.{RESET}")
                else:
                    while True:
                        custom_mac = input("Enter your custom MAC address: ")
                        # Reformat the custom MAC address without colons if it's 12 characters
                        if len(custom_mac) == 12 and all(c in '0123456789ABCDEFabcdef' for c in custom_mac):
                            custom_mac = ':'.join([custom_mac[i:i+2] for i in range(0, 12, 2)])
                            print(f"\nReformatted MAC address to: {custom_mac}")
                            return_code, stdout, stderr = change_mac_address(interface_name, custom_mac, sudo_password)
                            if return_code == 0:
                                print(GREEN + "\nMAC address changed successfully." + RESET)
                            else:
                                print(f"\n{RED}Failed to change MAC address. Error: {stderr}{RESET}")
                            break
                        elif is_valid_mac_address(custom_mac):
                            print(f"\nChanging MAC address to: {custom_mac}")
                            return_code, stdout, stderr = change_mac_address(interface_name, custom_mac, sudo_password)
                            if return_code == 0:
                                print(GREEN + "\nMAC address changed successfully." + RESET)
                            else:
                                print(f"\n{RED}Failed to change MAC address. Error: {stderr}{RESET}")
                            break
                        else:
                            print(f"{RED}Invalid MAC address. Please enter a valid MAC address.{RESET}")
            else:
                print("You chose {RED}not{RED} to change the MAC address.")
        else:
            print("The wireless interface is active. But, somehow there is no MAC address found for the interface.")
    else:
        print(f"{RED}No{RESET} wireless interface found.")

def main():
    parser = argparse.ArgumentParser(description='MAC Address Changing Utility')
    parser.add_argument('-help', action='store_true', help='Brings up the full help command.')

    args = parser.parse_args()

    if args.help:
        print("This tool was created to easily change your MAC address. Either choose one of the predefined ones or use your own.\n\nYou may enter your own in either the XXXXXXXXXXXX or XX:XX:XX:XX:XX:XX formats.")
    else:
        check_wireless_interface()

if __name__ == "__main__":
    main()

