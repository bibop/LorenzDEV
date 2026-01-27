#!/usr/bin/env python3
"""
LORENZ Production Fix via SSH
Automatically fixes the database initialization issue
"""
import sys

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def main():
    host = "lorenz.bibop.com"
    user = "linuxuser"
    password = "C2[j7rAZqQhv87dY"
    
    print("=== LORENZ Production Fix ===\n")
    print(f"Connecting to {host}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        print("Connected successfully!\n")
        
        # Command sequence
        commands = [
            # Find project directory
            ("find / -name 'lorenz-backend' -type d 2>/dev/null | grep -v docker | head -1", "Finding project..."),
        ]
        
        project_backend = None
        for cmd, desc in commands:
            print(f"{desc}")
            stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                print(f"  Output: {output}")
                project_backend = output
            if error and "find" not in error:
                print(f"  Error: {error}")
        
        if not project_backend:
            print("\n❌ Could not find lorenz-backend directory!")
            return 1
        
        # Get project root (parent of lorenz-backend)
        import os
        project_root = os.path.dirname(project_backend)
        print(f"\n✅ Project found at: {project_root}\n")
        
        # Now execute the fix script
        fix_commands = [
            f"cd {project_root} && git pull origin main",
            "docker exec lorenz-backend pip install psycopg2-binary",
            "docker restart lorenz-backend",
            "sleep 15",
            "docker exec lorenz-backend alembic upgrade head",
            "docker exec lorenz-backend python3 scripts/create_admin_user.py",
            'curl -s -X POST http://localhost:8050/api/v1/auth/login -H "Content-Type: application/json" -d \'{"email":"admin@lorenz.ai","password":"adminpassword123"}\' -w "\\nHTTP:%{http_code}"'
        ]
        
        for i, cmd in enumerate(fix_commands, 1):
            print(f"\n[{i}/{len(fix_commands)}] Executing: {cmd[:60]}...")
            
            # Use sudo for all commands
            full_cmd = f"echo '{password}' | sudo -S bash -c '{cmd}'"
            stdin, stdout, stderr = ssh.exec_command(full_cmd, get_pty=True)
            
            # Read output
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                print(output)
            if error and "sudo" not in error.lower():
                print(f"  Stderr: {error}")
        
        print("\n=== Fix complete! ===")
        print("\nCredentials:")
        print("  URL: https://lorenz.bibop.com")
        print("  Email: admin@lorenz.ai")
        print("  Password: adminpassword123")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        ssh.close()

if __name__ == "__main__":
    sys.exit(main())
