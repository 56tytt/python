#!/usr/bin/env python3
"""
ShayElevate - כלי להרחבת הרשאות וחיפוש סיסמאות
כתב: Shay Kadosh
"""

import os
import sys
import subprocess
import platform
import argparse
from colorama import Fore, Style, init

init(autoreset=True)

class ShayElevate:
    def __init__(self):
        self.os_type = platform.system()
        self.results = []

    def print_banner(self):
        banner = f"""
{Fore.RED}
    ╔══════════════════════════════════════════════════╗
    ║     🔥 SHAYELEVATE - PRIVILEGE ESCALATION      ║
    ║         Shay Kadosh - Cyber Security Expert     ║
    ╚══════════════════════════════════════════════════╝
{Style.RESET_ALL}
        """
        print(banner)

    def check_current_user(self):
        """בדיקת משתמש נוכחי והרשאות"""
        print(f"{Fore.CYAN}[*] בודק משתמש נוכחי...{Style.RESET_ALL}")
        if self.os_type == "Windows":
            result = subprocess.run(["whoami", "/all"], capture_output=True, text=True)
            print(result.stdout)
        else:  # Linux
            result = subprocess.run(["id"], capture_output=True, text=True)
            print(result.stdout)
            # בדיקת sudo הרשאות
            sudo_check = subprocess.run(["sudo", "-l"], capture_output=True, text=True)
            if "may run the following commands" in sudo_check.stdout:
                print(f"{Fore.GREEN}[+] יש לך הרשאות sudo!{Style.RESET_ALL}")

    def find_passwords(self):
        """חיפוש סיסמאות בקבצים נפוצים"""
        print(f"{Fore.CYAN}[*] מחפש סיסמאות בקבצים...{Style.RESET_ALL}")

        if self.os_type == "Windows":
            paths_to_check = [
                "C:\\Windows\\Panther\\unattend.xml",
                "C:\\Windows\\Panther\\sysprep.inf",
                "C:\\Users\\*\\AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt"
            ]
        else:  # Linux
            paths_to_check = [
                "/etc/passwd",
                "/etc/shadow",
                "/root/.bash_history",
                "/home/*/.bash_history",
                "/var/www/html/config.php"
            ]

        for path in paths_to_check:
            if os.path.exists(path) or "*" in path:
                print(f"{Fore.YELLOW}[!] מוצא: {path}{Style.RESET_ALL}")
                # נמשיך עם חיפוש מפורט בהמשך

    def check_vulnerabilities(self):
        """בדיקת פרצות נפוצות להרחבת הרשאות"""
        print(f"{Fore.CYAN}[*] בודק פרצות נפוצות...{Style.RESET_ALL}")

        if self.os_type == "Windows":
            # בדיקת AlwaysInstallElevated
            reg_check = subprocess.run(
                ['reg', 'query', 'HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer', '/v', 'AlwaysInstallElevated'],
                capture_output=True, text=True
            )
            if "0x1" in reg_check.stdout:
                print(f"{Fore.GREEN}[+] AlwaysInstallElevated מופעל! ניתן להתקין MSI עם SYSTEM{Style.RESET_ALL}")

        else:  # Linux
            # בדיקת קבצי SUID
            suid_files = subprocess.run(
                ['find', '/', '-perm', '-4000', '-type', 'f', '2>/dev/null'],
                capture_output=True, text=True, shell=True
            )
            if suid_files.stdout:
                print(f"{Fore.YELLOW}[!] קבצי SUID חשודים:{Style.RESET_ALL}")
                print(suid_files.stdout[:500])  # חותכים למניעת ספאם

    def run_full_scan(self):
        """הרצת כל הבדיקות"""
        self.print_banner()
        self.check_current_user()
        self.find_passwords()
        self.check_vulnerabilities()
        print(f"{Fore.GREEN}\n[+] סריקה הושלמה!{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="ShayElevate - כלי להרחבת הרשאות")
    parser.add_argument("--full", action="store_true", help="סריקה מלאה")
    parser.add_argument("--user", action="store_true", help="בדיקת משתמש בלבד")
    parser.add_argument("--passwords", action="store_true", help="חיפוש סיסמאות")
    args = parser.parse_args()

    tool = ShayElevate()

    if args.full:
        tool.run_full_scan()
    elif args.user:
        tool.check_current_user()
    elif args.passwords:
        tool.find_passwords()
    else:
        tool.print_banner()
        print("השתמש ב--help לרשימת אפשרויות")

if __name__ == "__main__":
    main()
