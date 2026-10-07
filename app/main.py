import os
import sys
import argparse
import subprocess

# Ensure workspace root is in path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

def print_header():
    print("\n" + "="*60)
    print(" Google Photos AI Retrieval Discovery Engine ".center(60, "="))
    print("="*60 + "\n")

def run_pm_console():
    """Runs the PM Q&A Console."""
    console_path = os.path.join(workspace_root, "app", "pm_console.py")
    if not os.path.exists(console_path):
        print(f"Error: pm_console.py not found at {console_path}")
        return
    print(f"Starting PM Q&A Console...\n")
    subprocess.run([sys.executable, console_path])

def run_unified_frontend():
    """Runs the Unified Streamlit App (Dashboard + Chatbot)."""
    app_path = os.path.join(workspace_root, "app", "unified_frontend.py")
    if not os.path.exists(app_path):
        print(f"Error: unified_frontend.py not found at {app_path}")
        return
    print(f"Starting Unified Streamlit Frontend (Dashboard + Chatbot)...")
    print(f"Press Ctrl+C to stop when done.\n")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

def run_report_generator():
    """Runs the Automated Failure Taxonomy Report Generator."""
    report_gen_path = os.path.join(workspace_root, "app", "taxonomy_report_generator.py")
    if not os.path.exists(report_gen_path):
        print(f"Error: taxonomy_report_generator.py not found at {report_gen_path}")
        return
    print(f"Generating Failure Taxonomy Report...\n")
    subprocess.run([sys.executable, report_gen_path])

def main():
    parser = argparse.ArgumentParser(description="Google Photos AI Retrieval Discovery Engine")
    parser.add_argument(
        "action",
        choices=["console", "frontend", "report", "interactive"],
        nargs="?",
        default="interactive",
        help="Action to perform (default: interactive menu)"
    )
    
    args = parser.parse_args()
    
    if args.action == "console":
        run_pm_console()
    elif args.action == "frontend":
        run_unified_frontend()
    elif args.action == "report":
        run_report_generator()
    else:
        # Interactive Menu
        while True:
            print_header()
            print("Please select an application to launch:\n")
            print("  1. PM Q&A Console (CLI)")
            print("  2. Unified Web Frontend (Streamlit Dashboard & Chatbot)")
            print("  3. Generate Failure Taxonomy Report (Markdown)")
            print("  4. Exit\n")
            
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                run_pm_console()
            elif choice == "2":
                run_unified_frontend()
            elif choice == "3":
                run_report_generator()
            elif choice == "4" or choice.lower() in ['q', 'quit', 'exit']:
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()
