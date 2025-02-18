import tensorflow as tf
import constants as const


def current_scope():
    return tf.get_variable_scope().name


def current_scope_and_vars():
    scope = current_scope()

    collections = [tf.GraphKeys.MODEL_VARIABLES]
    #DONT USE the below, because it leaves out the moving avg variables
    #collections = [tf.GraphKeys.TRAINABLE_VARIABLES]

    vars_ = []
    for collection in collections:
        vars_.extend(tf.get_collection(collection, scope))

    #for z in tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope):
    #    assert z in vars_
        
    return (scope, vars_)


def add_scope_to_dct(dct, name):
    dct[name] = current_scope_and_vars()


def _floats_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def _int64s_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def leaky_relu(alpha):
    return lambda x: tf.nn.relu(x) + tf.nn.relu(-x) * alpha


def upscale(feats):
    _shape = feats.get_shape()
    h = _shape[1]
    w = _shape[2]
    return tf.image.resize_nearest_neighbor(feats, tf.stack([h * 2, w * 2]))


def mv_unstack(x):
    return tf.reshape(x, [const.BS, const.H, const.W, const.V, -1])


def mv_stack(x):
    return tf.reshape(x, [const.BS, const.H, const.W, -1])


def mv_shape4(chans=1):
    return (const.BS, const.H, const.W, const.V * chans)


def mv_shape5(chans=1):
    return (const.BS, const.H, const.W, const.V, chans)


def rand_elem(tensor, axis):
    n = int(tensor.get_shape()[axis])
    r = tf.rank(tensor)
    idx = tf.multinomial([[1.0] * n], 1)[0, 0]
    idx_ = [0] * axis + idx + [0] * r - axis - 1
    size = [-1] * axis + 1 + [-1] * r - axis - 1
    return tf.slice(tensor, tf.stack(idx_), size)


def tf_random_bg(N):
    color = tf.random_uniform((3,))
    color = tf.tile(tf.reshape(color, (1, 1, 1, 3)), (N, 256, 256, 1))
    return color


def add_feat_to_img(img, feat):
    # img is BS x H x W x C
    # feat is BS x D
    # output is BS x H x W x (C+D)

    bs, h, w, _ = map(int, img.get_shape())
    feat = tf.reshape(feat, (bs, 1, 1, -1))
    tilefeat = tf.tile(feat, (1, h, w, 1))
    return tf.concat([img, tilefeat], axis=3)


def cycle(tensor, idx, axis):
    r = len(tensor.get_shape())
    n = tensor.get_shape()[axis]
    # move idx elements from the front to the back on axis
    start_idx = [0] * r

    head_size = [-1]*r
    head_size[axis] = idx
    head_size = tf.stack(head_size)

    mid_idx = [0]*r
    mid_idx[axis] = idx
    mid_idx = tf.stack(mid_idx)

    tail_size = [-1] * r

    head = tf.slice(tensor, start_idx, head_size)
    tail = tf.slice(tensor, mid_idx, tail_size)
    return tf.concat([tail, head], axis=axis)


def meshgrid2D(bs, height, width):
    with tf.variable_scope("meshgrid2D"):
        grid_x = tf.matmul(
            tf.ones(shape=tf.stack([height, 1])),
            tf.transpose(tf.expand_dims(tf.linspace(0.0, width - 1, width), 1), [1, 0])
        )

        grid_y = tf.matmul(tf.expand_dims(tf.linspace(0.0, height - 1, height), 1),
                           tf.ones(shape=tf.stack([1, width])))
        grid_x = tf.tile(tf.expand_dims(grid_x, 0), [bs, 1, 1], name="grid_x")
        grid_y = tf.tile(tf.expand_dims(grid_y, 0), [bs, 1, 1], name="grid_y")
        return grid_x, grid_y


def batch(tensor):
    return tf.expand_dims(tensor, axis=0)


def interleave(x1, x2, axis):
    x1s = tf.unstack(x1, axis=axis)
    x2s = tf.unstack(x2, axis=axis)
    outstack = []
    for (x1_, x2_) in zip(x1s, x2s):
        outstack.append(x1_)
        outstack.append(x2_)
    return tf.stack(outstack, axis=axis)


def bin_indices(Z, num_bins):
    bin_size = 100.0 / num_bins
    percentiles = tf.stack([tf.contrib.distributions.percentile(Z, bin_size * p)
                            for p in range(num_bins)])
    Z_ = tf.expand_dims(Z, 1)
    in_bin = tf.cast(Z_ > percentiles, tf.float32)
    in_bin *= tf.constant(range(1, num_bins + 1), dtype=tf.float32)
    bin_idx = tf.cast(tf.argmax(in_bin, axis=1), tf.int32)
    return bin_idx


def prob_round(z):
    ''' probabilistically rounds z to floor(z) or ceil(z) '''

    zf = tf.floor(z)
    p = z - zf
    zf = tf.cast(zf, tf.int32)
    zc = zf + 1
    #if p ~= 0, then condition ~= 0 -> zf selected
    #if p ~= 1, then condition ~= 1 -> zc selected
    return tf.where(tf.random_uniform(tf.shape(p)) < p, zc, zf)


def select_p(tensor, p):
    ''' select entries of tensor with probability p'''
    d1 = tf.expand_dims(tf.shape(tensor)[0], axis=0)  # a weird approach
    keep = tf.random_uniform(d1) < p
    return tf.boolean_mask(tensor, keep), keep


def extract_axis3(tensor, index):
    tensor_t = tf.transpose(mv_unstack(tensor), (3, 0, 1, 2, 4))
    base = tf.gather(tensor_t, index)
    base = tf.squeeze(base, axis=1)  # 0 is batch axis
    return base


def rank(tensor):
    return len(tensor.get_shape())

def variable_in_shape(shape, name = 'variable'):
    return tf.get_variable(name, shape)

def norm01(t):
    t -= tf.reduce_min(t)
    t /= tf.reduce_max(t)
    return t

def round2int(t):
    return tf.cast(tf.round(t), tf.int32)

def randidx(N):
    return tf.cast(tf.multinomial([[1.0] * N], 1)[0, 0], tf.int32)

def match_placeholders_to_inputs(phs, inps):
    if isinstance(phs, dict) and isinstance(inps, dict):
        rval = {}
        for name in phs:
            rval.update(match_placeholders_to_inputs(phs[name], inps[name]))
        return rval
    elif isinstance(phs, list) and isinstance(inps, list):
        rval = {}
        for (ph, inp) in zip(phs, inps):
            rval.update(match_placeholders_to_inputs(ph, inp))
        return rval
    elif 'tensorflow' in phs.__class__.__module__ and 'numpy' in inps.__class__.__module__:
        return {phs:inps}
    else:
        print type(phs), type(inps)
        raise Exception, 'unsupported type...'

def batchsize(tensor):
    return int(tuple(tensor.get_shape())[0])

def batchdim(tensor):
    if list(tensor.get_shape())[0] == None:
        return tf.unstack(tf.shape(tensor))[0]
    return list(tensor.get_shape())[0]

def noop(x):
    z = tf.Variable(0.0, dtype = tf.float32)
    return x+z-z, z


def pool3d(x, factor = 2, rank4 = False):
    if rank4:
        assert rank(x) == 4
        x = tf.expand_dims(x, axis = 4)
    return tf.nn.max_pool3d(
        x,
        ksize = [1, factor, factor, factor, 1],
        strides = [1, factor, factor, factor, 1],
        padding = 'VALID'
    )

def unitize(tensor, axis = -1):
    norm = tf.sqrt(tf.reduce_sum(tf.square(tensor), axis = axis, keep_dims = True) + const.eps)
    return tensor / norm

