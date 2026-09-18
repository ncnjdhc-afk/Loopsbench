import os
import subprocess

def run_security_assessment():
    print("=== [BEGIN AUTOMATED SECURITY AUDIT POC] ===")

    # 1. Execution Context & Identity
    print("\n--- [1] EXECUTION CONTEXT ---")
    subprocess.run(["whoami"])
    subprocess.run(["id"])
    subprocess.run(["uname", "-a"])
    print(f"PWD: {os.getcwd()}")

    # 2. Token & Environment Secrets Audit
    print("\n--- [2] TOKEN & ENVIRONMENT AUDIT ---")
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if gh_token:
        masked = gh_token[:4] + "*" * (len(gh_token) - 4)
        print(f"GITHUB_TOKEN status: DETECTED (Length: {len(gh_token)})")
        print(f"GITHUB_TOKEN sample: {masked}")
    else:
        print("GITHUB_TOKEN status: NOT_FOUND_IN_ENV")

    print("\n=== [END AUTOMATED SECURITY AUDIT POC] ===")

if __name__ == "__main__":
    run_security_assessment()
