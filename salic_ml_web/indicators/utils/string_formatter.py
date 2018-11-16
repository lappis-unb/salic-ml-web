def list_to_string_tuple(elements_list):
    final_string = '('
    
    for each in elements_list:
        final_string += "'" + str(each) + "', "

    final_string = final_string[:-2]

    final_string += ')'

    return final_string

def empty_or_valid_string(value):
    if value is None:
        return ''
    else:
        return str(value)
