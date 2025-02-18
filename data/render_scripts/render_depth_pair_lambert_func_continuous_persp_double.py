import os,sys,time, math
import bpy
import random
import numpy as np
import shutil
import scipy.io
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, '../../utils'))
import util 
import OpenEXR
import Imath
import array
import scipy.misc as sm
import mathutils

# scp -r jerrypiglet@128.237.184.26:Bitsync/3dv2017_PBA/data/render_scripts/render_depth_pair_lambert* . && nice -n 10
# blender blank.blend -b -P render_depth_pair_lambert_main_double.py -- ./lists/02958343_select.list ./lists/02958343_select.list NAME 128

# nice -n 10 blender blank.blend -b -P render_depth_pair_lambert_func.py -- 02958343 MODEL RES views model_id

BASE_OUT_DIR = '../data_cache/'
#BASE_OUT_DIR = '/projects/katefgroup/ziyan/'
res_list = [128]

## transfer Z to inverse Z
def get_inverse_depth(Z_path, res):
    file = OpenEXR.InputFile(Z_path)
    dw = file.header()['dataWindow']
    sz = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1) #(H,W)
    
    # Read the three color channels as 32-bit floats
    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    (R,G,B) = [np.reshape(np.asarray(array.array('f', file.channel(Chan, FLOAT))), (sz[0], sz[1], 1)) for Chan in ("R", "G", "B") ]

    return np.reciprocal(R.reshape(res, res))

## determine camera center position by rho, azim, elev
def objectCenteredCamPos(rho,azim,elev):
    phi = np.deg2rad(elev)
    theta = np.deg2rad(azim)
    x = rho*np.cos(theta)*np.cos(phi)
    y = rho*np.sin(theta)*np.cos(phi)
    z = rho*np.sin(phi)
    return [x,y,z]

## camera center position to quaternion
def camPosToQuaternion(camPos):
    [cx,cy,cz] = camPos
    q1 = [0,0,np.sqrt(2)/2,np.sqrt(2)/2]
    camDist = np.linalg.norm([cx,cy,cz])
    cx,cy,cz = cx/camDist,cy/camDist,cz/camDist
    t = np.linalg.norm([cx,cy])
    tx,ty = cx/t,cy/t
    yaw = np.arccos(ty) 
    yaw = 2*np.pi-np.arccos(ty) if tx>0 else yaw
    pitch = 0
    roll = np.arccos(np.clip(tx*cx+ty*cy,-1,1))
    roll = -roll if cz<0 else roll
    q2 = quaternionFromYawPitchRoll(yaw,pitch,roll)    
    q3 = quaternionProduct(q2,q1)
    return q3

## camera rotation along its optical axis; input with camera position and rotation angle; output transformation quaternion
def camRotQuaternion(camPos,theta):
    theta = np.deg2rad(theta)
    [cx,cy,cz] = camPos
    camDist = np.linalg.norm([cx,cy,cz])
    cx,cy,cz = -cx/camDist,-cy/camDist,-cz/camDist
    qa = np.cos(theta/2.0)
    qb = -cx*np.sin(theta/2.0)
    qc = -cy*np.sin(theta/2.0)
    qd = -cz*np.sin(theta/2.0)
    return [qa,qb,qc,qd]

def quaternionProduct(q1,q2): 
    qa = q1[0]*q2[0]-q1[1]*q2[1]-q1[2]*q2[2]-q1[3]*q2[3]
    qb = q1[0]*q2[1]+q1[1]*q2[0]+q1[2]*q2[3]-q1[3]*q2[2]
    qc = q1[0]*q2[2]-q1[1]*q2[3]+q1[2]*q2[0]+q1[3]*q2[1]
    qd = q1[0]*q2[3]+q1[1]*q2[2]-q1[2]*q2[1]+q1[3]*q2[0]
    return [qa,qb,qc,qd]

def quaternionFromYawPitchRoll(yaw,pitch,roll):
    c1 = np.cos(yaw/2.0)
    c2 = np.cos(pitch/2.0)
    c3 = np.cos(roll/2.0)
    s1 = np.sin(yaw/2.0)
    s2 = np.sin(pitch/2.0)
    s3 = np.sin(roll/2.0)
    qa = c1*c2*c3+s1*s2*s3
    qb = c1*c2*s3-s1*s2*c3
    qc = c1*s2*c3+s1*c2*s3
    qd = s1*c2*c3-c1*s2*s3
    return [qa,qb,qc,qd]

def quaternionToRotMatrix(q):
    R = np.array([[1-2*(q[2]**2+q[3]**2),2*(q[1]*q[2]-q[0]*q[3]),2*(q[0]*q[2]+q[1]*q[3])],
                  [2*(q[1]*q[2]+q[0]*q[3]),1-2*(q[1]**2+q[3]**2),2*(q[2]*q[3]-q[0]*q[1])],
                  [2*(q[1]*q[3]-q[0]*q[2]),2*(q[0]*q[1]+q[2]*q[3]),1-2*(q[1]**2+q[2]**2)]])
    return R

def rotMatrixToQuaternion(R):
    t = R[0,0]+R[1,1]+R[2,2]
    r = np.sqrt((1+t).clip(0))
    qa = 0.5*r
    qb = np.sign(R[2,1]-R[1,2])*np.abs(0.5*np.sqrt((1+R[0,0]-R[1,1]-R[2,2]).clip(0)))
    qc = np.sign(R[0,2]-R[2,0])*np.abs(0.5*np.sqrt((1-R[0,0]+R[1,1]-R[2,2]).clip(0)))
    qd = np.sign(R[1,0]-R[0,1])*np.abs(0.5*np.sqrt((1-R[0,0]-R[1,1]+R[2,2]).clip(0)))
    return [qa,qb,qc,qd]

def projectionMatrix(scene,camera):
    scale = camera.data.ortho_scale
    scale_u,scale_v = scene.render.resolution_x/scale,scene.render.resolution_y/scale
    u_0 = scale_u/2.0
    v_0 = scale_v/2.0
    skew = 0 # only use rectangular pixels
    P = np.array([[scale_u,      0,u_0],
                  [0      ,scale_v,v_0]])
    return P

def cameraExtrinsicMatrix(q,camPos):
#    1. The World coordinates: "world"
#       - right-handed
#    2. The Blender camera coordinates: "bcam"
#       - x is horizontal
#       - y is up
#       - right-handed: negative z look-at direction
#    3. The desired computer vision camera coordinates: "cv"
#       - x is horizontal
#       - y is down (to align to the actual pixel coordinates 
#         used in digital images)
#       - right-handed: positive z look-at direction
    R_world2bcam = quaternionToRotMatrix(q).T
    t_world2bcam = -1*R_world2bcam.dot(np.expand_dims(np.array(camPos),-1)) # [[0], [0], [-1]]
    print('t_world2bcam', t_world2bcam)

    R_bcam2world = R_world2bcam.T
    t_bcam2world = -1*R_bcam2world.dot(np.array([[0], [0], [-rho]])) # [[0], [0], [-1]]
    print('t_bcam2world', t_bcam2world)

    R_bcam2cv = np.array([[ 1, 0, 0],
                          [ 0,-1, 0],
                          [ 0, 0,-1]])
    R_world2cv = R_bcam2cv.dot(R_world2bcam)
    t_world2cv = R_bcam2cv.dot(t_world2bcam)
    Rt = np.concatenate([R_world2cv,t_world2cv],axis=1)
    q_world2bcam = rotMatrixToQuaternion(R_world2bcam)
    return Rt, R_world2bcam ,q_world2bcam,t_world2bcam, t_bcam2world# Rt,R_extr(saved), q_extr,t_extr

def obj_centered_camera_pos(dist, azimuth_deg, elevation_deg):
    phi = float(elevation_deg) / 180 * math.pi
    theta = float(azimuth_deg) / 180 * math.pi
    x = (dist * math.cos(theta) * math.cos(phi))
    y = (dist * math.sin(theta) * math.cos(phi))
    z = (dist * math.sin(phi))
    return (x, y, z)

CATEGORY1 = sys.argv[-7]
MODEL1 = sys.argv[-6]
CATEGORY2 = sys.argv[-5]
MODEL2 = sys.argv[-4]
NAME = sys.argv[-3]
RESOLUTION = int(sys.argv[-2])
#VIEWS = int(sys.argv[-2])
BUFFER = int(sys.argv[-1])
idx1 = 1
idx2 = 2

# redirect output to log file
logfile = BASE_OUT_DIR+"tmp/blender_render_model%d.log"%BUFFER

## Blender settings
scene = bpy.context.scene
camera = bpy.data.objects["Camera"]
camera.data.type = "PERSP"
print('aad', camera.data.lens, 'sensor_HW', camera.data.sensor_height, camera.data.sensor_width)
camera.data.lens = 92
#camera.data.sensor_width = 49.303
camera.data.sensor_width = 49.303
camera.data.sensor_height = camera.data.sensor_width

# compositor nodes
scene.render.use_antialiasing = True
scene.render.alpha_mode = "TRANSPARENT"
scene.render.image_settings.color_depth = "16"
scene.render.image_settings.color_mode = "RGBA"
# scene.render.image_settings.file_format = "JPEG"
# scene.world.horizon_color = [255, 255, 255]
scene.render.image_settings.use_zbuffer = True
scene.render.use_compositing = True
scene.use_nodes = True
tree = scene.node_tree
for n in tree.nodes:
    tree.nodes.remove(n)
rl = tree.nodes.new("CompositorNodeRLayers")
fo = tree.nodes.new("CompositorNodeOutputFile")
seg_out_1 = tree.nodes.new(type="CompositorNodeOutputFile")
seg_mask_1 = tree.nodes.new(type="CompositorNodeIDMask")
seg_out_2 = tree.nodes.new(type="CompositorNodeOutputFile")
seg_mask_2 = tree.nodes.new(type="CompositorNodeIDMask")
fo.base_path = BASE_OUT_DIR + "tmp/buffer/{0}/".format(BUFFER)
seg_out_1.base_path = BASE_OUT_DIR + "tmp/buffer/{0}/".format(BUFFER)
seg_out_2.base_path = BASE_OUT_DIR + "tmp/buffer/{0}/".format(BUFFER)
seg_mask_1.index = idx1
seg_mask_2.index = idx2
#seg_mask_1.base_path = BASE_OUT_DIR + "tmp/buffer/{0}/".format(BUFFER)
#seg_mask_2.base_path = BASE_OUT_DIR + "tmp/buffer/{0}/".format(BUFFER)
if not os.path.isdir(fo.base_path):
    os.makedirs(fo.base_path)
fo.format.file_format = "OPEN_EXR"
fo.file_slots.new("RGB")
fo.file_slots.new("Z")
fo.file_slots.new("NORM")
tree.links.new(rl.outputs["Image"],fo.inputs["RGB"])
tree.links.new(rl.outputs["Z"],fo.inputs["Z"])
tree.links.new(rl.outputs["Normal"],fo.inputs["NORM"])
tree.links.new(rl.outputs['IndexOB'], seg_mask_1.inputs['ID value'])
tree.links.new(seg_mask_1.outputs['Alpha'], seg_out_1.inputs['Image'])
tree.links.new(rl.outputs['IndexOB'], seg_mask_2.inputs['ID value'])
tree.links.new(seg_mask_2.outputs['Alpha'], seg_out_2.inputs['Image'])
seg_out_1.file_slots[0].path = 'idx1'
seg_out_2.file_slots[0].path = 'idx2'
#seg_out_1.file_slots[0].path = BASE_OUT_DIR + "tmp/buffer/{}/{}".format(BUFFER, 'idx1')
#seg_out_2.file_slots[0].path = BASE_OUT_DIR + "tmp/buffer/{}/{}".format(BUFFER, 'idx2')
#print(rl.outputs.keys())
#sys.exit()

# set environment lighting
scene.world.light_settings.use_ambient_occlusion = True # https://docs.blender.org/manual/en/dev/render/blender_render/world/ambient_occlusion.html
# scene.world.light_settings.use_environment_light = True
# scene.world.light_settings.environment_energy = 10
# scene.world.light_settings.environment_color = "PLAIN"

# scene.render.resolution_x = RESOLUTION
# scene.render.resolution_y = RESOLUTION
# scene.render.resolution_percentage = 100

## Start rendering
timeStart = time.time()
q_extr_list = []
t_extr_list = []
angles_list = []
t_list = []
R_extr_list = []

#open(logfile, "a").close()
#old = os.dup(1)
#sys.stdout.flush()
#os.close(1)
#os.open(logfile, os.O_WRONLY)

#if CATEGORY == '02958343':
#    shape_file = "/home/ziyanw1/dataset/ShapeNetCore.v1/{0}/{1}/model.obj".format(CATEGORY,MODEL)
#    shape_file = "/projects/katefgroup/shapenet/ShapeNetCore.v1/{0}/{1}/model.obj".format(CATEGORY,MODEL)
#    lights_num = 20
#    scene.world.light_settings.ao_factor = 0.05
#else:
#    shape_file = "/home/ziyanw1/dataset/ShapeNetCore.v2/{0}/{1}/models/model_normalized.obj".format(CATEGORY,MODEL)
#    shape_file = "/projects/katefgroup/shapenet/ShapeNetCore.v2/{0}/{1}/models/model_normalized.obj".format(CATEGORY,MODEL)
#    lights_num = 35
#    scene.world.light_settings.ao_factor = 0.15
#shape_file = "/home/ziyanw1/dataset/ShapeNetCore.v1/{0}/{1}/model.obj".format(CATEGORY,MODEL)
shape_file1 = "/projects/katefgroup/shapenet/ShapeNetCore.v1/{0}/{1}/model.obj".format(CATEGORY1,MODEL1)
shape_file2 = "/projects/katefgroup/shapenet/ShapeNetCore.v1/{0}/{1}/model.obj".format(CATEGORY2,MODEL2)
lights_num = 20
scene.world.light_settings.ao_factor = 0.05
bpy.ops.import_scene.obj(filepath=shape_file1) 

## translate and rotate objects here
rho_max = 0.25
rho_min = 0.15
theta_pool = np.linspace(0, 180, 19)
theta = np.random.choice(theta_pool)
rho1 = np.random.uniform(rho_min, rho_max)
rho2 = np.random.uniform(rho_min, rho_max)
translation1 = (rho1*np.cos(np.deg2rad(theta)), rho1*np.sin(np.deg2rad(theta)), 0)
translation2 = (rho2*np.cos(np.deg2rad(theta+180)), rho2*np.sin(np.deg2rad(theta+180)), 0)
for name in bpy.data.objects.keys():
    if name not in ['Camera', 'Lamp']:
        bpy.data.objects[name].location = bpy.data.objects[name].location + mathutils.Vector(translation1)
        bpy.data.objects[name].scale = (0.5, 0.5, 0.5)

## dump object 1
for res in res_list:
    base_path = BASE_OUT_DIR + 'blender_renderings/'
    save_path = base_path + "res{1}_{2}/{0}".format(BUFFER,res,NAME)
    target_file1 = '{}/obj1.obj'.format(save_path) 
    bpy.ops.export_scene.obj(filepath=target_file1)

for obj in bpy.data.objects:
    obj.select = True
    if 'mesh' in obj.name:
        obj.pass_index = idx1
    obj.select = False

bpy.ops.import_scene.obj(filepath=shape_file2) 
for obj in bpy.data.objects:
    obj.select = True
    if 'mesh' in obj.name:
        if obj.pass_index != idx1:
            obj.pass_index = idx2
    obj.select = False
for name in bpy.data.objects.keys():
    if name not in ['Camera', 'Lamp']:
        if hasattr(bpy.data.objects[name], 'pass_index') and bpy.data.objects[name].pass_index != 1:
            bpy.data.objects[name].location = bpy.data.objects[name].location + mathutils.Vector(translation2)
            bpy.data.objects[name].scale = (0.5, 0.5, 0.5)
## 

print("================= OBJ file loaded sucessfully!=================")

for m in bpy.data.materials:
    m.diffuse_shader = 'LAMBERT'
    m.diffuse_intensity = 0.5
    m.specular_intensity = 0
#     m.use_shadeless = True

bpy.context.scene.world.light_settings.use_environment_light = True
bpy.context.scene.world.light_settings.environment_energy = np.random.uniform(0.5, 1)
bpy.context.scene.world.light_settings.environment_color = 'PLAIN'

for i in range(15):
    light_azimuth_deg = np.random.uniform(0, 360)
    light_elevation_deg  = np.random.uniform(-70, 15)
    # light_elevation_deg  = np.random.uniform(-70, 70)
    light_dist = np.random.uniform(12, 20)
    lx, ly, lz = obj_centered_camera_pos(light_dist, light_azimuth_deg, light_elevation_deg)
    bpy.ops.object.lamp_add(type='POINT', view_align = False, location=(lx, ly, lz))
    bpy.data.objects['Point'].data.energy = max(np.random.normal(20, 4),0)

# uniformly sample rotation angle
# pos = np.inf
# while np.linalg.norm(pos)>1:
#     pos = np.random.rand(3)*2-1
# pos /= np.linalg.norm(pos)
# # print(pos)
# phi = np.arcsin(pos[2])
# theta = np.arccos(pos[0]/np.cos(phi))
# if pos[1]<0: theta = 2*np.pi-theta
# elev = np.rad2deg(phi)
# azim0 = np.rad2deg(theta)
rho = 2
# theta = np.random.rand()*360

#azim0 = 0.
#elev0 = 0.
#theta0 = 0.
# azim_all = azim0 + np.random.normal(loc=0., scale=10., size=(VIEWS,))

## version _all
azim_all = np.linspace(0, 360, 19)
azim_all = azim_all[0:-1]
elev_all = np.linspace(20, 60, 3)
### version _new
#azim_all = np.linspace(0, 360, 13)
#azim_all = azim_all[0:-1]
#elev_all = np.linspace(-90, 90, 7)
#elev_all = elev_all[0:-1]

# elev_all = elev0 + np.random.normal(loc=0., scale=10., size=(VIEWS,))
# elev_all[0] = elev0


#for bkg in range(1):
#    for res in res_list:
#        scene.render.resolution_x = res
#        scene.render.resolution_y = res
#        scene.render.resolution_percentage = 100
#        base_path = BASE_OUT_DIR + 'blender_renderings/'
#        #save_path = base_path + "{2}/res{1}_continuous_0712_infiniteBkg/{0}".format(MODEL,res,CATEGORY)
#        #save_path = base_path + "{2}/res{1}_continuous_0930_persp_iphonev2/{0}".format(MODEL,res,CATEGORY)
#        save_path = base_path + "res{1}_{2}/{0}".format(BUFFER,res,NAME)
#        #save_path = base_path + "{2}/res{1}_debug_perspInfinite/{0}".format(MODEL,res,CATEGORY)
#        #save_path = base_path + "{2}/debug_persp/{0}".format(MODEL,res,CATEGORY)
#        if os.path.exists(save_path):
#            shutil.rmtree(save_path)
#
#        if not os.path.isdir(save_path):
#            os.makedirs(save_path)
#        ## dump category
#        category_file = base_path+"res{1}_{2}/{0}/catgory.txt".format(BUFFER,res,NAME)
#        category_lines = []
#        category_lines.append(CATEGORY1+'\n')
#        category_lines.append(CATEGORY2+'\n')
#        with open(category_file, 'w') as f:
#            f.writelines(category_lines)
#            
#        for i in range(azim_all.shape[0]):
#            for j in range(elev_all.shape[0]):
#                azim = azim_all[i]
#                elev = elev_all[j]
#                theta = 0.
#                camPos = objectCenteredCamPos(rho,azim,elev)
#                q1 = camPosToQuaternion(camPos)
#                q2 = camRotQuaternion(camPos,theta)
#                q = quaternionProduct(q2,q1)
#                Rt,R_extr, q_extr,t_extr, t_bcam2world = cameraExtrinsicMatrix(q,camPos)
#
#                camera.rotation_mode = "QUATERNION"
#                camera.location[0] = camPos[0] #+ t_bcam2world[0]
#                camera.location[1] = camPos[1] #+t_bcam2world[1]
#                camera.location[2] = camPos[2] #+t_bcam2world[2]
#                camera.rotation_quaternion[0] = q[0]
#                camera.rotation_quaternion[1] = q[1]
#                camera.rotation_quaternion[2] = q[2]
#                camera.rotation_quaternion[3] = q[3]
#                camera.data.sensor_height = camera.data.sensor_width
#
#                P = projectionMatrix(scene,camera)
#                # q = np.nan_to_num(q)
#                # q_extr = np.nan_to_num(q_extr)
#
#                scene.render.filepath = "{0}temp.png".format(fo.base_path)
#                bpy.ops.render.render(write_still=True)
#
#                invZ = get_inverse_depth("{0}/Z0001.exr".format(fo.base_path), res)
#                #shutil.copyfile("{0}/Z0001.exr".format(fo.base_path),"{0}/{1}_{2}.exr".format(save_path,int(azim),int(elev)))
#                #shutil.copyfile("{0}/RGB0001.exr".format(fo.base_path),"{0}/{1}_{2}_rgb.exr".format(save_path,int(azim),int(elev)))
#                sm.imsave("{0}/invZ_{1}_{2}.png".format(save_path,int(azim),int(elev)) , invZ)
#                np.save("{0}/invZ_{1}_{2}.npy".format(save_path,int(azim),int(elev)) , invZ)
#                shutil.copyfile(scene.render.filepath,"{0}/RGB_{1}_{2}.png".format(save_path,int(azim),int(elev)))
#
#                q_extr_list.append(np.array(q_extr))
#                t_extr_list.append(np.array(t_extr))
#                angles_list.append(np.stack([azim, elev, theta]))
#                R_extr_list.append(np.array(R_extr))
#
#                ## render mask and seg map
#                bpy.context.scene.render.layers["RenderLayer"].use_pass_object_index = True
#                scene.render.filepath = "{0}temp.png".format(fo.base_path)
#                bpy.ops.render.render(write_still=True)
#                mask1 = sm.imread(BASE_OUT_DIR + "tmp/buffer/{}/{}".format(BUFFER, 'idx10001.png'))
#                mask1 = mask1[:,:,0] * mask1[:,:,3]
#                idx_in_mask1 = np.argwhere(mask1 > 0)
#                bbox_y11, bbox_x11 = idx_in_mask1.min(axis=0) 
#                bbox_y12, bbox_x12 = idx_in_mask1.max(axis=0)
#                bbox1 = np.asarray([bbox_x11, bbox_y11, bbox_x12, bbox_y12])
#                
#                mask2 = sm.imread(BASE_OUT_DIR + "tmp/buffer/{}/{}".format(BUFFER, 'idx20001.png'))
#                mask2 = mask2[:,:,0] * mask2[:,:,3]
#                idx_in_mask2 = np.argwhere(mask2 > 0)
#                bbox_y21, bbox_x21 = idx_in_mask2.min(axis=0) 
#                bbox_y22, bbox_x22 = idx_in_mask2.max(axis=0)
#                bbox2 = np.asarray([bbox_x21, bbox_y21, bbox_x22, bbox_y22])
#                bg = ((np.ones_like(mask1)-mask1-mask2) > 0).astype(mask1.dtype)
#                sm.imsave(
#                    "{0}/SEG_{1}_{2}.png".format(save_path,int(azim),int(elev)),
#                    np.stack([mask1, mask2, bg], axis = 2)*255.0
#                )
#                save_dict = {'bbox1': bbox1, 'bbox2': bbox2}
#                scipy.io.savemat('{}/anno_{}_{}.mat'.format(save_path, int(azim), int(elev)), save_dict)
#
#                ## render amodal segmentation
#                delta = 1000.0
#                delta = mathutils.Vector((delta, delta, delta))
#                
#                #1. move obj 1 out of the way
#                for obj in bpy.data.objects:
#                    obj.select = True
#                    if 'mesh' in obj.name:
#                        if obj.pass_index == idx1:
#                            bpy.data.objects[obj.name].location = bpy.data.objects[obj.name].location + delta
#                    obj.select = False
#                bpy.ops.render.render( write_still=True )
#                amodal2 = sm.imread(BASE_OUT_DIR + "tmp/buffer/{}/{}".format(BUFFER, 'idx20001.png'))
#
#                #2. move obj 1 back into place
#                for obj in bpy.data.objects:
#                    obj.select = True
#                    if 'mesh' in obj.name:
#                        if obj.pass_index == idx1:
#                            bpy.data.objects[obj.name].location = bpy.data.objects[obj.name].location - delta
#                    obj.select = False
#                
#                #3. move obj 2 out of place
#                for obj in bpy.data.objects:
#                    obj.select = True
#                    if 'mesh' in obj.name:
#                        if obj.pass_index == idx2:
#                            bpy.data.objects[obj.name].location = bpy.data.objects[obj.name].location + delta
#                    obj.select = False
#                bpy.ops.render.render( write_still=True )
#                amodal1 = sm.imread(BASE_OUT_DIR + "tmp/buffer/{}/{}".format(BUFFER, 'idx10001.png'))
#                #4. move obj 2 back into place (for completeness... this is optional)
#                for obj in bpy.data.objects:
#                    obj.select = True
#                    if 'mesh' in obj.name:
#                        if obj.pass_index == idx2:
#                            bpy.data.objects[obj.name].location = bpy.data.objects[obj.name].location - delta
#                    obj.select = False
#                amodal1 = amodal1[:,:,0] * amodal1[:,:,3]
#                amodal2 = amodal2[:,:,0] * amodal2[:,:,3]
#                bg = np.logical_and(amodal1 == 0, amodal2 == 0)
#                sm.imsave(
#                    '{0}/amodal_{1}_{2}.png'.format(save_path,int(azim),int(elev)),
#                    np.stack([amodal1, amodal2, bg], axis = 2)*255.0
#                )
#                bpy.context.scene.render.layers["RenderLayer"].use_pass_object_index = False
#
#        trans_path = "{0}/trans_per.mat".format(save_path)
#        save_dict = {'theta': theta, 'translation1': translation1, 'translation2': translation2,
#            'angles_list':np.stack(angles_list), 'R_extr_list':np.stack(R_extr_list),'q_extr_list':np.stack(q_extr_list),
#            't_extr_list':np.array(t_extr_list)}
#        scipy.io.savemat(trans_path, save_dict)

    #if bkg == 0:
    #    bpy.data.objects['cobble'].select = True
    #    bpy.ops.object.delete()
        # bpy.data.objects['cobble'].select = False
    # else:
    #     bpy.data.objects['cobble'].select = True
    #     bpy.ops.object.delete()
#os.close(1)
#os.dup(old)
#os.close(old)
## dump scene
target_file = '{}/scene.obj'.format(save_path) 
bpy.ops.export_scene.obj(filepath=target_file)
## delete object 1
#2. move obj 1 back into place
for obj in bpy.data.objects:
    if obj.pass_index == idx1:
        obj.select = True
bpy.ops.object.delete()
## dump object 2
for res in res_list:
    save_path = base_path + "res{1}_{2}/{0}".format(BUFFER,res,NAME)
    target_file2 = '{}/obj2.obj'.format(save_path) 
    bpy.ops.export_scene.obj(filepath=target_file2)

# clean up
for o in bpy.data.objects:
    if o==camera: continue
    o.select = True
bpy.ops.object.delete()
for m in bpy.data.meshes:
    bpy.data.meshes.remove(m)
for m in bpy.data.materials:
    m.user_clear()
    bpy.data.materials.remove(m)

print(util.toGreen("#{2} done, time={0:.4f} sec. Model saved to {2}".format(time.time()-timeStart, trans_path, BUFFER)))
