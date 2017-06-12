

def arr_to_str(arr, width=4):
    return '[' + ','.join('{0: >{1}}'.format(str(a), width) for a in arr) + ']'


def bytes_to_str(data):
    return ''.join(list(map(chr, data)))
