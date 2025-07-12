__author__='Andrea Bonetti'
__author_email__=''

'''
======================================================
ascii bars
======================================================

author: Andrea Bonetti
github: https://github.com/andreabonetti

inspired by:
https://alexwlchan.net/2018/05/ascii-bar-charts/

block elements:
https://en.wikipedia.org/wiki/Block_Elements

selection of useful block elements:
U+2587  ▇   Lower seven eighths block
U+2588  █   Full block
U+2591  ░   Light shade
U+2592  ▒   Medium shade
U+2593  ▓   Dark shade

'''

def _get_sign(x):
    '''
    Get sign of a number:
    -1  : negative
     0  : zero
    +1  : positive
    '''
    if (x>0):  
        sign = +1
    elif (x<0):
        sign = -1
    else:
        sign = 0
    return sign

def plot(
    data,
    sep_lc          =' | ',     # label-count separator
    unit            ='█',       # string unit for bar
    zero            ='▏',       # string for bar when equal to zero
    max_length      = 20,       # maximum bar length in plot
    neg_unit        = '',       # negated bar unit (e.g., '░')
    neg_max         = 0,        # maximum value when negated bar is used
    count_pf        = ''        # count postfix (e.g., '%')
    ):
    '''
    Plot bars
    '''
    # ======================================================
    # get useful data
    # ======================================================
    # generate enables
    neg_e = False
    neg_max_e = False
    if neg_unit != '':
        neg_e = True
    if neg_max > 0:
        neg_max_e = True
    # min/max values
    max_value = max(count for _, count in data)
    min_value = min(count for _, count in data)
    if (max_value < 0):
        max_value = 0
    if (min_value > 0):
        min_value = 0
    # max len(str(count))
    max_len_str_count=0
    for _, count in data:
        len_str_count=len(str(count))
        if (len_str_count > max_len_str_count):
            max_len_str_count = len_str_count
    # range of values
    if (neg_e and neg_max_e):
            range_of_values = neg_max
    else:
        range_of_values = max_value - min_value
    # max label length
    max_label_length = max(len(label) for label, _ in data)
    # get signs
    i=0
    vect_sign=[]
    for _, count in data:
        vect_sign.append(_get_sign(count))
    # ======================================================
    # checks
    # ======================================================
    # data cannot be negative if neg_unit or neg_max are specified
    data_is_zero_or_positive = True
    for sign in vect_sign:
        if (sign==(-1)):
            data_is_zero_or_positive = False
            break
    if ( (data_is_zero_or_positive==False) and (neg_e or neg_max_e) ):
        raise Exception("Error: sorry, data cannot be negative if neg_unit or neg_max are specified")
    # ======================================================
    # build bars (strings)
    # ======================================================
    vect_str_bar = []
    vect_str_neg = []
    max_pos_length = 0
    max_neg_length = 0
    for label, count in data:
        # get sign of count
        sign = _get_sign(count)
        # get bar length (absolute value)
        length = round(abs(count)/range_of_values*max_length)
        # get negated bar length (absolute value)
        neg_length = max_length - length
        # longest positive/negative bar
        if (sign==(+1)):
            if (length > max_pos_length):
                max_pos_length = length
        elif (sign==(-1)):
            if (length > max_neg_length):
                max_neg_length = length
        # bar
        bar     = unit * length
        neg = neg_unit * neg_length
        vect_str_bar.append(bar)
        vect_str_neg.append(neg)
    # ======================================================
    # plot bars
    # ======================================================
    i=0
    for label, count in data:
        # get sign of count
        sign = _get_sign(count)
        # print
        str_label = label.ljust(max_label_length)
        str_count = str(count).rjust(max_len_str_count)
        # str_bar
        if (sign==(+1)):
            str_spaces = " " * max_neg_length
            str_bar = str_spaces + vect_str_bar[i]
            if (neg_e):
                str_bar = str_bar + vect_str_neg[i]
        elif (sign==(-1)):
            str_bar = vect_str_bar[i].rjust(max_neg_length)
        else:
            str_spaces = " " * max_neg_length
            if (neg_e):
                str_negated = neg_unit * (max_length)
                str_bar = str_negated
            else:
                str_bar = str_spaces + zero
        # print
        print(str_label + sep_lc + str_count + count_pf + ' ' + str_bar)
        i+=1
    # ======================================================
    # print max value if max value of negated bar is enabled
    # ======================================================
    if (neg_e and neg_max_e):
        str_spaces = " " * (max_label_length+len(sep_lc)+max_len_str_count+len(count_pf)+1)
        str_max_val = (str(neg_max)+str(count_pf)).rjust(max_length)
        print(str_spaces + str_max_val)

