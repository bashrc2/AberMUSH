__filename__ = "threads.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Web Interface"

import threading
import sys
import time
import datetime


class threadWithTrace(threading.Thread):
    def __init__(self, *args, **keywords):
        self.start_time = datetime.datetime.now()
        self.is_started = False
        tries = 0
        while tries < 3:
            try:
                self._args, self._keywords = args, keywords
                threading.Thread.__init__(self, *self._args, **self._keywords)
                self.killed = False
                break
            except Exception as ex:
                print('ERROR: threads.py/__init__ failed - ' + str(ex))
                time.sleep(1)
                tries += 1

    def start(self):
        tries = 0
        while tries < 3:
            try:
                self.__run_backup = self.run
                self.run = self.__run
                threading.Thread.start(self)
                break
            except Exception as e:
                print('ERROR: threads.py/start failed - ' + str(e))
                time.sleep(1)
                tries += 1
        # note that this is set True even if all tries failed
        self.is_started = True

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True

    def clone(self, fn):
        return threadWithTrace(target=fn,
                               args=self._args,
                               daemon=True)


def removeDormantThreads(baseDir: str, threads_list: [], debug: bool) -> None:
    """Removes threads whose execution has completed
    """
    if len(threads_list) == 0:
        return

    dormant_threads = []
    curr_time = datetime.datetime.now()
    changed = False

    # which threads are dormant?
    no_of_active_threads = 0
    for thd in threads_list:
        remove_thread = False

        if thd.is_started:
            if not thd.is_alive():
                if (curr_time - thd.start_time).total_seconds() > 10:
                    if debug:
                        print('DEBUG: ' +
                              'thread is not alive ten seconds after start')
                    remove_thread = True
            # timeout for started threads
            if (curr_time - thd.start_time).total_seconds() > 600:
                if debug:
                    print('DEBUG: started thread timed out')
                remove_thread = True
        else:
            # timeout for threads which havn't been started
            if (curr_time - thd.start_time).total_seconds() > 600:
                if debug:
                    print('DEBUG: unstarted thread timed out')
                remove_thread = True

        if remove_thread:
            dormant_threads.append(thd)
        else:
            no_of_active_threads += 1
    if debug:
        print('DEBUG: ' + str(no_of_active_threads) +
              ' active threads out of ' + str(len(threads_list)))

    # remove the dormant threads
    dormant_ctr = 0
    for thd in dormant_threads:
        if debug:
            print('DEBUG: Removing dormant thread ' + str(dormant_ctr))
        dormant_ctr += 1
        threads_list.remove(thd)
        thd.kill()
        changed = True

    # start scheduled threads
    if len(threads_list) < 10:
        ctr = 0
        for thrd in threads_list:
            if not thrd.is_started:
                print('Starting new send thread ' + str(ctr))
                thrd.start()
                changed = True
                break
            ctr += 1

    if not changed:
        return

    if debug:
        send_log_filename = baseDir + '/send.csv'
        try:
            with open(send_log_filename, "a+",
                      encoding='utf-8') as fp_log:
                fp_log.write(curr_time.strftime("%Y-%m-%dT%H:%M:%SZ") +
                             ',' + str(no_of_active_threads) +
                             ',' + str(len(threads_list)) + '\n')
        except BaseException:
            pass
