import os
import signal
import subprocess
import sys
import time
import webbrowser


def main() -> None:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(root_dir, "backend")

    servers = [
        ("Flight MCP Server (8001)", [python_exe, os.path.join(root_dir, "mcp_servers", "flight_server.py")]),
        ("Weather MCP Server (8002)", [python_exe, os.path.join(root_dir, "mcp_servers", "weather_server.py")]),
        ("Places MCP Server (8003)", [python_exe, os.path.join(root_dir, "mcp_servers", "places_server.py")]),
        ("FastAPI Backend & Web SPA (8000)", [python_exe, "-m", "app.main"]),
    ]

    processes: list[subprocess.Popen[bytes]] = []

    print("=" * 65)
    print("PlanMyTrip AI — Starting Full Stack System")
    print("=" * 65)

    for name, cmd in servers:
        print(f"[*] Launching {name}...")
        proc = subprocess.Popen(cmd, env=env)
        processes.append(proc)
        time.sleep(1.0)

    print("=" * 65)
    print("All services running:")
    print(" - Web Interface: http://localhost:8000")
    print(" - API Docs:      http://localhost:8000/docs")
    print(" - Flight MCP:    http://localhost:8001")
    print(" - Weather MCP:   http://localhost:8002")
    print(" - Places MCP:    http://localhost:8003")
    print("=" * 65)
    print("Demo Account:")
    print(" Email:    demo@planmytrip.ai")
    print(" Password: password123")
    print("=" * 65)
    print("Press Ctrl+C to stop all servers.")

    time.sleep(1.5)
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

    def handle_shutdown(sig: int, frame: object) -> None:
        print("\nStopping all services...")
        for p in processes:
            p.terminate()
        for p in processes:
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"[!] A service exited unexpectedly (code {p.returncode})")
                    handle_shutdown(0, None)
    except KeyboardInterrupt:
        handle_shutdown(0, None)


if __name__ == "__main__":
    main()
