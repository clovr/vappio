def isSFF(path):
    return '.sff' == open(path).read(4)

def isFastq(path):
    return '@' == open(path).read(1024).strip()[0]

def isFasta(path):
    return '>' == open(path).read(1024)[0]

def isGenbank(path):
    return 'LOCUS' == open(path).read(5)
