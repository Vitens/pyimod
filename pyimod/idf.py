#-------------------------------------------------------------------------------
# Name:         iMOD-interpreter
# Version:      1.1
# Purpose:      read/write IDF- en IFF-files
# Author:       Sjoerd Rijpkema, Vitens
# Created:      19-09-2014
#-------------------------------------------------------------------------------

class idf:
    # Cond.               Record  Format(bytes)     Variable                                                                  Description
    #                          1      Integer 4         1271                                                    Lahey RecordLength Ident.
    #                          2      Integer 4         Ncol                                                            Number of columns
    #                          3      Integer 4         Nrow                                                               Number of rows
    #                          4        Float 4         Xmin                                                      X lower-left-coordinate
    #                          5        Float 4         Xmax                                                     X upper-right-coordinate
    #                          6        Float 4         Ymin                                                      Y lower-left-coordinate
    #                          7        Float 4         Ymax                                                     Y upper-right-coordinate
    #                          8        Float 4         Dmin                                                           Minimal data value
    #                          9        Float 4         Dmax                                                           Maximal data value
    #                         10        Float 4       NoData                                                                 NoData value
    #                         11      Integer 1          IEQ                                     0: equidistant IDF 1: nonequidistant IDF
    #                                 Integer 1          ITB             0: no usage of Top and Bot Values 1: usage of Top and Bot Values
    #                                 Integer 1          IVF                               0: no usage of vectors 1: vectors to be stored
    #                                 Integer 1     Not used
    #IEQ=0                    12        Float 4           Dx                                    Column width, minimum width in case IEQ=1
    #IEQ=0                    13        Float 4           Dy                                     Row height, minimum height in case IEQ=1
    #ITB=1       12+abs(IEQ-1)*2        Float 4          Top                                                           Top value if ITB=1
    #ITB=1       13+abs(IEQ-1)*2        Float 4          Bot                                                           Bot value if ITB=1
    #IEQ=1              12+ITB*2        Float 4      Dx(Ncol)                     Column width for each column, ranging from west to east
    #IEQ=1         13+ITB*2+Ncol        Float 4      Dy(Nrow)                        Row height for each row, ranging from north to south
    #                       iRec        Float 4  X(Ncol,Nrow)  Value for each cell  (iRec=10 + abs(IEQ-1)*2 + IEQ*(Nrow+Ncol) + ITB*2 + 1)
    #         iRec + (Nrow*Ncol)      Integer 1         IAdit      Binary number to store optional arguments: IP1=1: Comments added IP?=?:
    #IP1=1   iRec +(Nrow*Ncol)+1      Integer 1         Nline                                        Number of lines that contain comments
    #IP1=1                              Char. 4   Comm(Nline)                                                           Comment for Nlines

    def __init__(self, idf_file):
        import struct

        self.path = idf_file
        with open(idf_file, mode='rb') as file:
            self.idf_cont = file.read()

        idf_header  = struct.unpack("iiifffffffbbbbff", self.idf_cont[: 52])

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
        import numpy, struct
        idf_array = [ [ 0 for i in range(0, self.ncol) ] for j in range(0, self.nrow) ]
        for i in range(0, self.nrow):
            for j in range(0, self.ncol):
                idf_array[i][j] = struct.unpack("f", self.idf_cont[self.irec+((self.ncol*(i))+j)*4: self.irec+(self.ncol*(i)+j+1)*4])[0]

        self.np_array = numpy.asarray(idf_array, dtype=numpy.float32)

        return None

    def xy2cr(self, x, y):
        x = float(x)
        y = float(y)
        if (x < self.xmin) or (x > self.xmax) or (y < self.ymin) or (y > self.ymax):
            print "Coordinates outside idf domain", self.xmin, self.xmax, self.ymin, self.ymax, x, y
            raise error

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

        return col, row

    def get_value(self, x, y, cor_type="cor"):
        import struct
        if cor_type == "cor":
            col, row = self.xy2cr(x, y)
        elif cor_type == "col_row":
            if (x < 0) or (x > self.ncol) or (y < 0) or (y > self.nrow):
                print "Coordinates outside idf domain"
                raise error
            col = x
            row = y
        else:
            print "Wrong argument"
            raise error

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
    import struct
    import numpy

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
