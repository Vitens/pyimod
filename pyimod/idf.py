class IDF:
    def __init__(self, idf_file):
        self.path = idf_file

        #Open binary file and read total content in memory
        with open(idf_file, mode='rb') as file:
            self.idf_cont = file.read()

        #Read the total header of the file and from that read metadata
        import struct
        idf_header  = struct.unpack("iiifffffffbbbbff", self.idf_cont[:52])
        self.ncol   = idf_header[1]
        self.nrow   = idf_header[2]
        self.xmin   = idf_header[3]
        self.xmax   = idf_header[4]
        self.ymin   = idf_header[5]
        self.ymax   = idf_header[6]
        self.dmin   = idf_header[7]
        self.dmax   = idf_header[8]
        self.nodata = idf_header[9]
        self.ieq    = idf_header[10]
        self.itb    = idf_header[11]
        self.ivf    = idf_header[12]
        self.min_dx = idf_header[14]
        self.min_dy = idf_header[15]
        self.irec   = 4*(11 + abs(self.ieq-1)*2 + self.ieq*(self.nrow+self.ncol) + self.itb*2)

        #Determine equidistant or not, depending on that read dx, dy
        if self.ieq == 1:
            self.dx = struct.unpack(self.ncol * "f", self.idf_cont[4*(11 + self.itb*2)            : 4*(11 + self.itb*2 + self.ncol)])
            self.dy = struct.unpack(self.nrow * "f", self.idf_cont[4*(11 + self.itb*2 + self.ncol): 4*(11 + self.itb*2 + self.ncol + self.nrow)])
        else:
            self.dx = self.min_dx
            self.dy = self.min_dy

    def __getattr__(self, name):
        if name == 'np_array':
            self.__get_matrix()
            return self.np_array

    def __get_matrix(self):
        import numpy
        idf_array = [ [ 0 for i in range(0, self.ncol) ] for j in range(0, self.nrow) ]
        for i in range(0, self.nrow):
            for j in range(0, self.ncol):
                idf_array[i][j] = struct.unpack("f", self.idf_cont[self.irec+((self.ncol*(i))+j)*4: self.irec+(self.ncol*(i)+j+1)*4])[0]

        self.np_array = numpy.asarray(idf_array, dtype=numpy.float32)

    def xy2cr(self, x, y):
        #function to convert x, y coordinate to row, col of idf
        x = float(x)
        y = float(y)
        if (x<self.xmin) or (x>self.xmax) or (y<self.ymin) or (y>self.ymax):
            print "Coordinates outside idf domain", self.xmin, self.xmax, self.ymin, self.ymax, x, y
            raise error
        else:
            if self.ieq:
                posx = self.xmin
                for col in range(0, len(self.dx)):
                    if posx > x:
                        break
                    posx = posx + self.dx[col]
                posy = self.ymax
                for row in range(0, len(self.dy)):
                    if posy < y:
                        break
                    posy = posy - self.dy[row]
            else:
                col = int((x-self.xmin)/self.dx)+1
                row = int((self.ymax-y)/self.dy)+1
            return row, col

    def get_value(self, x, y, row_col=False):
        #Determine the value add coordinate x, y (either in real coordinates or
        #row, col)
        if not row_col:
            row, col = self.xy2cr(x, y)
        else:
            col = x
            row = y

        value = struct.unpack("f", self.idf_cont[self.irec+(self.ncol*(row-1)+col-1)*4: self.irec+(self.ncol*(row-1)+col)*4])[0]
        return value

    def save(self, path=None):
        if path == None:
            path = self.path

        idf_write(path, self.xmin,self.ymin,self.ncol,self.nrow, self.dx, self.dy, self.nodata, self.np_array)
        return None

    def save_subset(self, xmin, ymin, xmax, ymax, path):
        colmin, rowmin = self.xy2cr(xmin, ymin)
        colmax, rowmax = self.xy2cr(xmax, ymax)

        xmin_cell = self.xmin + self.dx * (colmin)
        ymin_cell = self.ymax - self.dy * (rowmin)

        subset = self.np_array[rowmax:rowmin,colmin:colmax]

        nrow, ncol = subset.shape

        idf_write(path, xmin_cell, ymin_cell, ncol, nrow, self.dx, self.dy, self.nodata, subset, ITB=0, IVF=0, IAdit=0)

        return None

    def save_arcgis(self, path, overwrite = False):
        import arcpy

        arcpy.env.overwriteOutput = overwrite

        ras_arcgis = arcpy.NumPyArrayToRaster(self.np_array, arcpy.Point(self.xmin, self.ymin), self.dx, self.dy)
        ras_arcgis.save(path)

        return None

    def save_asc(self, path):
        asc = open(path, 'w')

        asc.write("ncols          " + str(self.ncol)   + "\n")
        asc.write("nrows          " + str(self.nrow)   + "\n")
        asc.write("xllcorner      " + str(self.xmin)   + "\n")
        asc.write("yllcorner      " + str(self.ymin)   + "\n")
        asc.write("cellsize       " + str(self.dx)     + "\n")
        asc.write("NODATA_value   " + str(self.nodata) + "\n")

        for i in xrange(self.nrow):
            for j in xrange(self.ncol):
                asc.write(str(self.np_array[i,j]) + "   ")
            asc.write('\n')

        return None

def idf_write(path, xmin, ymin, ncol, nrow, dx, dy, nodata, data, ITB=0, IVF=0, IAdit=0):
    import struct, numpy

    idf_o = open(path, mode='wb')

    if isinstance(dx, float) and isinstance(dy, float):
        IEQ = 0
        xmax = xmin + dx * ncol
        ymax = ymin + dy * nrow
    else:
        IEQ = 1
        xmax = xmin
        ymax = ymin
        for dxi in dx:
            xmax = xmax + dxi
        for dyi in dy:
            ymax = ymax + dyi



    if not isinstance(data, numpy.ndarray):
        data = numpy.asarray(data)

    dmin = numpy.min(data)
    dmax = numpy.max(data)

    #Write header
    idf_o.write(struct.pack('i',1271))
    idf_o.write(struct.pack('ii',ncol, nrow))
    idf_o.write(struct.pack('ffff', xmin, xmax, ymin, ymax))
    idf_o.write(struct.pack('fff', dmin, dmax, nodata))
    idf_o.write(struct.pack('bbbb', IEQ, ITB, IVF, 0))

    #Write column and row width
    if IEQ == 0:
        idf_o.write(struct.pack('ff', dx, dy))
    else:
        idf_o.write(struct.pack('ff', min(dx), min(dy)))
        for dxi in dx:
            idf_o.write(struct.pack('f', dxi))
        for dyi in dy:
            idf_o.write(struct.pack('f', dyi))

    #Write data
    shape = data.shape
    for i in range(shape[0]):
        for j in range(shape[1]):
            idf_o.write(struct.pack('f', data[i][j]))

    #Write comment
    idf_o.write(struct.pack('b', IAdit))

    idf_o.close()
