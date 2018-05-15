def cont_iff(iff, i):
    import linecache, re
    delimenter = r'[,\s]\s*'
    line       = linecache.getline(iff, i+1)
    line_strip = line.rstrip('\n').rstrip(' ').lstrip(' ')
    line_split  = re.split(delimenter, line_strip)
    return line_split

class IFF:
    def __init__(self, iff_file):
        self.path = iff_file
        import re, linecache
        delimenter = r'[,\s]\s*'

        #Determine max line iff
        f = open(self.path, 'r')
        for i, l in enumerate(f):
            pass
        f.close()
        line_max = i+1

        #get number of fields and fieldnames
        self.num_fields = int(cont_iff(self.path,0)[0])

        self.fields = []
        for i in range(1, self.num_fields):
            self.fields.append(cont_iff(self.path,i))

        #get number of particles, particle numbers and corresponding lines
        self.particles = []
        begin_l = []
        end_l   = []
        for i in range(self.num_fields + 1, line_max):
            l = cont_iff(self.path, i)
            part_num = int(l[0])
            if i == self.num_fields + 1:
                begin_l.append(i)
                self.particles.append(part_num)
            else:
                if part_num not in self.particles:
                    self.particles.append(part_num)
                    begin_l.append(i)
                    end_l.append(i - 1)
        end_l.append(i)
        self.num_particles = len(self.particles)

        self.particles_line = {}
        for i, p in enumerate(self.particles):
            self.particles_line[p]= [begin_l[i], end_l[i]]

        #get endpoints and beginpoints (x, y, z, end_time)
        self.endpoints   = {}
        self.beginpoints = {}
        for p in self.particles:
            pbl = self.particles_line[p][0]
            pel = self.particles_line[p][1]
            self.beginpoints[p] = [float(cont_iff(self.path, pbl)[2]), float(cont_iff(self.path, pbl)[3]), float(cont_iff(self.path,pbl)[4]), float(cont_iff(self.path,pbl)[5]), int(cont_iff(self.path,pbl)[1])]
            self.endpoints[p]   = [float(cont_iff(self.path, pel)[2]), float(cont_iff(self.path, pel)[3]), float(cont_iff(self.path,pel)[4]), float(cont_iff(self.path,pel)[5]), int(cont_iff(self.path,pel)[1])]

    def get_path(self, part_num):
        path = []
        for i in range(self.particles_line[part_num][0], self.particles_line[part_num][1]+1):
            l    = cont_iff(self.path, i)
            x    = float(l[2])
            y    = float(l[3])
            z    = float(l[4])
            time = float(l[5])
            velo = float(l[6])
            lay  = int(l[1])
            path.append([x, y, z, time, velo, lay])
        return path

    def save_part(self, iff_file, out_part):
        iff_out = open(iff_file, 'w')

        for i in range(self.num_fields+1):
            iff_out.write(cont_iff(self.path, i)[0]+'\n')

        for p in out_part:
            pbl = self.particles_line[p][0]
            pel = self.particles_line[p][1]
            for i in range(pbl, pel+1):
                for n in cont_iff(self.path, i):
                    iff_out.write(n + '  ')
                iff_out.write('\n')

        iff_out.close()

    def save_pnt(self, path, t, part_out=[]):
        import ipf
        pnt = []
        if t == 'end':
            for k, v in self.endpoints.iteritems():
                if k in part_out or part_out == []:
                    p = v
                    p.append(k)
                    pnt.append(p)
        elif t == 'begin':
            for k, v in self.beginpoints.iteritems():
                if k in part_out or part_out == []:
                    p = v
                    p.append(k)
                    pnt.append(p)

        print(pnt)
        fld = ['x', 'y', 'z', 'end_time', 'part_n']

        ipf.write_ipf(fld, pnt, path)

    def save_shp(self, path_out, multi=True, part_out=[]):
        import shapefile
        s = shapefile.Writer(shapefile.POLYLINE)

        if part_out == []:
            part_out = self.particles

        #add fields
        s.field('xb','F',10,4)
        s.field('yb','F',10,4)
        s.field('zb','F',10,4)
        s.field('xe','F',10,4)
        s.field('ye','F',10,4)
        s.field('ze','F',10,4)
        s.field('time','F',10,4)
        if multi:
            s.field('velo','F',10,4)
        s.field('part','F',10,4)


        #add features
        for part in part_out:
            path = self.get_path(part)
            if multi:
                for i in range(len(path)-1):
                    pnt_b, pnt_e = path[i], path[i+1]
                    xb, yb, zb = pnt_b[0], pnt_b[1], pnt_b[2]
                    xe, ye, ze = pnt_e[0], pnt_e[1], pnt_e[2]
                    t, v = pnt_e[3], pnt_e[4]
                    s.line([[[xb, yb], [xe, ye]]])
                    s.record(xb, yb, zb, xe, ye, ze, t, v, part)
            else:
                line = []
                for pnt in path:
                    line.append([pnt[0], pnt[1]])
                s.line([line])
                xb, yb, zb = path[0][0], path[0][1], path[0][2]
                xe, ye, ze = path[-1][0], path[-1][1], path[-1][2]
                t = path[-1][3]
                s.record(xb, yb, zb, xe, ye, ze, t, part)
        s.save(path_out)