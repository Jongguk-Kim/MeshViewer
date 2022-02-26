try: 
    import pyvista as pv
except: 
    os.system("pip install pyvista")
    
import vtk 
import numpy as np 

class MESH(): 
    def __init__(self, meshfile, centering=False) : 
        self.meshfile = meshfile 
        
        self.grid, self.edges, self.pt_cloud, self.surfaces, self.nodes, self.idx_element, self.cells  = \
            load_pyVista_mesh(meshfile, centering=centering)

        


def readInp(fname): 

    with open(fname) as F: 
        lines = F.readlines()
    nodes =[]
    s8=[]
    cmd = False 
    offset = 0 
    index_elements=[]
    no_changeXZ = True 
    mtype = 9
    for line in lines: 
        if "**" in line: 
            if "END OF MATERIAL INFO" in line: 
                no_changeXZ = False 
            continue 
        # if "TREADPTN_NIDSTART_NIDOFFSET_EIDSTART_EIDOFFSET" in line.upper(): 
        #     wds = line.split(",")
        #     offset = int(wds[-1].strip())
        # if "OFFSET" in line.upper() and not "TREADPTN" in line.upper(): 
        #     wds = line.split("=")
        #     offset = int(wds[1].strip())
        if "*" in line: 
            if "*NODE" in line.upper(): 
                cmd = 'n'
            elif "*ELEMENT" in line.upper() and "C3D8" in line.upper(): 
                cmd = 'n8'
            elif "*ELEMENT" in line.upper() and "C3D6" in line.upper(): 
                cmd = 'n6'
            elif "*ELEMENT" in line.upper() and "MGAX1" in line.upper(): 
                cmd = 'n2'
            elif "*ELEMENT" in line.upper() and "CGAX3" in line.upper(): 
                cmd = 'n3'
            elif "*ELEMENT" in line.upper() and "CGAX4" in line.upper():
                mtype =  5 
                cmd = 'n4'
            else: 
                cmd = False 
        else: 
            wds = line.split(",")
            if cmd == 'n': 
                if no_changeXZ: 
                    nodes.append([ float(wds[0].strip()), float(wds[1].strip()), float(wds[2].strip()), float(wds[3].strip())  ])
                    
                else: 
                    nodes.append([ float(wds[0].strip()), float(wds[3].strip()), float(wds[2].strip()), float(wds[1].strip())  ])
            if cmd == 'n8':
                s8.append([8, 
                            int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[4].strip()), 
                            int(wds[5].strip()), int(wds[6].strip()), int(wds[7].strip()), int(wds[8].strip())
                            ])
                index_elements.append([int(wds[0].strip()), len(s8)]) 
            if cmd == 'n6':
                s8.append([8, 
                            int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[3].strip()), 
                            int(wds[4].strip()), int(wds[5].strip()), int(wds[6].strip()), int(wds[6].strip())
                            ]) 
                index_elements.append([int(wds[0].strip()), len(s8)]) 
            
            # if cmd == 'n2':
            #     s8.append([4, 
            #                 int(wds[1].strip()), int(wds[1].strip()), int(wds[2].strip()), int(wds[2].strip())
            #               ]) 
            #     index_elements.append([int(wds[0].strip()), len(s8)]) 
            # if cmd == 'n3':
            #     s8.append([4, 
            #                 int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[3].strip())
            #               ]) 
            #     index_elements.append([int(wds[0].strip()), len(s8)]) 
            if cmd == 'n4':
                s8.append([4, 
                            int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[4].strip())
                          ]) 
                index_elements.append([int(wds[0].strip()), len(s8)]) 

    return nodes, s8, index_elements, mtype

def readMesh_pyVista(fname,  files=None, centering=False): 
    
    nodes, s8, idx_element, meshtype = readInp(fname)
    nodes = np.array(nodes)
    s8 = np.array(s8)

    if not isinstance(files, type(None)): 
        for file in files: 
            nds, sd, idx_element, meshtype = readInp(file) 
            nodes = np.concatenate((nodes, np.array(nds)), axis=0)
            s8 = np.concatenate((s8, np.array(sd)), axis=0)


    print (" Number of nodes : %d"%(len(nodes)))
    print (" Number of 8-node elements : %d"%(len(s8)))

    idmax = int(np.max(nodes[:,0]))
    if centering: 
        md = np.average(nodes[:,1]) 
        nodes[:,1] -= md 
        print (" shift %.6f"%(md))

    npn = np.zeros(shape=(idmax+1, 4))

    for n in nodes: 
        npn[int(n[0])][0]=n[0]
        npn[int(n[0])][1]=n[1]
        npn[int(n[0])][2]=n[2]
        npn[int(n[0])][3]=n[3]
    return npn, np.array(s8).ravel(), idx_element, s8, meshtype


# def readSmallMesh_pyVista(fname): 
#     nodes, s8, idx_element, meshtype = readInp(fname)
#     nodes = np.array(nodes)
#     s8 = np.array(s8)

#     solids=[]
#     for s in s8: 
#         ix1=np.where(nodes[:,0] == s[1])[0][0]
#         ix2=np.where(nodes[:,0] == s[2])[0][0]
#         ix3=np.where(nodes[:,0] == s[3])[0][0]
#         ix4=np.where(nodes[:,0] == s[4])[0][0]
#         ix5=np.where(nodes[:,0] == s[5])[0][0]
#         ix6=np.where(nodes[:,0] == s[6])[0][0]
#         ix7=np.where(nodes[:,0] == s[7])[0][0]
#         ix8=np.where(nodes[:,0] == s[8])[0][0]
#         solids.append([8, ix1, ix2, ix3, ix4, ix5, ix6, ix7, ix8]) 

#     return nodes, np.array(solids).ravel(), meshtype
    

def makePyvisterCells(cells, nodes, meshtype): 
    nCell = int(len(cells)/meshtype)

    xyz = nodes[:,1:4]

    # each cell is a VTK_HEXAHEDRON
    celltypes = np.empty(nCell, dtype=np.uint16) 
    celltypes[:] = vtk.VTK_HEXAHEDRON 

    # if you are not using VTK 9.0 or newer, you must use the offset array
    # grid = pv.UnstructuredGrid(offset8, cells, celltypes, xyz) 

    #  if you are using VTK 9.0 or newer, you do not need to input the offset array:
    # grid = pv.UnstructuredGrid(cells, celltypes, xyz)

    # # Alternate versions:
    # grid = pv.UnstructuredGrid({vtk.VTK_HEXAHEDRON: cells.reshape([-1, meshtype])[:, 1:]}, xyz)
    grid = pv.UnstructuredGrid({vtk.VTK_HEXAHEDRON: np.delete(cells, np.arange(0, cells.size, meshtype))}, xyz)

    return grid, xyz  

def load_pyVista_mesh(file_name, centering=False): 

    nodes, cells, idx_element, elements, meshtype = readMesh_pyVista(file_name, centering=centering)
    grid, xyz = makePyvisterCells(cells, nodes, meshtype)

    pt_cloud = pv.PolyData(xyz)
    if meshtype ==9: 
        edges = grid.extract_feature_edges(feature_angle=45, boundary_edges=False)
        surfaces = grid.extract_surface()
        print(" Mesh Volume", grid.volume)
    else: 
        edges = grid.extract_all_edges()
        surfaces = None 
    
    return grid, edges, pt_cloud, surfaces, nodes, idx_element, elements

def lighting(): 
    # setup lighting
    lights=[]
    # light = pv.Light((-2, 2, 0), (0, 0, 0), 'white'); lights.append(light)
    light = pv.Light((1, 1, 1), (0, 0, 0), 'white'); lights.append(light)
    light = pv.Light((-1, -1, -1), (0, 0, 0), 'white'); lights.append(light)
    light = pv.Light((1, 0, 0), (0, 0, 0), 'white'); lights.append(light)
    light = pv.Light((-1, 0, 0), (0, 0, 0), 'gray'); lights.append(light)
    # light2 = pv.Light((2, 0, 0), (0, 0, 0), (0.7, 0.0862, 0.0549))
    # light3 = pv.Light((0, 0, 10), (0, 0, 0), 'white'); lights.append(light)

    return lights 

def createCamera(): 
    return pv.Camera()

def generatePointCloud(ids, npns): 
    points =[]; tlabels=[]
    for npn in npns: 
        for id in ids: 
            if npn[id][0] != 0: 
                points.append(npn[id][1:4])
                tlabels.append(str(int(npn[id][0])))
    poly_points=pv.PolyData(np.array(points))
    poly_points["label"] = [f'{tlabels[i]}' for i in range(poly_points.n_points)]
    
    return  poly_points

def generateMesh_searched(ids, indexes, elements, nodes): 
    
    cells =[]
    indexes = np.array(indexes)
    elements = np.array(elements) 
    cnt = 0 
    for id in ids: 
        ix = np.where(indexes[:,0] == id)[0]
        if len(ix) > 0: 
            for x in ix: 
                cells.append(elements[indexes[x][1]])
                cnt += 1 
    if cnt > 0: 
        grid, _ = makePyvisterCells(np.array(cells).ravel(), nodes, 9)
        return  grid 
    else: 
        return None 
# def getCameraAngle(camera): 


def main(): 
    fname = 'AH32.trd'
    print("\n Reading mesh : %s"%(fname))
    trd, pt1 = load_pyVista_mesh(fname, points=True) 
    fname = 'AH32.axi'
    print("\n Reading mesh : %s"%(fname))
    axi = load_pyVista_mesh(fname) 

    # plot the grid (and suppress the camera position output)
    
    # _ = grid.plot(show_edges=True)
    pl = pv.Plotter()
    actor1 = pl.add_mesh(trd,  color='tan', label='trd', opacity=1.0, show_edges=True, line_width=0.1) ## style='wireframe',
    # pt1 = pl.add_points(pt1, point_size=1, render_points_as_spheres=True)
    actor2 = pl.add_mesh(axi,  color='gray',   label='axi', opacity=0.8) ## style='wireframe',

    # actor1 = pl.add_mesh(trd, color='tan', style='surface', scalars=None, clim=None, show_edges=True, edge_color='gray', point_size=1.0, line_width=0.1,\
    #     opacity=1.0, lighting=False, label='trd', metallic=1)
        ## style : default 'surface', 'wireframe', 'point'
    
    # pl.add_mesh_clip_plane(trd)  # , normal='x')
    # pl.add_mesh_slice(trd)
    
    # Single slice - origin defaults to the center of the mesh
    # single_slice = trd.slice(normal=[1, 1, 0])
    # pl.add_mesh(single_slice, show_edges=True)

    ## colors=['black', 'blue', 'yellow', 'grey', 'red']

    pl.set_background('white', top='black')
    pl.show()

    ## show in PyQt 
    from pyvistaqt import QtInteractor, MainWindow

    
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import  Qt  ## Qt.black, Qt.white.. 
    from PyQt5.QtGui import QPalette, QColor


    self.frame =QtWidgets.QFrame() 
    


if __name__ == "__main__": 
    main()