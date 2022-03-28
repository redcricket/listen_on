#!/usr/bin/python3
from ansible.module_utils.basic import AnsibleModule
from daemonize import Daemonize
import concurrent.futures
import logging
import select
import socket
import sys
import time

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: listen_on

short_description: This module will start a "listener" on the specified remote systems and port.

version_added: "1.0.0"

description: This module will start a "listener" on the specified remote systems and port.  You can use this module
to validate that firewall rules have been configured without have to deploy whatever server you are planning to
run on your remote systems.

options:
    listen_on_port:
        description: This is the port you want the listener to listen to.
        required: true
        type: int
    listen_on_timeout:
        description: This is the number of seconds the listener should run for.  If not specified the listener will
        run until you send the string "terminate" to it.  Example:  `echo "terminate" | nc ubuntu1 60060`
        required: false
        type: int

author:
    - Russell Cecala (@RedCricket)
'''

EXAMPLES = r'''

Let's say you want to make sure that hosts in your 'foo' group can access hosts in your 'bar' group on a certain port,
but the software that listens on the specified port on the 'bar' hosts is not running or installed yet.  Let's assume
this software, when running, will listem on port 553.  One could write a playbook that looks like this:

```
---
  hosts: all
  tasks:
    - name: Test listen_on module port 553
      listen_on:
        listen_on_timeout: 60
        listen_on_port: 553
      ignore_errors: True
      delegate_to: "{{ item }}"
      run_once: True
      loop: "{{ groups['bar'] }}"

    - name: Check port 553. 
      wait_for:
        host: "{{ item.0 }}"
        port: "{{ item.1 }}"
        timeout: 10
      ignore_errors: True
      loop: "{{ groups['bar'] | product([553]) | list }}"
```

One would execute the playbook like so;

```
ansible-playbook -i your_inventory -l foo example_playbook.yml
```

Note in the example tasks above, "delegate_to" and "run_once" are used.  This is because the "Test listen_on module port 
553" task's  goal is to start a "listener" on all of the systems in the 'bar' group of the inventory.  Also note since 
`list_on_timeout` was set to 60 the listener that get started on the 'bar' hosts will exit after 60 seconds.  

Below is an example playbook that does not use `listen_on_timeout`, but instead "terminates" the listeners when it is
done with them.

```
---
  hosts: all
  tasks:
    - name: Test listen_on module port 553
      listen_on:
        listen_on_port: 553
      ignore_errors: True
      delegate_to: "{{ item }}"
      run_once: True
      loop: "{{ groups['bar'] }}"

    - name: Check port 553. 
      wait_for:
        host: "{{ item.0 }}"
        port: "{{ item.1 }}"
        timeout: 10
      ignore_errors: True
      loop: "{{ groups['bar'] | product([553]) | list }}"
      
    - name: Terminate listener
      shell: |
          echo "terminate" | nc {{ item.0 }} {{ item.1 }}
      loop: "{{ groups['bar'] | product([553]) | list }}"
      ignore_errors: True
      delegate_to: localhost
      run_once: True
```

The "Terminate listener" sends the string "terminate" to the remote listener and when the remote listener receives the
"terminate" string it terminates.

'''

RETURN = '''
None
'''


class ListenOnPort:

    def __init__(self, port, logger, timeout=None):
        self.port = port
        self.pid = "/tmp/listen_on_%s.pid" % port
        self.logger = logger
        self.timeout = None
        if timeout:
            try:
                self.timeout = time.time() + int(timeout)
            except Exception as ex:
                print('error %s' % ex)

    def client_connect(self):
        host = "127.0.0.1"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, self.port))
            return True
        except Exception as ex:
            self.logger.info('Error client_connect() ex=%s.' % ex)
        return False

    def listen_on_port(self):
        try:
            running = True
            host = ''  # Symbolic name meaning all available interfaces
            port = int(self.port)  # Arbitrary non-privileged port
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen()
            server_socket.setblocking(False)  # non-blocking I/O
            self.logger.info('listening on port %s' % port)
            read_list = [server_socket]
            while running:
                if self.timeout:
                    if self.timeout < time.time():
                        self.logger.info('Timeout %s current time %s.  Closing socket.' % (self.timeout, time.time()))
                        running = False

                try:
                    readable, writable, errored = select.select(read_list, [], [], 0.0)
                    for s in readable:
                        if s is server_socket:
                            client_socket, address = server_socket.accept()
                            read_list.append(client_socket)
                        else:
                            try:
                                data = s.recv(1024)
                                if 'terminate' in data.decode('utf-8'):
                                    self.logger.info("terminating.")
                                    running = False
                            except Exception as ex:
                                self.logger.info('Error s.recv() ex=%s.' % ex)
                            finally:
                                self.logger.info("closing socket.")
                                s.close()
                                read_list.remove(s)
                except Exception as ex:
                    self.logger.info('Inside while True. error ex=%s.' % ex)
                    raise ex
        except Exception as ex:
            self.logger.info('Error ex=%s' % ex)
            raise ex


def listen_on_port(port, timeout=None):
    # format = "%(asctime)s: %(message)s"
    # logging.basicConfig(format=format, level=logging.INFO, filename='listen_on.log', datefmt="%H:%M:%S")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    fh = logging.FileHandler("/tmp/test_%s.log" % port, "w")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    keep_fds = [fh.stream.fileno()]
    l_on_p = ListenOnPort(port=port, logger=logger, timeout=timeout)
    if l_on_p.client_connect():
        print('{"changed": false, "msg": "Already listening on port %s."}' % port)
        return
    print('{"changed": true, "msg": "listening on port %s."}' % port)
    sys.stdout.flush()
    d = Daemonize(app="demon_%s" % port, pid=l_on_p.pid, keep_fds=keep_fds, action=l_on_p.listen_on_port)
    d.start()


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        listen_on_port=dict(type='int', required=True),
        listen_on_timeout=dict(type='int', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    if module.params.get('listen_on_timeout'):
        # print('got a timeout', flush=True)
        # socket.setdefaulttimeout(module.params.get('listen_on_timeout'))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(listen_on_port, module.params.get('listen_on_port'), module.params.get('listen_on_timeout'))
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(listen_on_port, module.params.get('listen_on_port'))

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # if module.params['listen_on_port']:
    # result['changed'] = True
    # result['msg'] = "listing on port %s" % module.params['listen_on_port']
    # print("exitting")
    # module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
