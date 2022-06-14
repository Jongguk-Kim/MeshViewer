try: 
    import pyvista as pv
except: 
    import os 
    os.system("pip install pyvista")
    
from pydoc import tempfilepager
from time import perf_counter
import vtk 
import numpy as np 

import smart_results as Smart 

import time 
def timer(func): 
    def wrapper(*args, **kwargs): 
        start = time.time()
        rv = func(*args, **kwargs)
        total = time.time() - start
        print ("### Time : %.2f"%(total))
        return rv 
    return wrapper




def reading_stl(fname): 
    reader = pv.get_reader(fname) 
    mesh = reader.read()
    return mesh 

class pyTire_Mesh: 
    def __init__(self): 
        pass 

    def generateMesh(self, meshfiles): 
        if len(meshfiles) ==1: 
            meshfile = meshfiles[0]
        else: 
            meshfile = meshfiles 
        self.readMesh(meshfile)
        if '.ptn' in meshfiles[0].lower(): self.centering()
        # self.pyVistaMeshIndexing() 
        self.makePyVistaGrid()
        self.makePyVistaSurface()
        self.makePyVistaEdge()

    def centering(self): 
        mid1 = np.average(self.nodes[:,1]) 
        mid3 = np.average(self.nodes[:,3])
        if mid1 > mid3: 
            self.nodes[:,1] -= mid1 
        else: 
            self.nodes[:,3] -= mid3

    def makePyVistaGrid(self): 
        self.nodes = self.convertIndexNodes(self.nodes)
        self.cells = self.elements.ravel()
        self.grid, self.xyz = makePyvisterCells(self.cells, self.nodes, self.meshtype)
        self.pt_cloud = pv.PolyData(self.xyz)

    def makePyVistaSurface(self): 
        self.surfaces = self.grid.extract_surface()

    def makePyVistaEdge(self,angle=45): 
        self.edges = self.grid.extract_feature_edges(feature_angle=angle, boundary_edges=False)

    def convertIndexNodes(self, nodes=None, value=False): 
        idmax = int(np.max(nodes[:,0]))
        if value: 
            npn = np.zeros(shape=(idmax+1, 5))
            for n in nodes: 
                npn[int(n[0])][0]=n[0]
                npn[int(n[0])][1]=n[1]
                npn[int(n[0])][2]=n[2]
                npn[int(n[0])][3]=n[3]
                npn[int(n[0])][4]=n[value]
        else: 
            npn = np.zeros(shape=(idmax+1, 4))
            for n in nodes: 
                npn[int(n[0])][0]=n[0]
                npn[int(n[0])][1]=n[1]
                npn[int(n[0])][2]=n[2]
                npn[int(n[0])][3]=n[3]
        return npn 

    def readMesh(self, meshfile): 
        
        if isinstance(meshfile, str): 
            self.meshfile = meshfile 
            nodes, elements, index, self.meshtype, self.elsets = readInp(meshfile)

        elif isinstance(meshfile, list):
            nodes=[]; elements=[]; index=[]; self.meshtype=0; self.elsets=[]
            self.meshfile=""
            for fname in meshfile: 
                node, element, ind, self.meshtype, elsets = readInp(fname)
                nodes += node 
                elements += element 
                index += ind 
                self.elsets += elsets 
                self.meshfile += fname +" & "
        else: 
            return 

        self.nodes = np.array(nodes)
        self.elements = np.array(elements)
        self.index = np.array(index)

    def inputMesh(self, nodes, elements, index=False, meshtype=9): 
        self.nodes=nodes 
        self.elements = elements 
        if index : 
            self.index = index 
        else: 
            self.pyVistaMeshIndexing(meshtype=meshtype)

    def pyVistaMeshIndexing(self, meshtype=0): 
        idx = range(len(self.elements))
        self.index = list(zip(self.elements[:,0], idx))
        self.elements[:,0] = meshtype - 1


class pyMesh_sfric(pyTire_Mesh): 
    def __init__(self):
        super().__init__() 
    
    def readsfric(self, fname) :
        self.meshfile = fname
        self.sfric = Smart.SFRIC()
        Smart.ResultSfric(fname[:-3], fname, self.sfric, deformed=1)
        self.meshtype = 5 
        self.nodes = np.array(self.sfric.Node.Node[:, :4]) 
        self.elements = np.array(self.sfric.Surface.Surface) 
        self.pyVistaMeshIndexing(meshtype = self.meshtype)
        self.makePyVistaGrid()
        self.makePressureCells()
        self.makePressureSurface()

    def makePressureSurface(self): 
        self.press = None 
        self.press_grid, self.press_xyz = makePyvisterCells(self.press_cells, self.press3Dnodes, self.meshtype)
        self.press_ptcloud = pv.PolyData(self.press_nodes[:, 1:4])
        self.press_ptcloud["press"] = self.press_nodes[:, 4]
        self.press_surface = self.press_grid.extract_surface()
        self.press = self.press_surface.interpolate(self.press_ptcloud, radius=0.001)
        print(" Interpolating Contact Pressure")
    def makePressureCells(self): 
        pnodes=[]
        for sf in self.sfric.pSurface.Surface: 
            pnodes.append(sf[5][0])
            pnodes.append(sf[5][1])
            pnodes.append(sf[5][2])
            if sf[5][3][0] > 0:
                pnodes.append(sf[5][3])
        i =0 
        while i < len(pnodes): 
            j = i+1 
            while j < len(pnodes): 
                if pnodes[i][0] == pnodes[j][0]: 
                    del(pnodes[j])
                    continue 
                j += 1 
            i += 1 
        pnodes = np.array(pnodes)
        self.pHeight = 0.03 
        nmin = np.min(pnodes[:,3])
        pmax = np.max(pnodes[:,4])
        for i, pn in enumerate(pnodes): 
            pnodes[i][3] = nmin -  self.pHeight / pmax * pn[4]
        
        self.press_cells =[]
        self.press_index=[]
        for i, sf in enumerate(self.sfric.pSurface.Surface): 
            self.press_cells.append([4, sf[1], sf[2], sf[3], sf[4]])
            self.press_index.append([sf[0], i])

        self.press_nodes = np.array(pnodes) # self.convertIndexNodes(pnodes, value=4)
        self.press_cells = np.array(self.press_cells)
        self.press_index = np.array(self.press_index) 
        self.press3Dnodes = np.array(self.nodes)
        for pn in pnodes: 
            self.press3Dnodes[int(pn[0])][1]= pn[1]
            self.press3Dnodes[int(pn[0])][2]= pn[2]
            self.press3Dnodes[int(pn[0])][3]= pn[3]

class pyMesh_sdb(pyTire_Mesh): 
    def __init__(self):
        super().__init__() 

    def readsdb(self, fname) :
        self.meshfile = fname
        self.nodes, self.membrane, self.elements, self.eld, self.sed = Smart.getSDBModel(fname)
        self.meshtype = 9 
        self.pyVistaMeshIndexing(meshtype = self.meshtype)
        self.genTemperature()
        self.makePyVistaGrid()
        self.addValues()
        self.makePyVistaSurface()
        self.makePyVistaEdge()

    def genTemperature(self): 
        idmax = int(np.max(self.nodes[:,0]))
        npn = np.zeros(shape=(idmax+1, 4))
        self.Temperature = np.zeros(shape=(idmax+1, 1))
        for n in self.nodes: 
            npn[int(n[0])][0]=n[0]
            npn[int(n[0])][1]=n[1]
            npn[int(n[0])][2]=n[2]
            npn[int(n[0])][3]=n[3]
            self.Temperature[int(n[0])][0] =n[4]
        self.nodes = npn 

    def addValues(self): 
        self.grid["sed"] = self.sed[:,1]
        self.grid["eld"] = self.eld[:,1]

        ts =[]
        for e in self.elements: 
            if e[7] == e[8]: 
                t = (self.Temperature[e[1]]+self.Temperature[e[2]]+self.Temperature[e[3]]+
                     self.Temperature[e[5]]+self.Temperature[e[6]]+self.Temperature[e[7]]) / 6.0 
            else: 
                t = (self.Temperature[e[1]]+self.Temperature[e[2]]+self.Temperature[e[3]]+self.Temperature[e[4]]+
                     self.Temperature[e[5]]+self.Temperature[e[6]]+self.Temperature[e[7]]+self.Temperature[e[8]]) / 8.0 
            ts.append(t)
        self.grid["temperature"] = np.array(ts)

class pyMesh_stl(pyTire_Mesh): 
    def __init__(self):
        super().__init__()
        self.edges = None 
        self.surfaces = None 
        self.nodes=[]
    
    def readstl(self, fname): 
        self.meshfile=fname 
        self.grid = reading_stl(fname) 

class pyMesh_layout(pyTire_Mesh): 
    def __init__(self):
        super().__init__() 
        self.surfaces = None 

    def readLayoutMesh(self, fname): 
        self.meshfile = fname 
        nodes, elements, index, self.meshtype, self.elsets = readInp(fname)
        self.nodes = np.array(nodes)
        self.elements = np.array(elements)
        self.index = np.array(index)
        self.makePyVistaGrid()
        self.makePyVistaSurface()
        self.makePyVistaEdge()
        

class pyMesh_footprint(pyTire_Mesh): 
    def __init__(self):
        super().__init__() 
    
    def readpostFootprint(self, fname): 
        self.meshfile = fname 
        nodes, elements, self.index, self.meshtype = read_SMART_postFootshape(fname, height=0.03)
        self.elements = np.array(elements)
        self.nodes = self.convertIndexNodes(nodes)

        self.press = None 
        self.press_grid, self.press_xyz = makePyvisterCells(self.elements, self.nodes, self.meshtype)
        self.press_ptcloud = pv.PolyData(self.nodes[:, 1:4])
        self.press_ptcloud["press"] = self.nodes[:, 4]
        self.press_surface = self.press_grid.extract_surface()
        self.press = self.press_surface.interpolate(self.press_ptcloud, radius=0.001)

        self.grid=self.press_grid
        self.xyz=self.press_xyz 
        self.pt_cloud = self.press_ptcloud


class MESH(): 
    def __init__(self, meshfile, centering=False, inplines=False) : 
        self.meshfile = meshfile 
        self.elsets=[]
        if '.sfric' in meshfile: 
            self.grid, self.edges, self.pt_cloud, self.surfaces, self.nodes, self.idx_element, self.cells,\
                 self.npress, self.surfpress, self.class_sfric  = \
                load_pyVista_mesh(meshfile, centering=centering)
            self.press = None 
            print(" Interpolating Contact Pressure")
            self.press = self.surfpress.interpolate(self.npress, radius=0.002)
            
        elif '.sdb' in meshfile: 
            self.grid, self.edges, self.pt_cloud, self.surfaces, \
                self.nodes, self.idx_element, self.cells, \
                eld, sed, self.temperature  = \
                load_pyVista_mesh(meshfile, centering=centering)
            self.grid["sed"] = sed[:,1]
            self.grid["eld"] = eld[:,1]
        elif '.dat' in meshfile: ## grid, edges, pt_cloud, surfaces, nodes, idx_element
            self.grid, self.edges, self.pt_cloud, self.surfaces, self.nodes, self.idx_element, self.cells,\
                 self.npress, self.surfpress  = load_pyVista_mesh(meshfile, centering=centering)
            self.press = None 
            print(" Interpolating Contact Pressure")
            self.press = self.surfaces.interpolate(self.npress, radius=0.002)
        else: 
            self.grid, self.edges, self.pt_cloud, self.surfaces, self.nodes, self.idx_element, self.cells, self.elsets  = \
                    load_pyVista_mesh(meshfile, centering=centering, inplines=inplines)

def read_SMART_postFootshape(fname, height = 0.03): 
    with open(fname) as F: 
        lines = F.readlines()
    
    nodes =[]
    el =[]
    index_elements=[]
    mtype =  5
    cmd = False 
    for line in lines: 
        if "**" in line: continue 

        if '*' in line: 
            if "*NODE" in line:    cmd = 'n'
            if "*ELEMENT" in line: cmd = 'e'
            if '*OFFSET' in line:  cmd ='offset'
        else: 
            if cmd =='n': 
                wds = line.split(",")
                nodes.append([float(wds[0].strip()), float(wds[1].strip()), float(wds[2].strip()), float(wds[3].strip()), float(wds[4].strip())])
            if cmd =='e': 
                wds = line.split(",")
                el.append([4, int(wds[1].strip()), int(wds[2].strip()), int(wds[3].strip()), int(wds[4].strip())])
                index_elements.append([int(wds[0].strip()), len(el)]) 

    nodes = np.array(nodes) 
    pmax = np.max(nodes[:,4])
    nmin = np.min(nodes[:,3]) 
    nodes[:,3] = nmin - height / pmax * nodes[:,4]

    return nodes, el, index_elements, mtype


def parsingInp(lines, offset=0, first=True): 
    cmd = False 
    no_changeXZ = True 
    nodes =[]
    s8=[]
    index_elements=[]
    mtype = 9 
    scaling = 1.0 
    countingPart = 0 
    partOffset = 0 
    partOffsetNode = 0 
    isPart = False 
    elsets=[]
    for line in lines: 
        if "**" in line: 
            if "END OF MATERIAL INFO" in line: 
                no_changeXZ = False 
            continue 
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
            elif '*ELSET' in line.upper(): 
                if 'GENERATE' in line.upper():   cmd='esetgen'
                else:                            cmd='eset'
                wds = line.upper().split(",")
                for wd in wds: 
                    if 'ELSET' in wd and '=' in wd: 
                        w = wd.split("=")[1].strip()
                        elsets.append([w])
                        break 
            elif '*PROFILE_SCALING' in line.upper(): 
                wd = line.split(":")[1].strip() 
                scaling = float(wd)

            else: 
                cmd = False 
            if first : 
                if '*PART' in line.upper(): 
                    isPart = True 
            else: 
                if '*END PART' in line.upper() : 
                    countingPart += 1
                    partOffsetNode = offset * countingPart
                    partOffset = int(offset * countingPart)
            
        else: 
            wds = line.split(",")
            
            if cmd == 'n': 
                if len(wds) > 3:  
                    if no_changeXZ: 
                        nodes.append([ float(wds[0].strip()) + partOffsetNode , float(wds[1].strip()), float(wds[2].strip()), float(wds[3].strip())  ])
                        
                    else: 
                        nodes.append([ float(wds[0].strip()) + partOffsetNode, float(wds[3].strip()), float(wds[2].strip()), float(wds[1].strip())  ])
            if cmd == 'n8':
                s8.append([8, 
                            int(wds[1].strip()) + partOffset, int(wds[2].strip()) + partOffset, int(wds[3].strip()) + partOffset, int(wds[4].strip()) + partOffset, 
                            int(wds[5].strip()) + partOffset, int(wds[6].strip()) + partOffset, int(wds[7].strip()) + partOffset, int(wds[8].strip()) + partOffset
                            ])
                index_elements.append([int(wds[0].strip()) + partOffset, len(s8)-1]) 
            if cmd == 'n6':
                s8.append([8, 
                            int(wds[1].strip()) + partOffset, int(wds[2].strip()) + partOffset, int(wds[3].strip()) + partOffset, int(wds[3].strip()) + partOffset, 
                            int(wds[4].strip()) + partOffset, int(wds[5].strip()) + partOffset, int(wds[6].strip()) + partOffset, int(wds[6].strip()) + partOffset
                            ]) 
                index_elements.append([int(wds[0].strip()) + partOffset, len(s8)-1]) 
            
            if cmd == 'n3':
                s8.append([4, 
                            int(wds[1].strip()) + partOffset, int(wds[2].strip()) + partOffset, int(wds[3].strip()) + partOffset, int(wds[3].strip()) + partOffset
                          ]) 
                index_elements.append([int(wds[0].strip()) + partOffset, len(s8)-1]) 
            if cmd == 'n4':
                s8.append([4, 
                            int(wds[1].strip()) + partOffset, int(wds[2].strip()) + partOffset, int(wds[3].strip()) + partOffset, int(wds[4].strip()) + partOffset
                          ]) 
                index_elements.append([int(wds[0].strip()) + partOffset, len(s8)-1]) 
            if cmd == 'eset': 
                try: 
                    for wd in wds: 
                        if wd.strip() !='': 
                            elsets[-1].append(int(wd.strip()) + partOffset)
                except: 
                    del(elsets[-1])
                    cmd = False 
                # print(elsets[-1])
            if cmd == 'esetgen': 
                try: 
                    st = int(wds[0].strip())
                    ed = int(wds[1].strip())
                    sp = int(wds[2].strip())
                    for e in range(st, ed+sp, sp): 
                        elsets[-1].append(e + partOffset) 
                except: 
                    del(elsets[-1])
                    cmd = False 
    
    if scaling != 1.0: 
        nodes = np.array(nodes)
        nodes[:,1] *= scaling; nodes[:,2] *= scaling; nodes[:,3] *= scaling 

    return nodes, s8, index_elements, mtype, isPart, elsets

def readInp(fname, inplines=False): 
    if not inplines: 
        with open(fname) as F: 
            lines = F.readlines()
    else: 
        lines = inplines 
    nodes, s8, index_elements, mtype, isPart, elsets = parsingInp(lines, first=True, offset=0)
    if isPart : 
        nd = np.array(nodes)
        maxND = np.max(nd[:,0]) + 1
        elix = np.array(index_elements)
        maxEL = np.max(elix[:,0]) + 1
        if maxND > maxEL: 
            offset = maxND 
        else: 
            offset = maxEL 
        print(" Part Offset : %d"%(offset))
        nodes, s8, index_elements, mtype, _, elsets = parsingInp(lines, first=False, offset=offset)
        # print("**********************")
        print(" ELSETS : %d"%(len(elsets)))

        # for est in elsets: 
        #     if len(est) > 1: 
        #         print(len(est), ":", est[0], est[1], "...", est[-1])
        # print("**********************")

    return nodes, s8, index_elements, mtype, elsets
    
@timer 
def readMesh_pyVista(fname,  files=None, centering=False, sdb=False, inplines=False): 
    elsets = []
    if sdb: 
        import time 
        # t = time.time()
        nodes, membrane, solid, eld, sed = Smart.getSDBModel(fname)
        # t1 = time.time(); print(" SDB Reading %.3f"%(t1-t))
        meshtype = 9 
        idx_element=solid[:,0] 
        cnt = np.arange(len(solid))
        idx_element = np.column_stack((idx_element, cnt))

        s8=solid 
        s8[:,0] = 8
    
    else: 
        if '.dat' in fname: 
            nodes, s8, idx_element, meshtype = read_SMART_postFootshape(fname)
        else: 
            if not inplines: 
                nodes, s8, idx_element, meshtype, elsets = readInp(fname)
            else: 
                nodes, s8, idx_element, meshtype, elsets = readInp(fname, inplines=inplines)
                
            nodes = np.array(nodes)
        s8 = np.array(s8)
        # print(" FILE READING", fname)
        if not isinstance(files, type(None)): 
            for file in files: 
                # print("* FILE READING", file)
                nds, sd, idx_element, meshtype, elsets = readInp(file) 
                nodes = np.concatenate((nodes, np.array(nds)), axis=0)
                s8 = np.concatenate((s8, np.array(sd)), axis=0)
    
    idmax = int(np.max(nodes[:,0]))
    if centering: 
        md = np.average(nodes[:,1]) 
        nodes[:,1] -= md 
        # print (" shift %.6f"%(md))

    npn = np.zeros(shape=(idmax+1, 4))
    if '.sdb' in fname:
        tn = np.zeros(shape=(idmax+1, 1))
        for n in nodes: 
            npn[int(n[0])][0]=n[0]
            npn[int(n[0])][1]=n[1]
            npn[int(n[0])][2]=n[2]
            npn[int(n[0])][3]=n[3]
            tn[int(n[0])][0] =n[4]
    else: 
        for n in nodes: 
            npn[int(n[0])][0]=n[0]
            npn[int(n[0])][1]=n[1]
            npn[int(n[0])][2]=n[2]
            npn[int(n[0])][3]=n[3]

    print (" Number of nodes : %d"%(len(nodes)))
    print (" Number of elements : %d"%(len(s8)))
    print (" Element Type : %d"%(meshtype-1))
    print (" Max Node ID=%d"%(idmax))

    if sdb: 
        return npn, np.array(s8).ravel(), idx_element, np.array(s8), meshtype, eld, sed, tn
    elif '.dat' in fname: 
        return npn, np.array(s8).ravel(), idx_element, np.array(s8), meshtype, nodes
    else: 
        return npn, np.array(s8).ravel(), idx_element, np.array(s8), meshtype, elsets


def makePyvisterCells(cells, nodes, meshtype): 
    
    if meshtype != 5: 
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
    else: 
        
        xyz = nodes[:, 1:4]
        grid = pv.PolyData(xyz, cells)
    return grid, xyz  

def load_pyVista_mesh(file_name, centering=False, inplines=False): 
    elsets=[]
    if ".sfric" in file_name: 
        nodes, cells, idx_element, elements, meshtype, pnodes, pcells, class_sfric, pressNode = readSfric_pyVista(file_name)
    elif '.sdb' in file_name: 
        nodes, cells, idx_element, elements, meshtype, eld, sed, temperature = readMesh_pyVista(file_name, sdb=True)
    elif '.dat' in file_name: 
        nodes, cells, idx_element, elements, meshtype, n_pres = readMesh_pyVista(file_name, centering=False)

    else: 
        nodes, cells, idx_element, elements, meshtype, elsets = readMesh_pyVista(file_name, centering=centering, inplines=inplines)
    
    grid, xyz = makePyvisterCells(cells, nodes, meshtype)
    pt_cloud = pv.PolyData(xyz)
    if meshtype ==9 : 
        print(" Edges, surfaces are creating")
        edges = grid.extract_feature_edges(feature_angle=45, boundary_edges=False)
        surfaces = grid.extract_surface()
        # print(" Mesh Volume", grid.volume)
    elif meshtype ==5: 
        edges = grid.extract_all_edges()
        surfaces = grid.extract_surface()
        if ".sfric" in file_name: 
            pgrid, pxyz = makePyvisterCells(pcells, pressNode, meshtype)
            pn_cloud = pv.PolyData(pnodes[:, 1:4])
            pn_cloud["press"] = pnodes[:, 4]
            psurf = pgrid.extract_surface()

            return grid, edges, pt_cloud, surfaces, nodes, idx_element, elements, pn_cloud, psurf, class_sfric
        if '.dat' in file_name: 
            pgrid, pxyz = makePyvisterCells(cells, nodes, meshtype)
            pn_cloud = pv.PolyData(n_pres[:, 1:4])
            pn_cloud["press"] = n_pres[:, 4]
            psurf = pgrid.extract_surface()
            
            return grid, edges, pt_cloud, surfaces, nodes, idx_element, elements, pn_cloud, psurf

    else: 
        edges = grid.extract_all_edges()
        surfaces = None 
    if '.sdb' in file_name:
        tSolid = []
        for e in elements: 
            if e[7] == e[8]: 
                t = (temperature[e[1]]+temperature[e[2]]+temperature[e[3]]+
                     temperature[e[5]]+temperature[e[6]]+temperature[e[7]]) / 6.0 
            else: 
                t = (temperature[e[1]]+temperature[e[2]]+temperature[e[3]]+temperature[e[4]]+
                     temperature[e[5]]+temperature[e[6]]+temperature[e[7]]+temperature[e[8]]) / 8.0 
            tSolid.append(t)
        grid["temperature"] = np.array(tSolid)
        print (" temperature is added. ")
        return grid, edges, pt_cloud, surfaces, nodes, idx_element, elements, eld, sed, temperature
    else: 
        return grid, edges, pt_cloud, surfaces, nodes, idx_element, elements, elsets

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
def addlight(light_type='headlight'): 
    light = pv.Light(light_type=light_type)
    return light 

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

def generateMesh_searched(ids, indexes, elements, nodes, ctype=9): 
    
    cells =[]
    indexes = np.array(indexes)
    elements = np.array(elements) 
    cnt = 0 
    for id in ids: 
        ix = np.where(indexes[:,0] == id)[0]
        if len(ix) > 0: 
            for x in ix: 
                try: 
                    cells.append(elements[indexes[x][1]])
                    cnt += 1 
                except: 
                    continue 
    if cnt > 0: 
        grid, _ = makePyvisterCells(np.array(cells).ravel(), nodes, ctype)
        edges = grid.extract_feature_edges(feature_angle=45, boundary_edges=False)
        surfaces = grid.extract_surface()
        return  grid, edges, surfaces
    else: 
        return None, None, None

def generateMesh_index(idx, elements, nodes, ctype=9): 
    cells =[]
    for ix in idx: 
        cells.append(elements[ix])
    grid, _ = makePyvisterCells(np.array(cells).ravel(), nodes, ctype)
    edges = grid.extract_feature_edges(feature_angle=45, boundary_edges=False)
    surfaces = grid.extract_surface()
    return  grid, edges, surfaces

def readSfric_pyVista(file_name): 

    smart = Smart.SFRIC()
    Smart.ResultSfric(file_name[:-3], file_name, smart, deformed=1)


    cells=[]
    index_elements =[]
    cnt = 0 
    for surf in smart.Surface.Surface: 
        cells.append([4, surf[1], surf[2], surf[3], surf[4]])
        index_elements.append([surf[0], cnt])
        cnt +=1 

    idmax = int(np.max(smart.Node.Node[:,0]))
    npn = np.zeros(shape=(idmax+1, 4))
    for n in smart.Node.Node: 
        npn[int(n[0])][0]=n[0]
        npn[int(n[0])][1]=n[1]
        npn[int(n[0])][2]=n[2]
        npn[int(n[0])][3]=n[3]


    meshtype = 5


    p_cells=[]
    p_index_elements =[]
    cnt = 0 
    for surf in smart.pSurface.Surface: 
        p_cells.append([4, surf[1], surf[2], surf[3], surf[4]])
        p_index_elements.append([surf[0], cnt])
        cnt +=1 

    # idmax = int(np.max(smart.pNode.Node[:,0]))
    # p_npn = np.zeros(shape=(idmax+1, 4))
    # for n in smart.pNode.Node: 
    #     p_npn[int(n[0])][0]=n[0]
    #     p_npn[int(n[0])][1]=n[1]
    #     p_npn[int(n[0])][2]=n[2]
    #     p_npn[int(n[0])][3]=n[3]

    pnodes = np.array(npn) 
    height = 0.03
    nmin = np.min(pnodes[:,3])
    pmax = np.max(smart.pNode.Node[:,4]) 
    for i, p in enumerate(smart.pNode.Node): 
        pnodes[int(p[0])][3] = nmin - height / pmax * p[4]
        smart.pNode.Node[i][3] = pnodes[int(p[0])][3]


    return npn, np.array(cells).ravel(), index_elements, cells, meshtype, smart.pNode.Node, p_cells, smart, pnodes

def get_vtkDistanceWidget(plotter): 
    widget = vtk.vtkDistanceWidget() 
    widget.SetInteractor(plotter.iren.interactor)
    return widget
def get_vtkPointHandleRepresentation3D(widget): 
    handle = vtk.vtkPointHandleRepresentation3D()
    representation = vtk.vtkDistanceRepresentation2D()
    representation.SetHandleRepresentation(handle)
    widget.SetRepresentation(representation)
    return widget, handle, representation

def get_vtkPointPicker(plotter): 
    point_picker = vtk.vtkPointPicker()
    plotter.iren.set_picker(point_picker)
    return plotter, point_picker
def addObserver_widget(widget): 
    widget.AddObserver(vtk.vtkCommand.EndInteractionEvent, place_point)
    return widget 

representation=None 
point_picker=None 

def place_point(widget, event):
    p1 = [0, 0, 0]
    p2 = [0, 0, 0]
    representation.GetPoint1DisplayPosition(p1)
    representation.GetPoint2DisplayPosition(p2)
    if point_picker.Pick(p1, p.renderer):
        pos1 = point_picker.GetPickPosition()
        representation.GetPoint1Representation().SetWorldPosition(pos1)
        representation.GetAxis().GetPoint1Coordinate().SetValue(pos1)
    if point_picker.Pick(p2, p.renderer):
        pos2 = point_picker.GetPickPosition()
        representation.GetPoint2Representation().SetWorldPosition(pos2)
        representation.GetAxis().GetPoint2Coordinate().SetValue(pos2)
    representation.BuildRepresentation()
    return

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
    # main()
    fname = 'AH32.ptn' 
    
    sfric = False 
    if sfric: 
        fname = "D:\\01_ISLM_Scripts\\10_StandardMesh\\RND-3003473VT00036-0-D101-0001.sfric008"

        sf = pyMesh_sfric()
        sf.readsfric(fname) 
        pl = pv.Plotter()
        actor1 = pl.add_mesh(sf.grid,  color='tan', label='trd', opacity=1.0, show_edges=True, line_width=0.1) 
        item = 'press'
        vmax = sf.press[item].max()*0.8; vmin = sf.press[item].min()*0.2
        vmax = 10**6; vmin=10**5
        dargs = dict(scalars=item, cmap='rainbow', show_edges=True, n_colors=150, clim=[vmin, vmax], below_color='white', edge_color='gray')
        plotter_press = pl.add_mesh(sf.press, interpolate_before_map=True, opacity=1, 
                scalar_bar_args={'title': ' %s  - interpolated'%(item)}, smooth_shading=True, **dargs)

        pl.show()

    sdb = True 
    if sdb: 
        fname = "D:\\01_ISLM_Scripts\\temporary\\ZCA000_ZSA_L040_V020_1028068VT00029-0.sdb060"

        sdb = pyMesh_sdb()
        sdb.readsdb(fname) 
        pl = pv.Plotter()
        ac = pl.add_mesh(sdb.grid)
        pl.show()