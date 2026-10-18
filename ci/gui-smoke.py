#!/usr/bin/env python3
"""Run one catalogue application in an administrator-supplied software VM.

CI_VM_HELPER, CI_VM_RUNNER and CI_APP_EXECUTABLE are reviewed local paths.
The job receives neither /dev/kvm nor the host Nix daemon socket.
"""
import json
import os
import pathlib
import subprocess
import time
import zipfile


def main():
    helper = os.environ["CI_VM_HELPER"]
    runner = os.environ["CI_VM_RUNNER"]
    executable = os.environ["CI_APP_EXECUTABLE"]
    app_id = os.environ.get("CI_APP_ID", "featherpad")
    host, state = "ci-desktop", "gui"
    evidence = pathlib.Path("gui-evidence")
    evidence.mkdir(exist_ok=True)
    env = os.environ.copy()
    # The administrator retains the prebuilt closure; jobs cannot create host GC roots.
    env["NIXOS_VM_BUILD_CHECK"] = "1"

    def vm(action, *args, timeout=180):
        result = subprocess.run([helper, action, host, "--state", state, *args],
                                env=env, capture_output=True, timeout=timeout)
        if result.returncode:
            with (evidence / "failed-command.log").open("ab") as log:
                log.write(result.stdout + result.stderr)
            result.check_returncode()
        return result.stdout

    def guest(*args):
        return vm("exec", "--", "/run/current-system/sw/bin/env",
                  "PATH=/run/current-system/sw/bin:/run/wrappers/bin", *args)

    def user(program, *args):
        return guest("runuser", "-u", "main", "--", "env", "XDG_RUNTIME_DIR=/run/user/1000",
                     "WAYLAND_DISPLAY=" + display, "/run/current-system/sw/bin/" + program, *args)

    try:
        boot = vm("run", "--runner", runner, "--software", "--memory", "2048", "--cores", "2",
                  "--no-presets", "--detach", timeout=960)
        (evidence / "boot.log").write_bytes(boot)
        deadline = time.monotonic() + 180
        while True:
            try:
                sockets = guest("find", "/run/user/1000", "-maxdepth", "1", "-type", "s", "-name", "wayland-*").decode().splitlines()
            except subprocess.CalledProcessError:
                sockets = []
            if sockets:
                display = pathlib.Path(sockets[0]).name
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("desktop did not expose a Wayland socket")
            time.sleep(2)
        deadline = time.monotonic() + 300
        while True:
            panel = json.loads(guest("silo", "inspect", "panel", "--json"))
            try:
                guest("test", "-S", "/run/user/1000/desktop-theme.sock")
                ready = panel["status"].get("ActiveState") == "active"
            except subprocess.CalledProcessError:
                ready = False
            if ready:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("desktop sandbox registration did not become ready")
            time.sleep(2)
        catalogue = json.loads(pathlib.Path("checkout/catalogue.json").read_text())
        applications = catalogue["apps"]
        app = next(item for item in applications if item["id"] == app_id)
        definition = app["jail"]
        # The package is independently resolved from the catalogue pin by the administrator.
        # Execute that immutable package with the catalogue's real sandbox grants.
        definition["command"] = {"kind": "exec", "argv": [executable, *definition["command"].get("args", []), "/app/ci.txt"]}
        definition.setdefault("files", {})["ci.txt"] = "Silo catalogue GUI acceptance\nSoftware emulation, private sandbox, captured evidence.\n"
        source = evidence / "application.json"
        source.write_text(json.dumps(definition))
        vm("upload", "--", str(source), "/var/tmp/ci-application.json")
        guest("silo", "apply", "/var/tmp/ci-application.json", "--input-json")
        user("silo", "run", "--detach", definition["name"])
        deadline = time.monotonic() + 120
        while True:
            try:
                clients = json.loads(user("hyprctl", "-i", "0", "-j", "clients"))
            except subprocess.CalledProcessError:
                clients = []
            (evidence / "clients.json").write_text(json.dumps(clients, indent=2))
            matching = [c for c in clients if c.get("mapped") and
                        (app_id.lower() in (c.get("class", "") + c.get("title", "")).lower()
                         or c.get("title") == "/app/ci.txt")]
            matching = [c for c in matching if "silo-" + definition["name"] + ".service" in
                        guest("cat", "/proc/" + str(int(c["pid"])) + "/cgroup").decode()]
            if matching:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("application did not map a Wayland window")
            time.sleep(2)
        (evidence / "clients.json").write_text(json.dumps(clients, indent=2))
        time.sleep(3)
        user("grim", "/tmp/catalogue-gui.png")
        vm("download", "--", "/tmp/catalogue-gui.png", str(evidence / "screenshot.png"))
        print("Mapped catalogue application and captured screenshot", flush=True)
    finally:
        for name, command in [("application.log", ("silo", "logs", app_id, "--lines", "100")),
                              ("greetd.log", ("journalctl", "-b", "-u", "greetd", "-n", "120", "--no-pager")),
                              ("sessions.log", ("loginctl", "list-sessions", "--no-legend")),
                              ("desktop-journal.log", ("journalctl", "-b", "_UID=1000", "--no-pager")),
                              ("errors.log", ("journalctl", "-b", "-p", "warning", "--no-pager"))]:
            try:
                (evidence / name).write_bytes(guest(*command))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass
        vm_state = pathlib.Path(env.get("XDG_STATE_HOME", str(pathlib.Path.home() / ".local/state"))) / "nixos-config/microvm" / host / state
        for name in ("supervisor.log", "microvm-run.log", "virtiofsd-run.log"):
            source = vm_state / name
            if source.is_file():
                (evidence / name).write_bytes(source.read_bytes()[-1024 * 1024:])
        try:
            result = subprocess.run([helper, "stop", host, "--state", state], env=env, capture_output=True, timeout=30)
            (evidence / "stop.log").write_bytes(result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            (evidence / "stop.log").write_text("VM stop timed out; jail teardown will terminate remaining processes.\n")
        with zipfile.ZipFile("gui-evidence.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(evidence.iterdir()):
                if path.is_file():
                    archive.write(path, path.name)


if __name__ == "__main__":
    main()
