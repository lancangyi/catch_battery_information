# -*- coding: utf-8 -*-
##################################################
## This tool intended to reach battery cycle test
## for reliability team
##################################################
## Open source
##################################################
## Author: Casper Chang
## Copyright: Copyright 2019, Fircrest
## Version: 1.1.0
## Email: casper_chang@wistron.com
## Status: Dev status
##################################################

import time
import sys
import datetime
import argparse
import subprocess
import os.path

file_name_prefix = "/usr/local/"
file_name_default = "bat_rel_test_"
file_name_suffix = ".txt"

battery_status_file = "/sys/class/power_supply/sbs-12-000b/status"
g_low_boundary = 5
g_high_boundary = 100
g_default_cycle = 20
g_default_delay_sec = 60


def get_ec_version():
    proc1 = subprocess.Popen(['ectool', 'version'], stdout=subprocess.PIPE)
    out, err = proc1.communicate()
    if not err:
        if out:
            return out
        else:
            return 'ret_err'
    return 'ret_err'

def verify_environment():
    # 1. print ec version
    current_ec_version = get_ec_version()
    print("Current ec version:" + str(current_ec_version))
    return True


def set_chargecontrol_discharge():
    # ./wstec chargecontrol discharge
    args = ("ectool", "chargecontrol", "discharge")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    return(output)

def set_chargecontrol_normal():
    # ./wstec chargecontrol normal
    args = ("ectool", "chargecontrol", "normal")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    return(output)

def get_time_str():
    return "{0:%Y-%m-%d_%H_%M_%S}".format(datetime.datetime.now())

def get_time_short_str():
    return "{0:%Y-%m-%d}".format(datetime.datetime.now())

def get_charge_state():
    battery_status_file = "/sys/class/power_supply/sbs-12-000b/status"
    with open(battery_status_file) as f:
        content = f.readlines()[0].strip()
        print("[DEBUG] get_charge_state: " + content)
        return content.lower()

def get_battery_RSOC():
    battery_status_file = "/sys/class/power_supply/sbs-12-000b/capacity"
    with open(battery_status_file) as f:
        content = f.readlines()[0].strip()
        return int(content)

def get_battery_current_now():
    battery_status_file = "/sys/class/power_supply/sbs-12-000b/current_now"
    with open(battery_status_file) as f:
        content = f.readlines()[0].strip()
        return int(content)

def get_battery_voltage_now():
    battery_status_file = "/sys/class/power_supply/sbs-12-000b/voltage_now"
    with open(battery_status_file) as f:
        content = f.readlines()[0].strip()
        return int(content)

def get_battery_charge_full():
    battery_status_file = "/sys/class/power_supply/sbs-12-000b/charge_full"
    with open(battery_status_file) as f:
        content = f.readlines()[0].strip()
        return int(content)

def get_h1_version():
    args = ("gsctool", "-t", "-f")
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read()
    return(output)

def init_file_header(file_name):
    hs = open(file_name,"a")
    header = "        Time           Cycle           RSOC           current_now          voltage_now         charge_full"
    print(header)
    hs.write("{}\n".format(header))

def file_append_by_string(file_name, append_string):
    hs = open(file_name,"a")
    print(append_string)
    hs.write("{}\n".format(append_string))

def init_args():
    # arguments
    parser = argparse.ArgumentParser(description='perform battery stress test')
    parser.add_argument('--cycle', dest='iterations', type=int, metavar='int', help='iterations to serve the test, defult = 20 iterations')
    parser.add_argument('--delay', dest='delay', type=int, metavar='int', help='interval time between each log, default = 60 sec')
    parser.add_argument('--file', dest='file_name', type=int, metavar='string', help='assign file name of output file, default = bat_rel_test_[start_date].txt')
    parser.add_argument('--max', dest='high_boundary', type=int, metavar='int', help='assign high RSOC boundary, default = 100')
    parser.add_argument('--min', dest='low_boundary', type=int, metavar='int', help='assign low RSOC boundary, default = 5')

    args = parser.parse_args()
    if args.iterations:
        iterations = args.iterations
    else:
        iterations = g_default_cycle

    if args.delay:
        delay = args.delay
    else:
        delay = g_default_delay_sec

    if args.file_name:
        log_file_name = file_name_prefix + file_name + file_name_suffix
    else:
        log_file_name = file_name_prefix + file_name_default + get_time_str() + file_name_suffix

    if args.high_boundary:
        high_boundary = args.high_boundary
    else:
        high_boundary = g_high_boundary

    if args.low_boundary:
        low_boundary = args.low_boundary
    else:
        low_boundary = g_low_boundary

    print("[DEBUG] log_file_name = " + log_file_name)

    # TODO: extent if new args
    return {"iterations" : iterations,
            "delay" : delay,
            "file_name" : log_file_name,
            "high_boundary" : high_boundary,
            "low_boundary" : low_boundary}


def main():
    
    arg_dict = init_args()
    if not verify_environment():
        return
    iterations = arg_dict['iterations']
    delay = arg_dict['delay']
    file_name = arg_dict['file_name']
    high_boundary = arg_dict['high_boundary']
    low_boundary = arg_dict['low_boundary']

    print("[DEBUG] start --- iteration = "  + str(iterations) +  "   " + str(delay))

    if "discharging" == get_charge_state():
        print("connect AC and try again ... ")
        return

    cycle = 1
    loop = 1
    state = ["init_state", "trans_discharge_state", "discharge_state", "trans_charge_state",  "charge_state"]
    current_state = 0

    init_file_header(file_name)

    # Main loop
    try:

        while cycle <= iterations:
            is_break = 0
            while 1:
                if state[current_state] == "init_state":
                    # check if in the boundary
                    # if lower than high boudary keep init state as charge
                    # if over high boudary switch to discharge_state, break loop
                    init_RSOC = get_battery_RSOC()
                    print("[DEBUG] init_RSOC = " + str(init_RSOC) + " | high_boundary = " + str(high_boundary) + " | low_boundary = " + str(low_boundary))

                    if init_RSOC >= high_boundary:
                        print("[DEBUG]" + get_time_str() + " init state, switch to trans_discharge_state")
                        current_state = 1

                elif state[current_state] == "trans_discharge_state":
                    # TODO: insert stop charge tool
                    set_chargecontrol_discharge()
                    time.sleep(1)

                    print("[DEBUG]" + get_time_str() + " switch to discharge_state")
                    current_state = 2

                elif state[current_state] == "discharge_state":
                    # waiting for hit low boudary and start to charge
                    #init_RSOC = get_battery_RSOC()
                    print("[DEBUG] current RSOC = " + str(init_RSOC) + " | high_boundary = " + str(high_boundary) + " | low_boundary = " + str(low_boundary))
                    if get_battery_RSOC() <= low_boundary:
                        # break loop to increase cycle
                        print("[DEBUG]" + get_time_str() + " switch to trans_charge_state")
                        current_state = 3

                elif state[current_state] == "trans_charge_state":
                    # TODO: insert start charge tool
                    set_chargecontrol_normal()
                    print("[DEBUG]" + get_time_str() + " switch to charge_state")
                    time.sleep(10)

                    current_state = 4

                else: # charge_state
                    # waiting for hit high boudary and stop to charge
                    if get_battery_RSOC() >= high_boundary:
                        print("[DEBUG]" + get_time_str() + " switch to discharge_state")
                        current_state = 1
                        is_break = 1

                print("[DEBUG] cycle = " + str(cycle) +" | current state = " + state[current_state] + " | RSOC = " + str(get_battery_RSOC()))
                # append_string = "Time           Cycle           RSOC(%)           current_now       voltage_now        charge_full"
                append_string = '%s    %s               %s             %s                 %s             %s' %(get_time_str(), str(cycle), str(get_battery_RSOC()), str(get_battery_current_now()), str(get_battery_voltage_now()), str(get_battery_charge_full()))
                file_append_by_string(file_name, append_string)

                if is_break == 1:
                    print("[DEBUG]  Break and cycle increasing")
                    break
                time.sleep(delay)

            cycle = cycle + 1


    except KeyboardInterrupt:
        set_chargecontrol_normal()
        print("Keyboard Interrupt, set chargecontrol normal")


if __name__ == "__main__":
    main()
