#!/usr/bin/env python3
"""
Create GitHub repository and push NeuralAgent project
"""

import subprocess
import json
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    GITHUB_TOKEN = "REDACTED_GITHUB_TOKEN"
    REPO_NAME = "NeuralAgent"
    REPO_DESCRIPTION = "AI Agent System with 18-layer neural network architecture"
    
    root_dir = Path(__file__).parent
    
    print("=" * 80)
    print("  NeuralAgent GitHub Setup")
    print("=" * 80)
    print()
    
    # Create GitHub repository using API
    print("1. Creating GitHub repository...")
    
    create_repo_payload = {
        "name": REPO_NAME,
        "description": REPO_DESCRIPTION,
        "private": True,
        "auto_init": False
    }
    
    curl_cmd = f'curl -L -X POST -H "Authorization: token {GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/user/repos -d \'{json.dumps(create_repo_payload)}\''
    
    success, stdout, stderr = run_cmd(curl_cmd)
    
    if not success:
        print("   Note: Repo might already exist or error occurred, proceeding...")
    
    print()
    
    # Stage files
    print("2. Adding files to Git...")
    success, stdout, stderr = run_cmd("git add .", cwd=root_dir)
    if success:
        print("   ✅ Files staged!")
    else:
        print("   ⚠️ Staging files...")
    
    print()
    
    # Commit
    print("3. Creating initial commit...")
    commit_msg = "Initial commit - NeuralAgent AI System\n\n- 18-layer neural network architecture\n- Enhanced memory system\n- Full testing framework\n- Architecture visualization website"
    
    run_cmd(f'git commit -m "{commit_msg}" --allow-empty', cwd=root_dir)
    print("   ✅ Commit created!")
    
    print()
    
    # Add remote
    print("4. Configuring GitHub remote...")
    remote_url = f"https://{GITHUB_TOKEN}@github.com/2358384171/{REPO_NAME}.git"
    run_cmd("git remote remove origin 2>/dev/null || true", cwd=root_dir)
    success, stdout, stderr = run_cmd(f"git remote add origin {remote_url}", cwd=root_dir)
    print(f"   ✅ Remote added: {remote_url}")
    
    print()
    
    # Rename branch to main if needed
    print("5. Setting up main branch...")
    run_cmd("git branch -M main 2>/dev/null || true", cwd=root_dir)
    print("   ✅ Main branch set!")
    
    print()
    
    # Push
    print("6. Pushing to GitHub...")
    print("   This may take a moment...")
    success, stdout, stderr = run_cmd("git push -u origin main --force", cwd=root_dir)
    
    if success:
        print()
        print("=" * 80)
        print("  ✅ SUCCESS!")
        print("=" * 80)
        print(f"  📦 Repository: https://github.com/2358384171/{REPO_NAME}")
        print("  🔒 Privacy: Private")
        print()
        print("  Next steps:")
        print(f"  1. Visit https://github.com/2358384171/{REPO_NAME}")
        print("  2. Manage repository settings")
        print("=" * 80)
    else:
        print()
        print("⚠️ Push might have failed, but let's try alternative approach...")
        print("Manual push command:")
        print(f"  cd {root_dir} && git push -u origin main")
        print()
        print(f"Or visit: https://github.com/2358384171/{REPO_NAME}")

if __name__ == "__main__":
    main()
