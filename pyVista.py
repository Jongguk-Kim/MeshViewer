import pyvista as pv
import vtk 
import numpy as np 

def readInp(fname): 

    with open(fname) as F: 
        lines = F.readlines()
    nodes =[]
    s8=[]
    cmd = False 
    offset = 0 
    for line in lines: 
        if "**" in line: continue 
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
            else: 
                cmd = False 
        else: 
            wds = line.split(",")
            if cmd == 'n': 
                nodes.append([ float(wds[0].strip()), float(wds[3].strip()), float(wds[2].strip()), float(wds[1].strip())  ])
            if cmd == 'n8':
                s8.append([8, 
                            int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[4].strip()), 
                            int(wds[5].strip()), int(wds[6].strip()), int(wds[7].strip()), int(wds[8].strip())
                            ]) 
            if cmd == 'n6':
                s8.append([8, 
                            int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[3].strip()), 
                            int(wds[4].strip()), int(wds[5].strip()), int(wds[6].strip()), int(wds[6].strip())
                            ]) 
    return nodes, s8

def readMesh_pyVista(fname,  files=None, centering=False): 
    
    nodes, s8 = readInp(fname)
    nodes = np.array(nodes)
    s8 = np.array(s8)

    if not isinstance(files, type(None)): 
        for file in files: 
            nds, sd = readInp(file) 
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
    return npn, np.array(s8).ravel()


def readSmallMesh_pyVista(fname): 
    nodes, s8 = readInp(fname)
    nodes = np.array(nodes)
    s8 = np.array(s8)

    solids=[]
    for s in s8: 
        ix1=np.where(nodes[:,0] == s[1])[0][0]
        ix2=np.where(nodes[:,0] == s[2])[0][0]
        ix3=np.where(nodes[:,0] == s[3])[0][0]
        ix4=np.where(nodes[:,0] == s[4])[0][0]
        ix5=np.where(nodes[:,0] == s[5])[0][0]
        ix6=np.where(nodes[:,0] == s[6])[0][0]
        ix7=np.where(nodes[:,0] == s[7])[0][0]
        ix8=np.where(nodes[:,0] == s[8])[0][0]
        solids.append([8, ix1, ix2, ix3, ix4, ix5, ix6, ix7, ix8]) 

    return nodes, np.array(solids).ravel()
    

def load_pyVista_mesh(file_name, points=False, centering=False): 

    nodes, cells = readMesh_pyVista(file_name, centering=centering)
    nCell = int(len(cells)/9)

    xyz = nodes[:,1:4]

    
        

    # each cell is a VTK_HEXAHEDRON
    celltypes = np.empty(nCell, dtype=np.uint16) 
    celltypes[:] = vtk.VTK_HEXAHEDRON 

    # if you are not using VTK 9.0 or newer, you must use the offset array
    # grid = pv.UnstructuredGrid(offset8, cells, celltypes, xyz) 

    #  if you are using VTK 9.0 or newer, you do not need to input the offset array:
    grid = pv.UnstructuredGrid(cells, celltypes, xyz)

    # Alternate versions:
    grid = pv.UnstructuredGrid({vtk.VTK_HEXAHEDRON: cells.reshape([-1, 9])[:, 1:]}, xyz)
    grid = pv.UnstructuredGrid({vtk.VTK_HEXAHEDRON: np.delete(cells, np.arange(0, cells.size, 9))}, xyz)

    if points: 
        pt_cloud = pv.PolyData(xyz)
        return grid, pt_cloud 
    return grid 

def lighting(): 
    # setup lighting
    light1 = pv.Light((-2, 2, 0), (0, 0, 0), 'white')
    # light2 = pv.Light((2, 0, 0), (0, 0, 0), (0.7, 0.0862, 0.0549))
    light3 = pv.Light((0, 0, 10), (0, 0, 0), 'white')
    return [light1, light3]

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