#!/usr/bin/python3

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
failed: [ubuntu1 -> ubuntu3] (item=ubuntu3) => {
    "ansible_loop_var": "item", 
    "changed": false, 
    "item": "ubuntu3", 
    "module_stderr": "Shared connection to ubuntu3 closed.\r\n", 
    "module_stdout": "
{\"changed\": true, \"msg\": \"listening on port 60060.\"}
Unable to lock on the pidfile.
{\"msg\": \"New-style module did not handle its own exit\", \"failed\": true}\r\n", "msg": "MODULE FAILURE\nSee stdout/stderr for the exact error", "rc": 1}
'''

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.basic import AnsibleModule
from daemonize import Daemonize
import concurrent.futures
import logging
import select
import socket
import sys

class ListenOnPort:

    def __init__(self, port, logger):
        self.port = port
        self.pid = "/tmp/listen_on_%s.pid" % port
        self.logger = logger

    def client_connect(self):
        HOST = "127.0.0.1"  # The server's hostname or IP address
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, self.port))
            return True
        except Exception as ex:
            self.logger.info('line 49 error client_connect() ex=%s.' % ex)
        return False

    def listen_on_port(self):
        try:
            running = True
            HOST = ''                # Symbolic name meaning all available interfaces
            PORT = int(self.port)    # Arbitrary non-privileged port
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            server_socket.setblocking(False)  # non-blocking I/O
            self.logger.info('listening on port %s' % self.port)
            read_list = [server_socket]
            while running:
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
                                self.logger.info('line 69 error s.recv() ex=%s.' % ex)
                            finally:
                                self.logger.info("closing socket.")
                                s.close()
                                read_list.remove(s)
                except Exception as ex:
                    self.logger.info('line 75 Inside while True. error ex=%s.' % ex)
                    raise ex
        except Exception as ex:
            self.logger.info('line 78 error ex=%s' % ex)
            raise ex

def listen_on_port(port):
    # format = "%(asctime)s: %(message)s"
    # logging.basicConfig(format=format, level=logging.INFO, filename='listen_on.log', datefmt="%H:%M:%S")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    fh = logging.FileHandler("/tmp/test_%s.log" % port, "w")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    keep_fds = [fh.stream.fileno()]

    # print('{"changed": true, "msg": "listening on port %s."}' % port, flush=True)
    print('{"changed": true, "msg": "listening on port %s."}' % port)
    sys.stdout.flush()
    l = ListenOnPort(port=port, logger=logger)
    if l.client_connect():
        print('{"changed": false, "warning": True, "msg": "Already listening on port %s."}' % port)
        return
    d = Daemonize(app="demon_%s" % port, pid=l.pid, keep_fds=keep_fds, action=l.listen_on_port)
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
        socket.setdefaulttimeout(module.params.get('listen_on_timeout'))
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(listen_on_port,module.params.get('listen_on_port'))

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    #if module.params['listen_on_port']:
    #result['changed'] = True
    #result['msg'] = "listing on port %s" % module.params['listen_on_port']
    #print("exitting")
    #module.exit_json(**result)
    

def main():
    run_module()

if __name__ == '__main__':
    main()
