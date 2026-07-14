import os
import subprocess

def Do_Something_bad( user_input ):
    # Style Issue: Bad naming convention (camelCase in Python), bad spacing
    # Security Issue: Hardcoded secret and command injection
    secret_key = "12345-SUPER-SECRET"
    
    cmd = "echo " + user_input + " " + secret_key
    os.system(cmd)  # Security: shell injection risk
    
    # Performance Issue: O(N^3) nested loops doing nothing useful
    results = []
    for i in range(100):
        for j in range(100):
            for k in range(100):
                results.append(i + j + k)
                
    return results