# coding=utf-8

import wexpect
import threading
import queue
import time
import datetime
from util import *
           

class ADBManager:
    def __init__(self, config):
        self.adb = './adb/adb.exe'
        self.device = "/dev/input/event8"
        pipe = wexpect.spawn(self.adb + ' ' + config['adb_init_cmd'])
        pipe.expect(['connected', wexpect.EOF])
        # 链接shell
        self.shell_pipe = wexpect.spawn(self.adb + ' shell')
        
        self.key_status = {'1': 0}
        # print(self.key_status)
        # 后台shell
        #self.shell_queue = queue.Queue()
        self.cmd_list = []
        # 任务管理
        self.task_dict = {}
        self.shell_thre = threading.Thread(target=self._adb_send_loop)
        self.shell_thre.start()
        self.current_key = '1'
        self.current_updown = '-1' # -1无定义 0UP 1DOWN
        self.last_events = 0
        

    def stop_loop(self):
        self.release_all_keys()
        self._adb_send_cmd(['exit'])
        self.shell_thre.join()

    def release_all_keys(self):
        for i in self.key_status:
            self.send_release_event(i)
    

    def set_key_status(self, actions):
        for action in actions:
            if action == 0:
                continue
            idx = abs(action) - 1
            code = self.key_config[idx]['code']
            if action > 0:
                self.send_press_event(code)
            else:
                self.send_release_event(code)

    def get_key_status(self):
        return self.key_status
    
    def get_key_status_list(self):
        return [self.key_status[i] for i in self.key_status]
    
    def _adb_send_loop(self):
        c = 0
        to_del = []
        while True:
            # check
            check_time = time.perf_counter()
            count = len(self.cmd_list)
            if count:
                cmd = '\n'.join(self.cmd_list)
                # print(cmd)
                # print('---==%05d==---' % c)
                c += 1
                self.shell_pipe.sendline(cmd)
                if 'exit' in self.cmd_list:
                    break
                
                
                self.cmd_list = []
                pass_time = time.perf_counter() - check_time
                # print("%d - %d - %0.4f" % (last_events, count, pass_time))
            else:
                time.sleep(0.0001)
            self.last_events = count
        # print('loop_done')
    
    def _adb_send_cmd(self, cmd):
        # print(cmd)
        # self.shell_queue.put(cmd)
        self.cmd_list.append(' '.join(cmd))
        # print(self.shell_pipe.readline())
    
    def _adb_send_event(self, param):
        self._adb_send_cmd(['sendevent', self.device] + param)
        
    def _send_syn_event(self):
        self._adb_send_event(['0', '0', '0'])

    def _send_update_ptr(self, code):
        if self.current_key != code:
            self._adb_send_event(['3', '47', code]) # ABS_MT_SLOT
            self.current_key = code
            
    def _send_update_updown(self, is_up): 
        if (is_up and self.current_updown != '0') or (not is_up and self.current_updown != '1'):
            self.current_updown = '0' if is_up else '1'
            self._adb_send_event(['1', '330', self.current_updown])
        
    def _send_touch_event(self, code, is_up, xy=None):
        # check status:
        if self.key_status[code] == 0 ^ is_up:
            # print(("up" if is_up else "down") + code)
            # step1 update current device ptr  ABS_MT_SLOT
            self._send_update_ptr(code)
            # step2 flash current code id      ABS_MT_TRACKING_ID
            self._adb_send_event(['3', '57', '-1' if is_up else self.current_key])
            # step 2.5 if there is xy
            if xy:
                self._send_position_event(*xy)
            # step3 up/down
            self._send_update_updown(is_up)
            # step4 sync
            self._send_syn_event()
            # fresh state
            self.key_status[code] = 0 if is_up else 1
        
    def send_release_event(self, code='1'):
        self._send_touch_event(code, True)

    def send_press_event(self, xy=None, code='1'):
        # if xy is None: then repeat the last position
        self._send_touch_event(code, False, xy=xy)

    def _send_position_event(self, x, y):
        self._adb_send_event(['3', '53', str(x)])
        self._adb_send_event(['3', '54', str(y)])
        
    def send_tap_event(self, x, y, duration=0,  code='1'):
        self.send_press_event(xy=(x, y), code=code)
        if duration > 0:
            time.sleep(duration)
        self.send_release_event()
    
    def send_move_event(self):
        pass
        # this is a demo showing how to drag:
        # press_event
        # then _send_position_event + _send_syn_event()
        # finally release
        # use adb shell getevent -l to monitor events!
        
       
if __name__ == '__main__':
    cfg = load_cfg()
    f = ADBManager(cfg)
    f.send_tap_event(300, 200, duration=5)
    time.sleep(1)
    f.stop_loop()