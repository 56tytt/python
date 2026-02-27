#!/usr/bin/env python3
"""
ShaySysInfo - ממשק גרפי למידע מערכת
כתב: Shay Kadosh - Cyber Security Expert
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import platform
import psutil
import cpuinfo
import datetime
import os
import socket
import subprocess
import threading
import GPUtil  # אופציונלי - בשביל מידע על כרטיס מסך

class ShaySysInfo:
    def __init__(self, root):
        self.root = root
        self.root.title("ShaySysInfo - System Intelligence")
        self.root.geometry("1100x700")
        self.root.configure(bg='#0a0e1a')

        # הגדרות צבעים - סטייל האקר
        self.colors = {
            'bg': '#0a0e1a',
            'fg': '#00ff9d',
            'secondary': '#1a1f2f',
            'text': '#ffffff',
            'error': '#ff5555',
            'success': '#00ff9d',
            'warning': '#ffb86b',
            'info': '#00bcd4',
            'dark': '#000000'
        }

        self.setup_ui()
        self.load_system_info()

    def setup_ui(self):
        """בניית הממשק"""

        # ===== HEADER עם ASCII ART =====
        header_frame = tk.Frame(self.root, bg=self.colors['secondary'], height=120)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ascii_art = """
╔══════════════════════════════════════════════════════════════╗
║   ███████╗██╗  ██╗ █████╗ ██╗   ██╗███████╗██╗███╗   ██╗ ██████╗
║   ██╔════╝██║  ██║██╔══██╗╚██╗ ██╔╝██╔════╝██║████╗  ██║██╔═══██╗
║   ███████╗███████║███████║ ╚████╔╝ ███████╗██║██╔██╗ ██║██║   ██║
║   ╚════██║██╔══██║██╔══██║  ╚██╔╝  ╚════██║██║██║╚██╗██║██║   ██║
║   ███████║██║  ██║██║  ██║   ██║   ███████║██║██║ ╚████║╚██████╔╝
║   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝
╚══════════════════════════════════════════════════════════════════╝
        """

        ascii_label = tk.Label(
            header_frame,
            text=ascii_art,
            font=('Courier', 8),
            fg=self.colors['fg'],
            bg=self.colors['secondary'],
            justify=tk.LEFT
        )
        ascii_label.pack(pady=5)

        # ===== TABBED INTERFACE =====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # סטייל לטאבים
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.colors['secondary'],
                       foreground=self.colors['fg'],
                       padding=[15, 5],
                       font=('Courier', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['fg'])],
                 foreground=[('selected', self.colors['bg'])])

        # יצירת הטאבים
        self.create_info_tab()
        self.create_cpu_tab()
        self.create_memory_tab()
        self.create_disk_tab()
        self.create_network_tab()
        self.create_processes_tab()

        # ===== FOOTER עם סטטוס =====
        footer_frame = tk.Frame(self.root, bg=self.colors['secondary'], height=40)
        footer_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = tk.Label(
            footer_frame,
            text="System monitoring active | Shay Kadosh - Cyber Security Expert | ID: 34926089",
            font=('Courier', 9),
            fg='#666666',
            bg=self.colors['secondary']
        )
        self.status_label.pack(pady=10)

        # כפתור רענון
        refresh_btn = tk.Button(
            footer_frame,
            text="🔄 REFRESH",
            command=self.refresh_all,
            bg=self.colors['fg'],
            fg=self.colors['bg'],
            font=('Courier', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2'
        )
        refresh_btn.place(relx=0.95, rely=0.5, anchor=tk.CENTER)

    def create_info_tab(self):
        """טאב מידע כללי"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📊 SYSTEM INFO")

        # מידע כללי
        info_frame = tk.LabelFrame(tab, text="General Information",
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Courier', 11, 'bold'))
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.info_text = tk.Text(info_frame,
                                 bg=self.colors['dark'],
                                 fg=self.colors['fg'],
                                 font=('Courier', 10),
                                 height=15,
                                 wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # הוספת scrollbar
        scrollbar = tk.Scrollbar(self.info_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.info_text.yview)

    def create_cpu_tab(self):
        """טאב מידע על המעבד"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="💻 CPU")

        # מידע מעבד
        cpu_frame = tk.LabelFrame(tab, text="CPU Information",
                                  bg=self.colors['bg'], fg=self.colors['fg'],
                                  font=('Courier', 11, 'bold'))
        cpu_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.cpu_text = tk.Text(cpu_frame,
                                bg=self.colors['dark'],
                                fg=self.colors['fg'],
                                font=('Courier', 10),
                                height=20,
                                wrap=tk.WORD)
        self.cpu_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # הוספת scrollbar
        scrollbar = tk.Scrollbar(self.cpu_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cpu_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.cpu_text.yview)

    def create_memory_tab(self):
        """טאב מידע על הזיכרון"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📝 MEMORY")

        # מידע זיכרון
        mem_frame = tk.LabelFrame(tab, text="Memory Information",
                                  bg=self.colors['bg'], fg=self.colors['fg'],
                                  font=('Courier', 11, 'bold'))
        mem_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.mem_text = tk.Text(mem_frame,
                                bg=self.colors['dark'],
                                fg=self.colors['fg'],
                                font=('Courier', 10),
                                height=20,
                                wrap=tk.WORD)
        self.mem_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # הוספת scrollbar
        scrollbar = tk.Scrollbar(self.mem_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.mem_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.mem_text.yview)

    def create_disk_tab(self):
        """טאב מידע על הדיסק"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="💾 DISK")

        # מידע דיסק
        disk_frame = tk.LabelFrame(tab, text="Disk Information",
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Courier', 11, 'bold'))
        disk_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.disk_text = tk.Text(disk_frame,
                                 bg=self.colors['dark'],
                                 fg=self.colors['fg'],
                                 font=('Courier', 10),
                                 height=20,
                                 wrap=tk.WORD)
        self.disk_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # הוספת scrollbar
        scrollbar = tk.Scrollbar(self.disk_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.disk_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.disk_text.yview)

    def create_network_tab(self):
        """טאב מידע על הרשת"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🌐 NETWORK")

        # מידע רשת
        net_frame = tk.LabelFrame(tab, text="Network Information",
                                  bg=self.colors['bg'], fg=self.colors['fg'],
                                  font=('Courier', 11, 'bold'))
        net_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.net_text = tk.Text(net_frame,
                                bg=self.colors['dark'],
                                fg=self.colors['fg'],
                                font=('Courier', 10),
                                height=20,
                                wrap=tk.WORD)
        self.net_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # הוספת scrollbar
        scrollbar = tk.Scrollbar(self.net_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.net_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.net_text.yview)

    def create_processes_tab(self):
        """טאב תהליכים רצים"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="⚙️ PROCESSES")

        # מידע תהליכים
        proc_frame = tk.LabelFrame(tab, text="Running Processes (Top 20)",
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Courier', 11, 'bold'))
        proc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.proc_text = tk.Text(proc_frame,
                                 bg=self.colors['dark'],
                                 fg=self.colors['fg'],
                                 font=('Courier', 10),
                                 height=20,
                                 wrap=tk.WORD)
        self.proc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # הוספת scrollbar
        scrollbar = tk.Scrollbar(self.proc_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.proc_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.proc_text.yview)

    def load_system_info(self):
        """טעינת כל המידע"""
        # טוען כל טאב בנפרד
        self.load_general_info()
        self.load_cpu_info()
        self.load_memory_info()
        self.load_disk_info()
        self.load_network_info()
        self.load_processes_info()

    def load_general_info(self):
        """מידע כללי על המערכת"""
        self.info_text.delete(1.0, tk.END)

        info = []
        info.append("="*60)
        info.append(f"SYSTEM INFORMATION - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        info.append("="*60)
        info.append("")

        # מידע בסיסי
        info.append(f"🖥️  Hostname: {socket.gethostname()}")
        info.append(f"💻 System: {platform.system()} {platform.release()}")
        info.append(f"📀 Version: {platform.version()}")
        info.append(f"🏗️  Architecture: {platform.machine()}")
        info.append(f"🐍 Python: {platform.python_version()}")
        info.append("")

        # מידע על משתמש
        info.append(f"👤 User: {os.getenv('USER', 'Unknown')}")
        info.append(f"📁 Home: {os.getenv('HOME', 'Unknown')}")
        info.append(f"🕒 Boot Time: {datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}")

        # מידע על זמן פעילות
        uptime_seconds = datetime.datetime.now().timestamp() - psutil.boot_time()
        uptime = str(datetime.timedelta(seconds=uptime_seconds)).split('.')[0]
        info.append(f"⏱️  Uptime: {uptime}")

        self.info_text.insert(1.0, '\n'.join(info))

    def load_cpu_info(self):
        """מידע על המעבד"""
        self.cpu_text.delete(1.0, tk.END)

        info = []
        info.append("="*60)
        info.append(f"CPU INFORMATION")
        info.append("="*60)
        info.append("")

        try:
            # מידע כללי
            cpu_info = cpuinfo.get_cpu_info()
            info.append(f"🔧 CPU: {cpu_info.get('brand_raw', 'Unknown')}")
            info.append(f"⚡ Cores: {psutil.cpu_count(logical=False)} Physical / {psutil.cpu_count(logical=True)} Logical")
            info.append(f"📊 Max Frequency: {psutil.cpu_freq().max:.2f} MHz")
            info.append("")

            # שימוש במעבד
            info.append("📈 CPU Usage Per Core:")
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
                bar = self.create_progress_bar(percentage)
                info.append(f"  Core {i}: {percentage:5.1f}% {bar}")

            info.append("")
            info.append(f"📊 Total CPU Usage: {psutil.cpu_percent():.1f}%")

            # מידע נוסף
            info.append("")
            info.append("🔄 Context Switches:")
            ctx = psutil.cpu_stats()
            info.append(f"  ctx_switches: {ctx.ctx_switches}")
            info.append(f"  interrupts: {ctx.interrupts}")
            info.append(f"  soft_interrupts: {ctx.soft_interrupts}")
            info.append(f"  syscalls: {ctx.syscalls}")

        except Exception as e:
            info.append(f"Error getting CPU info: {e}")

        self.cpu_text.insert(1.0, '\n'.join(info))

    def load_memory_info(self):
        """מידע על הזיכרון"""
        self.mem_text.delete(1.0, tk.END)

        info = []
        info.append("="*60)
        info.append(f"MEMORY INFORMATION")
        info.append("="*60)
        info.append("")

        try:
            # זיכרון RAM
            mem = psutil.virtual_memory()
            info.append("📝 RAM Memory:")
            info.append(f"  Total:     {self.bytes_to_gb(mem.total)}")
            info.append(f"  Available: {self.bytes_to_gb(mem.available)}")
            info.append(f"  Used:      {self.bytes_to_gb(mem.used)}")
            info.append(f"  Free:      {self.bytes_to_gb(mem.free)}")
            info.append(f"  Usage:     {mem.percent:.1f}% {self.create_progress_bar(mem.percent)}")
            info.append("")

            # SWAP
            swap = psutil.swap_memory()
            info.append("💾 SWAP Memory:")
            info.append(f"  Total: {self.bytes_to_gb(swap.total)}")
            info.append(f"  Used:  {self.bytes_to_gb(swap.used)}")
            info.append(f"  Free:  {self.bytes_to_gb(swap.free)}")
            info.append(f"  Usage: {swap.percent:.1f}%")

        except Exception as e:
            info.append(f"Error getting memory info: {e}")

        self.mem_text.insert(1.0, '\n'.join(info))

    def load_disk_info(self):
        """מידע על הדיסקים"""
        self.disk_text.delete(1.0, tk.END)

        info = []
        info.append("="*60)
        info.append(f"DISK INFORMATION")
        info.append("="*60)
        info.append("")

        try:
            # מחיצות
            partitions = psutil.disk_partitions()
            for partition in partitions:
                info.append(f"📁 Partition: {partition.device}")
                info.append(f"  Mountpoint: {partition.mountpoint}")
                info.append(f"  Filesystem: {partition.fstype}")

                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info.append(f"  Total: {self.bytes_to_gb(usage.total)}")
                    info.append(f"  Used:  {self.bytes_to_gb(usage.used)}")
                    info.append(f"  Free:  {self.bytes_to_gb(usage.free)}")
                    info.append(f"  Usage: {usage.percent:.1f}% {self.create_progress_bar(usage.percent)}")
                except PermissionError:
                    info.append("  Access denied")

                info.append("")

            # I/O סטטיסטיקות
            disk_io = psutil.disk_io_counters()
            if disk_io:
                info.append("📊 Disk I/O Statistics:")
                info.append(f"  Read Count:  {disk_io.read_count}")
                info.append(f"  Write Count: {disk_io.write_count}")
                info.append(f"  Read Bytes:  {self.bytes_to_gb(disk_io.read_bytes)}")
                info.append(f"  Write Bytes: {self.bytes_to_gb(disk_io.write_bytes)}")
                info.append(f"  Read Time:   {disk_io.read_time}ms")
                info.append(f"  Write Time:  {disk_io.write_time}ms")

        except Exception as e:
            info.append(f"Error getting disk info: {e}")

        self.disk_text.insert(1.0, '\n'.join(info))

    def load_network_info(self):
        """מידע על הרשת"""
        self.net_text.delete(1.0, tk.END)

        info = []
        info.append("="*60)
        info.append(f"NETWORK INFORMATION")
        info.append("="*60)
        info.append("")

        try:
            # ממשקי רשת
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for interface, addrs in interfaces.items():
                info.append(f"🌐 Interface: {interface}")

                if interface in stats:
                    info.append(f"  Status: {'UP' if stats[interface].isup else 'DOWN'}")
                    info.append(f"  Speed: {stats[interface].speed} Mbps")
                    info.append(f"  MTU: {stats[interface].mtu}")

                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        info.append(f"  IPv4: {addr.address}")
                        info.append(f"  Netmask: {addr.netmask}")
                        info.append(f"  Broadcast: {addr.broadcast}")
                    elif addr.family == socket.AF_INET6:
                        info.append(f"  IPv6: {addr.address}")
                    elif addr.family == psutil.AF_LINK:
                        info.append(f"  MAC: {addr.address}")

                info.append("")

            # חיבורי רשת
            info.append("🔌 Network Connections (first 10):")
            connections = psutil.net_connections()
            for conn in connections[:10]:
                status = conn.status
                if conn.raddr:
                    info.append(f"  {conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip}:{conn.raddr.port} [{status}]")
                else:
                    info.append(f"  {conn.laddr.ip}:{conn.laddr.port} [LISTENING]")

            info.append("")

            # סטטיסטיקות I/O
            net_io = psutil.net_io_counters()
            if net_io:
                info.append("📊 Network I/O Statistics:")
                info.append(f"  Bytes Sent:    {self.bytes_to_gb(net_io.bytes_sent)}")
                info.append(f"  Bytes Received: {self.bytes_to_gb(net_io.bytes_recv)}")
                info.append(f"  Packets Sent:   {net_io.packets_sent}")
                info.append(f"  Packets Received: {net_io.packets_recv}")
                info.append(f"  Errors In:      {net_io.errin}")
                info.append(f"  Errors Out:     {net_io.errout}")
                info.append(f"  Drops In:       {net_io.dropin}")
                info.append(f"  Drops Out:      {net_io.dropout}")

        except Exception as e:
            info.append(f"Error getting network info: {e}")

        self.net_text.insert(1.0, '\n'.join(info))

    def load_processes_info(self):
        """מידע על תהליכים רצים"""
        self.proc_text.delete(1.0, tk.END)

        info = []
        info.append("="*60)
        info.append(f"TOP 20 PROCESSES BY CPU USAGE")
        info.append("="*60)
        info.append("")

        try:
            # אוסף תהליכים
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # ממיין לפי CPU
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)

            info.append(f"{'PID':>7} {'CPU%':>5} {'MEM%':>6} {'STATUS':<10} NAME")
            info.append("-"*60)

            for proc in processes[:20]:
                pid = proc['pid']
                cpu = proc['cpu_percent'] or 0
                mem = proc['memory_percent'] or 0
                status = proc['status'] or '?'
                name = proc['name'][:30]

                info.append(f"{pid:7d} {cpu:5.1f} {mem:6.2f} {status:<10} {name}")

        except Exception as e:
            info.append(f"Error getting process info: {e}")

        self.proc_text.insert(1.0, '\n'.join(info))

    def bytes_to_gb(self, bytes_value):
        """המרת בייטים ל-GB"""
        return f"{bytes_value / (1024**3):.2f} GB"

    def create_progress_bar(self, percentage, width=20):
        """יצירת פס התקדמות"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"

    def refresh_all(self):
        """רענון כל המידע"""
        self.status_label.config(text="Refreshing system information... 🔄")
        self.root.update()

        # טוען מחדש
        self.load_system_info()

        self.status_label.config(text="System information updated | Ready 🔥")
        messagebox.showinfo("Success", "System information refreshed successfully!")

# התקנת חבילות נדרשות לפני הרצה
def check_dependencies():
    """בדיקת והתקנת תלויות"""
    try:
        import psutil
        import cpuinfo
    except ImportError as e:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "py-cpuinfo", "gputil"])
        print("Dependencies installed!")

if __name__ == "__main__":
    # בדיקת תלויות
    check_dependencies()

    # הרצת האפליקציה
    root = tk.Tk()
    app = ShaySysInfo(root)
    root.mainloop()
