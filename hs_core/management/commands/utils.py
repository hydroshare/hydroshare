def migrate_core_meta_elements(orig_meta_obj, comp_res):
    """
    Helper to migrate core metadata elements from the resource that is converted to
    composite resource
    :param orig_meta_obj: metadata object of the resource that is getting converted to
    composite resource
    :param comp_res: converted composite resource
    :return:
    """
    single_meta_elements = ['title', 'type', 'language', 'rights', 'description',
                            'publisher']
    multiple_meta_elements = ['creators', 'contributors', 'coverages', 'subjects',
                              'dates', 'formats', 'identifiers', 'sources', 'relations',
                              'funding_agencies']
    for meta_element_name in single_meta_elements:
        meta_element = getattr(orig_meta_obj, meta_element_name)
        if meta_element is not None:
            meta_element.content_object = comp_res.metadata
            meta_element.save()
    for meta_element_name in multiple_meta_elements:
        meta_elements = getattr(orig_meta_obj, meta_element_name)
        for meta_element in meta_elements.all():
            meta_element.content_object = comp_res.metadata
            meta_element.save()
