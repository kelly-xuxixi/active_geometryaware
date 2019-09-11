import os
import sys


category = sys.argv[1]
file = open(category + ".list")
target_dir = category + "_lists"
try:
    os.mkdir(target_dir)
except:
    pass
lines = file.readlines()
total_len = len(lines)

train_name = os.path.join(target_dir, 'train_idx.txt')
val_name = os.path.join(target_dir, 'val_idx.txt')
test_name = os.path.join(target_dir, 'test_idx.txt')
all_name = os.path.join(target_dir, 'all_idx.txt')

train_list = [lines[i] for i in range(int(total_len * 0.7))]
val_list = [lines[i] for i in range(int(total_len * 0.1))]
test_list = [lines[i] for i in range(int(total_len * 0.2))]
all_list = [lines[i] for i in range(total_len)]

with open(train_name, 'w') as f:
    f.writelines(train_list)

with open(val_name, 'w') as f:
    f.writelines(val_list)

with open(test_name, 'w') as f:
    f.writelines(test_list)

with open(all_name, 'w') as f:
    f.writelines(all_list)

print train_list[:10]
