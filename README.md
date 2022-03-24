# listen_on


This module will listen on a specified port on a specified remote system to allow for firewall and security group testings.

## Chat with James (Dive into Ansible) instructor.

```
RC
Russell
0 upvotes
22 hours ago
Hi James, 

I must be doing something wrong here:

pip freeze shows I have installed ansible and daemonize.



(venv) ansible@ubuntu-c:~/listen_on$ pip freeze | grep daemon
daemonize==2.5.0
(venv) ansible@ubuntu-c:~/listen_on$ pip freeze | grep daemon
daemonize==2.5.0
(venv) ansible@ubuntu-c:~/listen_on$ which ansible-playbook
/home/ansible/listen_on/venv/bin/ansible-playbook
 
Here I run my playbook ....
 
(venv) ansible@ubuntu-c:~/listen_on$ cd TEST_LAB_FILES/
(venv) ansible@ubuntu-c:~/listen_on/TEST_LAB_FILES$ ansible-playbook -i hosts -l centos listen_on_playbook_ubuntu.yml 
 
PLAY [all] 
 
**************************************************************************************************************************
 
TASK [Gathering Facts] **************************************************************************************************************
ok: [centos3]
ok: [centos2]
ok: [centos1]
 
TASK [Terminate listener] ***********************************************************************************************************
...ignoring
 
TASK [Test listen_on module port 50030] *********************************************************************************************
fatal: [centos1 -> ubuntu3]: FAILED! => {"changed": false, "module_stderr": "unix_listener: cannot bind to path /home/ansible/.ansible/cp/b86a8a16f1.hDbLZzMXaJcHYUmw: Invalid argument\r\nControlSocket /home/ansible/.ansible/cp/b86a8a16f1.hDbLZzMXaJcHYUmw already exists, disabling multiplexing\r\nConnection to ubuntu3 closed.\r\n", "module_stdout": "\r\nTraceback (most recent call last):\r\n  File \"/home/ansible/.ansible/tmp/ansible-tmp-1648007518.8253736-14425-133966129228399/AnsiballZ_listen_on.py\", line 107, in <module>\r\n    _ansiballz_main()\r\n  File \"/home/ansible/.ansible/tmp/ansible-tmp-1648007518.8253736-14425-133966129228399/AnsiballZ_listen_on.py\", line 99, in _ansiballz_main\r\n    invoke_module(zipped_mod, temp_path, ANSIBALLZ_PARAMS)\r\n  File \"/home/ansible/.ansible/tmp/ansible-tmp-1648007518.8253736-14425-133966129228399/AnsiballZ_listen_on.py\", line 47, in invoke_module\r\n    runpy.run_module(mod_name='ansible.modules.listen_on', init_globals=dict(_module_fqn='ansible.modules.listen_on', _modlib_path=modlib_path),\r\n  File \"/usr/lib/python3.8/runpy.py\", line 207, in run_module\r\n    return _run_module_code(code, init_globals, run_name, mod_spec)\r\n  File \"/usr/lib/python3.8/runpy.py\", line 97, in _run_module_code\r\n    _run_code(code, mod_globals, init_globals,\r\n  File \"/usr/lib/python3.8/runpy.py\", line 87, in _run_code\r\n    exec(code, run_globals)\r\n  File \"/tmp/ansible_listen_on_payload_i5ofp39x/ansible_listen_on_payload.zip/ansible/modules/listen_on.py\", line 19, in <module>\r\nModuleNotFoundError: No module named 'daemonize'\r\n", "msg": "MODULE FAILURE\nSee stdout/stderr for the exact error", "rc": 1}
 
NO MORE HOSTS LEFT ******************************************************************************************************************
 
PLAY RECAP 
**************************************************************************************************************************
centos1                    : ok=2    changed=1    unreachable=0    failed=1    skipped=0    rescued=0    ignored=1   
centos2                    : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
centos3                    : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
 
(venv) ansible@ubuntu-c:~/listen_on/TEST_LAB_FILES$   
 
 
 
 
 
So do I have to install daemonize on all my remote systems too?


James — Instructor
1 upvote
14 minutes ago
Hi Russell,

This unfortunately is a quirk of running Ansible in a container. When I build the Ansible container image, I make a modification so that it uses a different path for shared memory rather than the default (which would be the overlay filesystem as part of Docker).

You won’t have this problem when you run outside of the lab.

See lines 29 and 30 from the container image source files for the commands you will want to run to patch your Ansible to work in the container -

https://github.com/spurin/diveintoansible-images/blob/ansible/Dockerfile
RC
Russell
0 upvotes
7 minutes ago
Hi James,  I was able to solve the issue with daemonize module.  Fortunately the daemonize module is on github and is not too complicated so I simply put the source code in my ansible module python file.
```


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
