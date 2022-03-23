#
#(venv) russellcecala@Russells-MacBook-Pro listen_on % ansible-playbook -i,localhost listen_on_playbook.yml --connection=local -e 'ansible_python_interpreter=/Users/russellcecala/ANSIBLE/venv/bin/python3'
#ansible-playbook -i,localhost listen_on_playbook.yml --connection=local -e 'ansible_python_interpreter=/Users/russellcecala/ANSIBLE/venv/bin/python3'
ansible-playbook -i hosts -l centos listen_on_playbook_ubuntu.yml 
