global FLAGS
flags = tf.flags
flags.DEFINE_integer('gpu', 0, "GPU to use [default: GPU 0]")
# task and control (yellow)
flags.DEFINE_string('model_file', 'pcd_ae_1_lmdb', 'Model name')
flags.DEFINE_string('cat_name', 'airplane', 'Category name')
flags.DEFINE_string('category', '03001627', 'category Index')
flags.DEFINE_string('train_filename_prefix', 'train', '')
flags.DEFINE_string('val_filename_prefix', 'val', '')
flags.DEFINE_string('test_filename_prefix', 'test', '')
flags.DEFINE_float('delta', 10.0, 'angle of each movement')
#flags.DEFINE_string('LOG_DIR', '/newfoundland/rz1/log/summary', 'Log dir [default: log]')
flags.DEFINE_string('LOG_DIR', './log_agent', 'Log dir [default: log]')
flags.DEFINE_string('data_path', './data/lmdb', 'data directory')
flags.DEFINE_string('data_file', 'rgb2depth_single_0212', 'data file')
#flags.DEFINE_string('CHECKPOINT_DIR', '/newfoundland/rz1/log', 'Log dir [default: log]')
flags.DEFINE_string('CHECKPOINT_DIR', './log_agent', 'Log dir [default: log]')
flags.DEFINE_integer('max_ckpt_keeps', 10, 'maximal keeps for ckpt file [default: 10]')
flags.DEFINE_string('task_name', 'tmp', 'task name to create under /LOG_DIR/ [default: tmp]')
flags.DEFINE_boolean('restore', False, 'If resume from checkpoint')
flags.DEFINE_integer('restore_iter', 0, '')
flags.DEFINE_boolean('pretrain_restore', False, 'If resume from checkpoint')
flags.DEFINE_string('pretrain_restore_path', 'log_agent/pretrain_models/pretrain_model.ckpt-5', '')
flags.DEFINE_string('ae_file', '', '')
# train (green)
flags.DEFINE_integer('num_point', 2048, 'Point Number [256/512/1024/2048] [default: 1024]')
flags.DEFINE_integer('resolution', 128, '')
flags.DEFINE_integer('voxel_resolution', 64, '')
flags.DEFINE_string('opt_step_name', 'opt_step', '')
flags.DEFINE_string('loss_name', 'sketch_loss', '')
flags.DEFINE_integer('batch_size', 4, 'Batch Size during training [default: 32]')
flags.DEFINE_float('learning_rate', 1e-3, 'Initial learning rate [default: 0.001]') #used to be 3e-5
flags.DEFINE_float('momentum', 0.95, 'Initial learning rate [default: 0.9]')
flags.DEFINE_string('optimizer', 'adam', 'adam or momentum [default: adam]')
flags.DEFINE_integer('decay_step', 5000000, 'Decay step for lr decay [default: 200000]')
flags.DEFINE_float('decay_rate', 0.7, 'Decay rate for lr decay [default: 0.8]')
flags.DEFINE_integer('max_iter', 1000000, 'Decay step for lr decay [default: 200000]')
# arch (magenta)
flags.DEFINE_string('network_name', 'ae', 'Name for network architecture used for rgb to depth')

flags.DEFINE_string('unet_name', 'U_SAME', '')
#options: U_SAME, OUTLINE
flags.DEFINE_string('agg_name', 'GRU', '')
#options: GRU, OUTLINE

flags.DEFINE_integer('agg_channels', 16, 'agg_channels')

flags.DEFINE_boolean('if_deconv', True, 'If add deconv output to generator aside from fc output')
flags.DEFINE_boolean('if_constantLr', True, 'If use constant lr instead of decaying one')
flags.DEFINE_boolean('if_en_bn', True, 'If use batch normalization for the mesh decoder')
flags.DEFINE_boolean('if_gen_bn', False, 'If use batch normalization for the mesh generator')
flags.DEFINE_boolean('if_bn', True, 'If use batch normalization for the mesh decoder')
flags.DEFINE_boolean('if_dqn_bn', True, 'If use batch normalization for the mesh decoder')
flags.DEFINE_float('bn_decay', 0.95, 'Decay rate for batch normalization [default: 0.9]')
flags.DEFINE_boolean("if_transform", False, "if use two transform layers")
flags.DEFINE_float('reg_weight', 0.1, 'Reweight for mat loss [default: 0.1]')
flags.DEFINE_boolean("if_vae", False, "if use VAE instead of vanilla AE")
flags.DEFINE_boolean("if_l2Reg", False, "if use l2 regularizor for the generator")
flags.DEFINE_boolean("if_dqn_l2Reg", False, "if use l2 regularizor for the policy network")
flags.DEFINE_float('vae_weight', 0.1, 'Reweight for mat loss [default: 0.1]')
flags.DEFINE_boolean('use_gan', False, 'if using GAN [default: False]')
flags.DEFINE_boolean('use_coef', False, 'if use coefficient for loss')
flags.DEFINE_float('loss_coef', 10, 'Coefficient for reconstruction loss [default: 10]')
flags.DEFINE_float('reward_weight', 10, 'rescale factor for reward value [default: 10]')
flags.DEFINE_float('penalty_weight', 0.0005, 'rescale factor for reward value [default: 10]')
flags.DEFINE_float('reg_act', 0.1, 'Reweight for mat loss [default: 0.1]')
flags.DEFINE_float('iou_thres', 0.4, 'Reweight for computing iou [default: 0.5]')
flags.DEFINE_boolean('random_pretrain', False, 'if random pretrain mvnet')
flags.DEFINE_integer('burin_opt', 0, '0: on all, 1: on last, 2: on first [default: 0]')
flags.DEFINE_boolean('dqn_use_rgb', True, 'use rgb for dqn')
flags.DEFINE_boolean('finetune_dqn', False, 'use rgb for dqn')
flags.DEFINE_boolean('finetune_dqn_only', False, 'use rgb for dqn')
flags.DEFINE_string('explore_mode', 'active', '')
flags.DEFINE_string('burnin_mode', 'random', '')
flags.DEFINE_integer('burnin_start_iter', 0, '0 [default: 0]')
flags.DEFINE_boolean("use_critic", False, "if save evaluation results")
flags.DEFINE_boolean("debug_train", False, "if save evaluation results")
flags.DEFINE_boolean("occu_only", False, "Not using rgb value")
# log and drawing (blue)
flags.DEFINE_boolean("is_training", True, 'training flag')
flags.DEFINE_boolean("force_delete", False, "force delete old logs")
flags.DEFINE_boolean("if_summary", True, "if save summary")
flags.DEFINE_boolean("if_save", True, "if save")
flags.DEFINE_integer("save_every_step", 10, "save every ? step")
flags.DEFINE_boolean("if_test", True, "if test")
flags.DEFINE_integer("test_every_step", 2, "test every ? step")
flags.DEFINE_boolean("if_draw", True, "if draw latent")
flags.DEFINE_integer("draw_every_step", 1000, "draw every ? step")
flags.DEFINE_integer("vis_every_step", 1000, "draw every ? step")
flags.DEFINE_boolean("if_init_i", False, "if init i from 0")
flags.DEFINE_integer("init_i_to", 1, "init i to")
flags.DEFINE_integer("test_iter", 2, "init i to")
flags.DEFINE_integer("test_episode_num", 2, "init i to")
flags.DEFINE_boolean("save_test_results", True, "if init i from 0")
flags.DEFINE_boolean("if_save_eval", False, "if save evaluation results")
flags.DEFINE_boolean("initial_dqn", False, "if initial dqn")
# reinforcement learning
flags.DEFINE_integer('mvnet_resolution', 224, 'image resolution for mvnet')
flags.DEFINE_integer('max_episode_length', 4, 'maximal episode length for each trajactory')
flags.DEFINE_integer('mem_length', 1000, 'memory length for replay memory')
flags.DEFINE_integer('action_num', 8, 'number of actions')
flags.DEFINE_integer('burn_in_length', 10, 'burn in length for replay memory')
flags.DEFINE_integer('burn_in_iter', 10, 'burn in iteration for MVnet')
flags.DEFINE_string('reward_type', 'IoU', 'reward type: [IoU, IG]')
flags.DEFINE_float('init_eps', 0.95, 'initial value for epsilon')
flags.DEFINE_float('end_eps', 0.05, 'initial value for epsilon')
flags.DEFINE_float('epsilon', 0, 'epsilon')
flags.DEFINE_float('gamma', 0.99, 'discount factor for reward')
flags.DEFINE_boolean('debug_single', False, 'debug mode: using single model')
flags.DEFINE_boolean('debug_mode', False, '')
flags.DEFINE_boolean('GBL_thread', False, '')
#whether to introduce pose noise to the unprojection
flags.DEFINE_boolean('pose_noise', False, '')
# some constants i moved inside
flags.DEFINE_float('BN_INIT_DECAY', 0.5, '')
flags.DEFINE_float('BN_DECAY_DECAY_RATE', 0.5, '')
flags.DEFINE_float('BN_DECAY_DECAY_STEP', -1, '')
flags.DEFINE_float('BN_DECAY_CLIP', 0.99, '')

FLAGS = flags.FLAGS
