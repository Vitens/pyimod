class ipf:
    def __init__(self, ipf_file, f_type=[]):
        #read ipf
        self.path = ipf_file
        self.ipf_cont = []
        with open(ipf_file, 'r') as infile:
            for line in infile:
                self.ipf_cont.append(line)

        #get number of fields and features
        self.num_features  = int(self.ipf_cont[0])
        self.num_fields    = int(self.ipf_cont[1])

        #get fieldnames
        self.fields = []
        for i in range(2, 2 + self.num_fields):
            self.fields.append(self.ipf_cont[i].rstrip('\n'))

        #get txt fieldnumber
        self.txt_fieldnumber = self.ipf_cont[2 + self.num_fields].split(r',')[0]


        #get features
        import re
        delimiter = r'[,\s]\s*'
        self.features = []
        for i in range(3 + self.num_fields, len(self.ipf_cont)):
            feat = re.split(delimiter, self.ipf_cont[i].rstrip('\n').lstrip(' '))
            if f_type == []:
                self.features.append(feat)
            else:
                feat_t = []
                for i, j in enumerate(feat):
                    if f_type[i] == 'f':
                        feat_t.append(float(j))
                    elif f_type[i] == 'i':
                        feat_t.append(int(j))
                    elif f_type[i] == 's':
                        feat_t.append(str(j))
                    else:
                        print "error"
                        exit
                self.features.append(feat_t)

    def add_field(self, field_name, values):
        if len(values) <> self.num_features:
            print "Error, wrong input"
            exit

        self.fields.append(field_name)
        for i in range(len(values)):
            self.features[i].append(values[i])

    def save(self, path=None):
        if path == None:
            path = self.path

        write_ipf(self.fields, self.features, path, self.txt_fieldnumber)

    def save2shp(self, path, fld_type=None):
        import shapefile
        w = shapefile.Writer(shapefile.POINT)
        w.autoBalance = 1

        #add geometry
        for feat in self.features:
            w.point(float(feat[0]),float(feat[1]))

        #add fields
        #(Types can be: Character, Numbers, Longs, Dates, or Memo)
        decimal_l = 4
        if fld_type == None:
            fld_type = ['C' for i in range(len(self.fields))]
        for fld in range(len(self.fields)):
            if fld == 0:
                 # name, fieldType="C", size="50", decimal=0
                w.field('x', fieldType=fld_type[fld], decimal=decimal_l )
            elif fld == 1:
                w.field('y', fieldType=fld_type[fld], decimal=decimal_l )
            else:
                w.field(self.fields[fld], fieldType=fld_type[fld], decimal=decimal_l )

        #add attributes
        for feat in self.features:
            w.record(feat)

        #save shapefile
        w.save(path)

def write_ipf(fields, features, path, txt_fieldnumber = 0):
    ipf_o = open(path, 'w')

    #Write header
    number_fields = len(fields)
    number_pnts   = len(features)

    ipf_o.write(str(number_pnts))
    ipf_o.write('\n')

    ipf_o.write(str(number_fields))
    ipf_o.write('\n')

    for i in fields:
        ipf_o.write(i)
        ipf_o.write('\n')
    ipf_o.write(str(txt_fieldnumber))
    ipf_o.write(',txt\n')

    #Write pnts
    cln_width = 20
    for i in features:
        k = 0
        for j in i:
            j_line = str(j)
            ipf_o.write(j_line)
            if k <> number_fields-1:
                ipf_o.write(r', ')
            else:
                ipf_o.write('\n')
            k+=1

    ipf_o.close()