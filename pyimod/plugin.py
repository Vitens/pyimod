def write_out(progress=None, info=None, error=None, window=None, f=None, path=None, wait=False):
    txt = []
    if window is not None:
        txt.append('WINDOW= ' + str(window[0]) + ',' +str(window[1]) + ',' +str(window[2]) + ',' +str(window[3]))

    if f is not None:
        txt.append('NFILE= ' + str(len(f)))
        for i, j in enumerate(f):
            txt.append('FILE' + str(i+1) + '= ' + j)

    if info is not None:
        txt.append('MESSAGE_INFO= ' + info)

    if error is not None:
        txt.append('MESSAGE_ERROR= ' + error)

    if progress is not None:
        txt.append('MESSAGE_PROGRESS= ' + progress)

    if txt == []:
        raise Exception("No output given.")

    if path is None:
        path = 'PLUG-IN.OUT'

    fo = open(path, 'w')
    for i in txt:
        fo.write(i + '\n')
    fo.close()

    if wait:
        import time, os
        t_tresh = 10.0
        t0 = time.time()
        t=0
        while t < t_tresh:
            t = time.time() - t0
            if not os.path.exists(path):
                return
        raise Exception("Time-out while waiting for iMOD.")

def read_in(path=None):
    if path is None:
        path = 'PLUG-IN.IN'
    fi = open(path, 'r')
    in_file = []
    for i in fi.readlines():
        in_file.append(i.rstrip('\n'))
    fi.close()
    return in_file

if __name__ == '__main__':
    print write_out(progress="H", info="I", error="O", window=[0,1,2,3], f=[r'C:\temp\ja.idf', r'C:\temp\nee.idf'], path='test.out', wait=True)
