import argparse
import getpass
import netifaces
import re
import subprocess
import shlex
import platform
import sys
import os
import time
import random

version = 'Version: 1.0 Author:bsmith14843'

#colors
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

PREDEFINED_MACS_FILE = 'predefined_macs.txt'


def display_random_word_art():
    word_art_options = [
        """
           __    __     ____    ____    _____ _____   ____     ____  _________ ___________    
           \ \  / /    (    )  / ___)  / ____(  __ \ / __ \   / __ \(_   _____) ___(   __ \   
           () \/ ()    / /\ \ / /     ( (___  ) )_) ) /  \ \ / /  \ \ ) (___ ( (__  ) (__) )  
           / _  _ \   ( (__) | (       \___ \(  ___( ()  () | ()  () |   ___) ) __)(    __/   
          / / \/ \ \   )    (( (           ) )) )  ( ()  () | ()  () )) (    ( (    ) \ \  _  
         /_/      \_\ /  /\  \\ \___   ___/ /( (    \ \__/ / \ \__/ /(   )    \ \__( ( \ \_)) 
        (/          \)__(  )__\\____) /____/ /__\    \____/   \____/  \_/      \____)_) \__/  
                                                                                     
        """,
        """
        ███╗   ███╗ █████╗  ██████╗    ███████╗██████╗ ██████╗  ██████╗ ███████╗███████╗██████╗ 
        █████╗ ████║██╔══██╗██╔════╝   ██╔════╝██╔═██╗██╔═══██╗██╔═══██╗██╔════╝██╔════╝██╔══██╗
        ██╔██╗██╔██║███████║██║        █████████████╔╝██║   ██║██║   ██║█████╗  █████╗  ██████╔╝
        ██║╚████╔╝██║██╔═██║██║        ╚════██║██╔═══╝██║   ██║██║   ██║██╔══╝  ██╔══╝  ██╔══██╗
        ██║ ╚██╔╝ ██║██║ ██║╚██████╗   ███████║██║    ╚██████╔╝╚██████╔╝██║     ███████╗██║  ██║
        ╚═╝  ╚═╝  ╚═╝╚═  ╚═╝ ╚═════╝   ══════╝╚═╝      ╚═════╝  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝
        """ ,
        """
            ___  ___ ___  _____   ___________ _____ ___________ ___________ 
            |  \/  |/ _ \/  __ \ /  ___| ___ \  _  |  _  |  ___|  ___| ___ \\
            | .  . / /_\ \ /  \/ \ `--.| |_/ / | | | | | | |_  | |__ | |_/ /
            | |\/| |  _  | |      `--. \  __/| | | | | | |  _| |  __||    / 
            | |  | | | | | \__/\ /\__/ / |   \ \_/ | \_/ / |   | |___| |\ \\ 
            \_|  |_|_| |_/\____/ \____/\_|    \___/ \___/\_|   \____/\_| \_|
            
        """ 
    ]

    #lenght of ascii art
    max_line_length = max(len(line) for art_piece in word_art_options for line in art_piece.split('\n'))

    #Pads
    padding_length = max(0, (max_line_length - len(version)) // 2)

    #centered line
    centered_version = ' ' * padding_length + version

    #make art
    centered_word_art = [art_piece + '\n' + centered_version for art_piece in word_art_options]

    #print art
    selected_word_art = random.choice(centered_word_art)
    print(selected_word_art)



def get_sudo_password(): #stealing your password obviously
    return getpass.getpass(prompt="Enter your password (this program may not work with an invalid password): ")

def is_valid_mac_address(mac_address): #validating format of MAC
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$')
    return bool(re.match(mac_pattern, mac_address))

def read_predefined_macs(): #reading and parsing from defined list
    try:
        with open(PREDEFINED_MACS_FILE, 'r') as file:
            lines = file.readlines()
            predefined_macs = []

            for line in lines:
                
                if not line.startswith('#'):
                    parts = line.strip().split('||')
                    if len(parts) == 2:
                        mac_address = parts[0].strip()
                        device_name = parts[1].strip()
                        predefined_macs.append({'mac': mac_address, 'device': device_name})

            return predefined_macs
    except FileNotFoundError:
        return []


def write_predefined_macs(predefined_macs): #Adding to the list of defined macs 
    with open(PREDEFINED_MACS_FILE, 'w') as file:
        for entry in predefined_macs:
            file.write(f"{entry['mac']} || {entry['device']}\n")

def change_mac_address(interface, new_mac, sudo_password): #doin werk changing address with provided sudo pass
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

def display_predefined_macs(predefined_macs): #Choose from list of MACs
    print("\nChoose a predefined MAC address:")
    for i, entry in enumerate(predefined_macs, 1):
        print(f"{i}. {entry['mac']} - {entry['device']}")

def add_to_predefined_macs(predefined_macs, new_mac, device_name):
    predefined_macs.append({'mac': new_mac, 'device': device_name})
    print(f"\nMAC address {GREEN}{new_mac}{RESET} has been saved to the address list as {GREEN}{device_name}{RESET}.")
    write_predefined_macs(predefined_macs)

def get_available_interfaces(): #basically ifconfig to show interfaces and return names of the ones avail.
    return [iface for iface in netifaces.interfaces() if iface != 'lo']

def display_available_interfaces(interfaces): #displays avail interfaces
    print("You can change the MAC address on the following interfaces:")
    for i, iface in enumerate(interfaces, 1):
        print(f"{i}. {iface}")

def choose_network_interface(): #Start of program. Displays avail interfaces for the user.
    interfaces = get_available_interfaces()

    if not interfaces:
        print(f"{RED}No network interfaces found.{RESET}")
        sys.exit(1)

    display_available_interfaces(interfaces)

    while True:
        choice = input("If you would like to continue, please enter an interface. To quit press 'q': ")

        if choice.lower() == 'q':
            print(f"You chose {RED}not{RESET} to change the MAC address. Exiting program.")
            sys.exit(0)
        elif choice.isdigit() and 1 <= int(choice) <= len(interfaces):
            return interfaces[int(choice) - 1]
        elif choice in interfaces:
            return choice
        else:
            print(f"{RED}Invalid choice. Please enter a valid interface or 'q' to quit.{RESET}")

def check_wireless_interface(predefined_macs): #quite obvious based off name lol
    interface_name = choose_network_interface()

    addresses = netifaces.ifaddresses(interface_name)

    if netifaces.AF_LINK in addresses:
        mac_address = addresses[netifaces.AF_LINK][0]['addr']
        print(f"\nYou have selected {GREEN}{interface_name}{RESET}. The MAC address currently set on that interface is: {mac_address}\n")

        sudo_password = get_sudo_password()

        use_predefined_mac = input("\nWould you like to use a predefined MAC address? (yes/no): ").lower()

        if use_predefined_mac in ['yes', 'y']:
            display_predefined_macs(predefined_macs)

            choice = input("Enter the number corresponding to your choice: ")

            if choice.isdigit() and 1 <= int(choice) <= len(predefined_macs):
                new_mac = predefined_macs[int(choice) - 1]['mac']
                print(f"\nChanging MAC address to: {new_mac}")
                return_code, stdout, stderr = change_mac_address(interface_name, new_mac, sudo_password)
                if return_code == 0:
                    print(GREEN + "\nMAC address changed successfully." + RESET)
                else:
                    print(f"\n{RED}Failed to change MAC address. Error: {stderr}{RESET}")
            else:
                print(f"{RED}Invalid choice. Not making any changes.{RESET}")
        else:
            while True:
                custom_mac = input("Enter your custom MAC address: ")
                if len(custom_mac) == 12 and all(c in '0123456789ABCDEFabcdef' for c in custom_mac):
                    custom_mac = ':'.join([custom_mac[i:i+2] for i in range(0, 12, 2)])
                    print(f"\nI reformatted your MAC address to {custom_mac} since you couldn't enter it right.")
                    return_code, stdout, stderr = change_mac_address(interface_name, custom_mac, sudo_password)
                    if return_code == 0:
                        print(GREEN + "\nMAC address changed successfully." + RESET)
                    else:
                        print(f"\n{RED}Failed to change MAC address. Error: {stderr}{RESET}")

                    save_custom_mac = input("Would you like to save the MAC address to the list (yes/no)?: ").lower()
                    if save_custom_mac in ['yes', 'y']:
                        device_name = input("Enter a name for this MAC: ")
                        add_to_predefined_macs(predefined_macs, custom_mac, device_name)
                    break  # Ensure we break out of the loop after handling the custom MAC address
                elif is_valid_mac_address(custom_mac):
                    print(f"\nChanging MAC address to: {custom_mac}")
                    return_code, stdout, stderr = change_mac_address(interface_name, custom_mac, sudo_password)
                    if return_code == 0:
                        print(GREEN + "\nMAC address changed successfully." + RESET)
                    else:
                        print(f"\n{RED}Failed to change MAC address. Error: {stderr}{RESET}")
                    # Indent the lines below to include them in the loop
                    save_custom_mac = input("Would you like to save the MAC address to the list (yes/no)?: ").lower()
                    if save_custom_mac in ['yes', 'y']:
                        device_name = input("Enter a name for this MAC: ")
                        add_to_predefined_macs(predefined_macs, custom_mac, device_name)
                    break
                else:
                    print(f"{RED}Invalid MAC address. Please enter a valid MAC address.{RESET}")

    else:
        print("The selected network interface is active. But, somehow there is no MAC address found for the interface.")

def main():
    
    # Display random word art
    display_random_word_art()

    # Pause for 2 seconds
    time.sleep(2)

    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    # Main Logic
    parser = argparse.ArgumentParser(description='MAC Address Changing Utility') #HALLLLPPPPP
    parser.add_argument('-help', action='store_true', help='Brings up the full help command.')

    args = parser.parse_args()

    if args.help:
        print("This tool was created to easily change your MAC address. Either choose one of the predefined ones or use your own.\n\nYou may enter your own in either the XXXXXXXXXXXX or XX:XX:XX:XX:XX:XX formats. You also have the ability to save it for future use." + RESET)
    else:
        predefined_macs = read_predefined_macs() #git to werk
        check_wireless_interface(predefined_macs)

if __name__ == "__main__":
    main()
