class Utils():

    def find(dict_list, key, expected):
        return next((item for item in dict_list if item.get(key) == expected), None)

    def lcfirst(myStr):
        return myStr[0:1].lower() + myStr[1:]

    def ucfirst(myStr):
        return myStr[0:1].upper() + myStr[1:]
