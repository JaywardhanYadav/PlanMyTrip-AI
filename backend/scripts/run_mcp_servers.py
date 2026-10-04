import os
import signal
import subprocess
import sys
import time


def main() -> None:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    python_exe = sys.executable

    servers = [
        ("Flight MCP Server (Port 8001)", os.path.join(root_dir, "mcp_servers", "flight_server.py")),
        ("Weather MCP Server (Port 8002)", os.path.join(root_dir, "mcp_servers", "weather_server.py")),
        ("Places MCP Server (Port 8003)", os.path.join(root_dir, "mcp_servers", "places_server.py")),
    ]

    processes: list[subprocess.Popen[bytes]] = []

    print("=" * 60)
    print("Starting all 3 PlanMyTrip MCP Servers...")
    print("=" * 60)

    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(root_dir, "backend")

    for name, script_path in servers:
        print(f"[*] Launching {name}...")
        proc = subprocess.Popen([python_exe, script_path], env=env)
        processes.append(proc)
        time.sleep(0.5)

    print("=" * 60)
    print("All 3 MCP servers running. Press Ctrl+C to stop all servers.")
    print("=" * 60)

    def handle_sigint(sig: int, frame: object) -> None:
        print("\nShutting down all MCP servers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("All servers stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"[!] Server exited with code {p.returncode}")
                    handle_sigint(0, None)
    except KeyboardInterrupt:
        handle_sigint(0, None)


if __name__ == "__main__":
    main()
