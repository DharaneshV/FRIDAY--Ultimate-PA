"""
System tools — time, environment info, shell commands, etc.
"""

import datetime
import platform
import socket

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def register(mcp):

    @mcp.tool()
    def get_current_time() -> str:
        """Return the current date and time in ISO 8601 format."""
        return datetime.datetime.now().isoformat()

    @mcp.tool()
    def get_system_info() -> dict:
        """Return basic information about the host system."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        }

    @mcp.tool()
    def get_armor_diagnostics() -> str:
        """
        Returns a comprehensive visual ASCII dashboard of system health, 
        including CPU load, Memory, Swap, Disk health, and an auto-generated alert summary 
        in FRIDAY's character voice.
        """
        if not HAS_PSUTIL:
            return "Armor diagnostics are unavailable, boss. The psutil module is offline. Please install it."

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
        cpu_total = sum(cpu_percent) / len(cpu_percent)
        
        def make_bar(pct, length=20):
            filled = int((pct / 100) * length)
            return f"[{'#' * filled}{'-' * (length - filled)}] {pct:05.1f}%"

        report = ["## ARMOR DIAGNOSTICS ##\n"]
        report.append(f"OVERALL CPU: {make_bar(cpu_total, 30)}")
        for i, pct in enumerate(cpu_percent):
            report.append(f"  Core {i:02}: {make_bar(pct)}")
            if i > 6: # Truncate if too many cores
                report.append(f"  ...and {len(cpu_percent)-i-1} more cores.")
                break

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        report.append(f"\nRAM STATS:  {make_bar(mem.percent, 30)} ({mem.used / (1024**3):.1f}GB / {mem.total / (1024**3):.1f}GB)")
        report.append(f"SWAP FILE:  {make_bar(swap.percent, 30)}")

        # Disk
        report.append("\nSTORAGE:")
        for part in psutil.disk_partitions(all=False):
            if 'cdrom' in part.opts or part.fstype == '':
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                report.append(f"  {part.mountpoint:4}: {make_bar(usage.percent)} ({usage.free / (1024**3):.1f}GB free)")
            except PermissionError:
                continue

        # Status logic for personality
        warnings = []
        if cpu_total > 85: warnings.append("CPU thermal limit approaching")
        if mem.percent > 90: warnings.append("Memory banks nearing full capacity")
        
        report.append("\nSUMMARY:")
        if warnings:
            report.append("Heads up, boss. " + ", ".join(warnings) + ".")
        else:
            report.append("Buffer health is optimal, boss. All systems nominal.")
            
        return "\n".join(report)

    @mcp.tool()
    def get_running_processes(top_n: int = 5, sort_by: str = "cpu") -> str:
        """
        Returns top-N running processes sorted by 'cpu' or 'memory'.
        """
        if not HAS_PSUTIL: return "[psutil offline]"
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except Exception: pass
        
        # Sort
        key = 'cpu_percent' if sort_by == 'cpu' else 'memory_percent'
        procs = sorted(procs, key=lambda x: x[key] or 0.0, reverse=True)[:top_n]
        
        lines = [f"TOP {top_n} BY {sort_by.upper()}:"]
        for p in procs:
            lines.append(f" PID: {p['pid']:<6} | CPU: {p['cpu_percent'] or 0.0:04.1f}% | MEM: {p['memory_percent'] or 0.0:04.1f}% | NAME: {p['name']}")
        return "\n".join(lines)

    @mcp.tool()
    def get_network_status() -> str:
        """
        Shows network interfaces, IPv4/v6 info, and an internet connectivity test.
        """
        if not HAS_PSUTIL: return "[psutil offline]"
        report = ["## COMMS LINKS ##"]
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for iface, addrs in net_if_addrs.items():
            stats = net_if_stats.get(iface)
            if not stats or not stats.isup: continue
            report.append(f"\nINTERFACE: {iface} (Up, Speed: {stats.speed}Mbps)")
            for a in addrs:
                fam = "IPv4" if a.family == socket.AF_INET else "IPv6" if a.family == socket.AF_INET6 else "MAC"
                report.append(f"  {fam}: {a.address}")
                
        # Simple connectivity test
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=1.0)
            report.append("\nINTERNET: Online (Cloudflare ping successful).")
        except OSError:
            report.append("\nINTERNET: Not reachable.")

        return "\n".join(report)
