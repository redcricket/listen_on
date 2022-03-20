# listen_on

## Testing so far

on the Dive Into Ansible lab we have:


```
ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ ansible-playbook -i hosts -l ubuntu listen_on_playbook.yml 

PLAY [all] **************************************************************************************************************************

TASK [Gathering Facts] **************************************************************************************************************
ok: [ubuntu1]
ok: [ubuntu2]
ok: [ubuntu3]

TASK [Test listen_on module port 50030] *********************************************************************************************
fatal: [ubuntu1 -> centos3]: FAILED! => {"changed": false, "module_stderr": "Shared connection to centos3 closed.\r\n", "module_stdout": "{\"changed\": true, \"msg\": \"listening on port 50030.\"}\r\nUnable to lock on the pidfile.\r\n{\"msg\": \"New-style module did not handle its own exit\", \"failed\": true}\r\n", "msg": "MODULE FAILURE\nSee stdout/stderr for the exact error", "rc": 1}

NO MORE HOSTS LEFT ******************************************************************************************************************

PLAY RECAP **************************************************************************************************************************
ubuntu1                    : ok=1    changed=0    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0   
ubuntu2                    : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
ubuntu3                    : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ 
```

the above failure mean that a process is already listening on port 50030 on remote host centos3.

We can correct that like so:


```
ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ nc -zvw5 centos3 50030
Connection to centos3 50030 port [tcp/*] succeeded!
ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ echo "terminate" | nc centos3 50030
ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ nc -zvw5 centos3 50030
nc: connect to centos3 port 50030 (tcp) failed: Connection refused
ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ 
```

No run the playbook again ...


```
ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ ansible-playbook -i hosts -l ubuntu listen_on_playbook.yml 

PLAY [all] **************************************************************************************************************************

TASK [Gathering Facts] **************************************************************************************************************
ok: [ubuntu1]
ok: [ubuntu2]
ok: [ubuntu3]

TASK [Test listen_on module port 50030] *********************************************************************************************
changed: [ubuntu1 -> centos3]

TASK [Test listen_on module port 40040] *********************************************************************************************
changed: [ubuntu1 -> centos3]

TASK [check port 50030] *************************************************************************************************************
failed: [ubuntu1] (item=centos1) => {"ansible_loop_var": "item", "changed": false, "elapsed": 10, "item": "centos1", "msg": "Timeout when waiting for centos1:50030"}
failed: [ubuntu2] (item=centos1) => {"ansible_loop_var": "item", "changed": false, "elapsed": 10, "item": "centos1", "msg": "Timeout when waiting for centos1:50030"}
failed: [ubuntu3] (item=centos1) => {"ansible_loop_var": "item", "changed": false, "elapsed": 10, "item": "centos1", "msg": "Timeout when waiting for centos1:50030"}
failed: [ubuntu1] (item=centos2) => {"ansible_loop_var": "item", "changed": false, "elapsed": 10, "item": "centos2", "msg": "Timeout when waiting for centos2:50030"}
failed: [ubuntu2] (item=centos2) => {"ansible_loop_var": "item", "changed": false, "elapsed": 10, "item": "centos2", "msg": "Timeout when waiting for centos2:50030"}
failed: [ubuntu3] (item=centos2) => {"ansible_loop_var": "item", "changed": false, "elapsed": 10, "item": "centos2", "msg": "Timeout when waiting for centos2:50030"}
ok: [ubuntu1] => (item=centos3)
...ignoring
ok: [ubuntu2] => (item=centos3)
...ignoring
ok: [ubuntu3] => (item=centos3)
...ignoring

TASK [Terminate listener] ***********************************************************************************************************
failed: [ubuntu1 -> localhost] (item=centos1) => {"ansible_loop_var": "item", "changed": true, "cmd": "echo \"terminate\" | nc centos1 50030\n", "delta": "0:00:00.006427", "end": "2022-03-20 20:15:57.118420", "item": "centos1", "msg": "non-zero return code", "rc": 1, "start": "2022-03-20 20:15:57.111993", "stderr": "", "stderr_lines": [], "stdout": "", "stdout_lines": []}
failed: [ubuntu1 -> localhost] (item=centos2) => {"ansible_loop_var": "item", "changed": true, "cmd": "echo \"terminate\" | nc centos2 50030\n", "delta": "0:00:00.006764", "end": "2022-03-20 20:15:57.363332", "item": "centos2", "msg": "non-zero return code", "rc": 1, "start": "2022-03-20 20:15:57.356568", "stderr": "", "stderr_lines": [], "stdout": "", "stdout_lines": []}
changed: [ubuntu1 -> localhost] => (item=centos3)
...ignoring

TASK [All done] *********************************************************************************************************************
ok: [ubuntu1 -> localhost] => {
    "msg": "All done"
}

PLAY RECAP **************************************************************************************************************************
ubuntu1                    : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=2   
ubuntu2                    : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1   
ubuntu3                    : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1   

ansible@ubuntu-c:~/diveintoansible/Ansible Playbooks, Introduction/Ansible Playbooks, Creating and Executing/solution/00$ 
```
