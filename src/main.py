"""Application entry point.

The `if __name__ == '__main__':` guard is required on Windows because
multiprocessing uses the 'spawn' method, which re-imports __main__ in
each child process. Without this guard, child processes would re-launch
the menu recursively.
"""

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()  # needed for frozen executables (PyInstaller etc.)
    from debate.cli.menu import run_menu
    run_menu()
