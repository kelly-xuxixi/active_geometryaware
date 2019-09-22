import os,sys,time, math
import bpy
import numpy as np
import shutil
import scipy.io
from functools import partial
from multiprocessing.dummy import Pool
from subprocess import call
import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, '../../utils'))
import util

def run(CATEGORY, MODLE_LIST, NAME):
    # nice -n 10 blender blank.blend -b -P render_depth_pair.py -- 02958343 ../blender_renderings/02958343.list 128 views

    # scp -r jerrypiglet@128.237.184.26:/Users/jerrypiglet/Bitsync/3dv2017_PBA/data/render_scripts/render_depth_pair_lambert_*.py . && nice -n 10 blender blank.blend -b -P render_depth_pair_lambert_main.py -- 02958343 ./lists/02958343.list 128 100

    # scp -r
    # jerrypiglet@128.237.129.33:/Users/jerrypiglet/Bitsync/3dv2017_PBA/data/render_scripts/render_depth_pair_lambert_*.py .
    # && nice -n 10 blender blank.blend -b -P render_depth_pair_lambert_main.py -- /home/rz1/Dropbox/blank_infinite.blend 02958343 /home/rz1/Documents/Projects/Chen-Hsuans/3dgen/data/PTNlist/02958343_testids.txt 128 200

    print(sys.argv)

    BLENDER_FILE = "blank.blend"
    RESOLUTION = 128
    pool_num = 16

    ## Start rendering
    listFile = open(MODLE_LIST)
    commands = []
    model_index = 0

    print(util.toMagenta('=== Generating rendering commands...'))
    for line in listFile:
        if CATEGORY in line.strip():
            MODEL = line.strip().split("/")[1]
        else:
            MODEL = line.strip()
        command = 'nice -n 10 blender %s -b -P render_depth_pair_lambert_func_continuous_persp_template.py -- %s %s %s %d %d' \
                  % (BLENDER_FILE, CATEGORY, MODEL, NAME, RESOLUTION, model_index)
        # command = 'nice -n 10 blender %s -b -P render_depth_pair_lambert_func_continuous_template_persp.py -- %s %s %d %d %d'\
        #    %(BLENDER_FILE, CATEGORY, MODEL, RESOLUTION, VIEWS, model_index)
        commands.append(command)
        model_index += 1
        print(command)
    # for debug
    # if model_index >= 5:
    #    break

    print(
        util.toMagenta('=== Rendering %d commands on %d workers, it takes a long time...' % (len(commands), pool_num)))
    pool = Pool(pool_num)
    for idx, return_code in enumerate(pool.imap(partial(call, shell=True), commands)):
        # print(util.toBlue('[%s] Rendering command %d of %d: %s' % (datetime.datetime.now().time(), idx, len(commands), commands[idx])))
        if return_code != 0:
            print(util.toYellow('Rendering command %d of %d (\"%s\") failed' % (idx, len(commands), commands[idx])))


if __name__=="__main__":
    d = {
        "02691156": "airplane",
        "03001627": "chair",
        "03636649": "lamp",
        "04379243": "table",
        "04530566": "vessel",
    }
    for cat_num in d.keys():
        run(cat_num, "lists/%s_lists", d[cat_num])
