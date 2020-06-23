def split_csdms_names():
    """ Split each record in csdms file and assign them to corresponding return part
        :return names, names in csdms
        :return splitted_names, split each name by space
        :return decors, decorations for each name in csdms
        :return splitted_decors, split each decor by space

    """
    filename = 'hs_csdms/csdms'
    std_names = []
    with open(filename) as f:
        std_names = f.readlines()
    std_names = [x.strip() for x in std_names]
    names = set()
    measures = set()
    decors = set()
    for std_name in std_names:
        tokens = std_name.split("__")
        name = tokens[0]
        if len(tokens) > 1:
            measure = tokens[1].replace("_", " ")
            measures.add(measure)
        name_tokens = name.split("~")
        raw_name = name_tokens[0].replace("_", " ")
        names.add(raw_name)
        if len(name_tokens) > 1:
            for d in name_tokens[1:]:
                raw_d = d.replace("_", " ")
                decors.add(raw_d)

    return names, decors, measures
