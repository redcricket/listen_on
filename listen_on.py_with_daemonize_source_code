#!/usr/bin/python3

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
'''

# #!/usr/bin/python

import fcntl
import os
import pwd
import grp
import sys
import signal
import resource
import logging
import atexit
from logging import handlers
import traceback


__version__ = "2.5.0"


class Daemonize(object):
    """
    Daemonize object.

    Object constructor expects three arguments.

    :param app: contains the application name which will be sent to syslog.
    :param pid: path to the pidfile.
    :param action: your custom function which will be executed after daemonization.
    :param keep_fds: optional list of fds which should not be closed.
    :param auto_close_fds: optional parameter to not close opened fds.
    :param privileged_action: action that will be executed before drop privileges if user or
                              group parameter is provided.
                              If you want to transfer anything from privileged_action to action, such as
                              opened privileged file descriptor, you should return it from
                              privileged_action function and catch it inside action function.
    :param user: drop privileges to this user if provided.
    :param group: drop privileges to this group if provided.
    :param verbose: send debug messages to logger if provided.
    :param logger: use this logger object instead of creating new one, if provided.
    :param foreground: stay in foreground; do not fork (for debugging)
    :param chdir: change working directory if provided or /
    """
    def __init__(self, app, pid, action,
                 keep_fds=None, auto_close_fds=True, privileged_action=None,
                 user=None, group=None, verbose=False, logger=None,
                 foreground=False, chdir="/"):
        self.app = app
        self.pid = os.path.abspath(pid)
        self.action = action
        self.keep_fds = keep_fds or []
        self.privileged_action = privileged_action or (lambda: ())
        self.user = user
        self.group = group
        self.logger = logger
        self.verbose = verbose
        self.auto_close_fds = auto_close_fds
        self.foreground = foreground
        self.chdir = chdir

    def sigterm(self, signum, frame):
        """
        These actions will be done after SIGTERM.
        """
        self.logger.warning("Caught signal %s. Stopping daemon." % signum)
        sys.exit(0)

    def exit(self):
        """
        Cleanup pid file at exit.
        """
        self.logger.warning("Stopping daemon.")
        os.remove(self.pid)
        sys.exit(0)

    def start(self):
        """
        Start daemonization process.
        """
        # If pidfile already exists, we should read pid from there; to overwrite it, if locking
        # will fail, because locking attempt somehow purges the file contents.
        if os.path.isfile(self.pid):
            with open(self.pid, "r") as old_pidfile:
                old_pid = old_pidfile.read()
        # Create a lockfile so that only one instance of this daemon is running at any time.
        try:
            lockfile = open(self.pid, "w")
        except IOError:
            print("Unable to create the pidfile.")
            sys.exit(1)
        try:
            # Try to get an exclusive lock on the file. This will fail if another process has the file
            # locked.
            fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print("Unable to lock on the pidfile.")
            # We need to overwrite the pidfile if we got here.
            with open(self.pid, "w") as pidfile:
                pidfile.write(old_pid)
            sys.exit(1)

        # skip fork if foreground is specified
        if not self.foreground:
            # Fork, creating a new process for the child.
            try:
                process_id = os.fork()
            except OSError as e:
                self.logger.error("Unable to fork, errno: {0}".format(e.errno))
                sys.exit(1)
            if process_id != 0:
                if self.keep_fds:
                    # This is the parent process. Exit without cleanup,
                    # see https://github.com/thesharp/daemonize/issues/46
                    os._exit(0)
                else:
                    sys.exit(0)
            # This is the child process. Continue.

            # Stop listening for signals that the parent process receives.
            # This is done by getting a new process id.
            # setpgrp() is an alternative to setsid().
            # setsid puts the process in a new parent group and detaches its controlling terminal.
            process_id = os.setsid()
            if process_id == -1:
                # Uh oh, there was a problem.
                sys.exit(1)

            # Add lockfile to self.keep_fds.
            self.keep_fds.append(lockfile.fileno())

            # Close all file descriptors, except the ones mentioned in self.keep_fds.
            devnull = "/dev/null"
            if hasattr(os, "devnull"):
                # Python has set os.devnull on this system, use it instead as it might be different
                # than /dev/null.
                devnull = os.devnull

            if self.auto_close_fds:
                for fd in range(3, resource.getrlimit(resource.RLIMIT_NOFILE)[0]):
                    if fd not in self.keep_fds:
                        try:
                            os.close(fd)
                        except OSError:
                            pass

            devnull_fd = os.open(devnull, os.O_RDWR)
            os.dup2(devnull_fd, 0)
            os.dup2(devnull_fd, 1)
            os.dup2(devnull_fd, 2)
            os.close(devnull_fd)

        if self.logger is None:
            # Initialize logging.
            self.logger = logging.getLogger(self.app)
            self.logger.setLevel(logging.DEBUG)
            # Display log messages only on defined handlers.
            self.logger.propagate = False

            # Initialize syslog.
            # It will correctly work on OS X, Linux and FreeBSD.
            if sys.platform == "darwin":
                syslog_address = "/var/run/syslog"
            else:
                syslog_address = "/dev/log"

            # We will continue with syslog initialization only if actually have such capabilities
            # on the machine we are running this.
            if os.path.exists(syslog_address):
                syslog = handlers.SysLogHandler(syslog_address)
                if self.verbose:
                    syslog.setLevel(logging.DEBUG)
                else:
                    syslog.setLevel(logging.INFO)
                # Try to mimic to normal syslog messages.
                formatter = logging.Formatter("%(asctime)s %(name)s: %(message)s",
                                              "%b %e %H:%M:%S")
                syslog.setFormatter(formatter)

                self.logger.addHandler(syslog)

        # Set umask to default to safe file permissions when running as a root daemon. 027 is an
        # octal number which we are typing as 0o27 for Python3 compatibility.
        os.umask(0o27)

        # Change to a known directory. If this isn't done, starting a daemon in a subdirectory that
        # needs to be deleted results in "directory busy" errors.
        os.chdir(self.chdir)

        # Execute privileged action
        privileged_action_result = self.privileged_action()
        if not privileged_action_result:
            privileged_action_result = []

        # Change owner of pid file, it's required because pid file will be removed at exit.
        uid, gid = -1, -1

        if self.group:
            try:
                gid = grp.getgrnam(self.group).gr_gid
            except KeyError:
                self.logger.error("Group {0} not found".format(self.group))
                sys.exit(1)

        if self.user:
            try:
                uid = pwd.getpwnam(self.user).pw_uid
            except KeyError:
                self.logger.error("User {0} not found.".format(self.user))
                sys.exit(1)

        if uid != -1 or gid != -1:
            os.chown(self.pid, uid, gid)

        # Change gid
        if self.group:
            try:
                os.setgid(gid)
            except OSError:
                self.logger.error("Unable to change gid.")
                sys.exit(1)

        # Change uid
        if self.user:
            try:
                uid = pwd.getpwnam(self.user).pw_uid
            except KeyError:
                self.logger.error("User {0} not found.".format(self.user))
                sys.exit(1)
            try:
                os.setuid(uid)
            except OSError:
                self.logger.error("Unable to change uid.")
                sys.exit(1)

        try:
            lockfile.write("%s" % (os.getpid()))
            lockfile.flush()
        except IOError:
            self.logger.error("Unable to write pid to the pidfile.")
            print("Unable to write pid to the pidfile.")
            sys.exit(1)

        # Set custom action on SIGTERM.
        signal.signal(signal.SIGTERM, self.sigterm)
        atexit.register(self.exit)

        self.logger.warning("Starting daemon.")

        try:
            self.action(*privileged_action_result)
        except Exception:
            for line in traceback.format_exc().split("\n"):
                self.logger.error(line)



from ansible.module_utils.basic import AnsibleModule
#from daemonize import Daemonize
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
                                self.logger.info('error s.recv() ex=%s.' % ex)
                            finally:
                                self.logger.info("closing socket.")
                                s.close()
                                read_list.remove(s)
                except Exception as ex:
                    self.logger.info('Inside while True. error ex=%s.' % ex)
                    raise ex
        except Exception as ex:
            self.logger.info('error ex=%s' % ex)

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
