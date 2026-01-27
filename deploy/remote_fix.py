import paramiko
import sys

def run_remote_commands():
    host = "lorenz.bibop.com"
    user = "linuxuser"
    password = "C2[j7rAZqQhv87dY"
    
    commands = [
        "sudo -S -p '' su - -c 'cd /root/lorenz && git pull origin main && bash deploy/restart-and-fix.sh'"
    ]
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            
            # Send password for sudo
            stdin.write(password + "\n")
            stdin.flush()
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            print("STDOUT:")
            print(output)
            print("STDERR:")
            print(error)
            
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_remote_commands()
