class Utils():

    def find(dict_list, key, expected):
        return next((item for item in dict_list if item.get(key) == expected), None)
