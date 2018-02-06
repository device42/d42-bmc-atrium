import sys, json, random, string
from importlib import reload


reload(sys)

DEBUG = True


def get_existing_cherwell_objects(service, configuration_item, page, data):
    bus_ib_pub_ids_request_data = {
        "busObId": configuration_item,
        'includeAllFields': True,
        "pageNumber": page,
        "pageSize": 100
    }
    bus_ib_pub_ids = service.request('/api/V1/getsearchresults', 'POST', bus_ib_pub_ids_request_data)
    data += bus_ib_pub_ids["businessObjects"]
    if bus_ib_pub_ids["totalRows"] > page * 100:
        page += 1
        get_existing_cherwell_objects(service, configuration_item, page, data)

    return data


def get_existing_cherwell_objects_map(data):
    result = {}
    cnt = 0
    for item in data:
        for field in item['fields']:
            if field['name'] == 'U_device42_id':
                result[field['value']] = {
                    "busObPublicId": item["busObPublicId"],
                    "busObRecId": item["busObRecId"],
                }
                cnt += 1
    print(cnt)
    return result


def random_string(length=10):
    # generates a pretty random string for use during testing
    return str(
        ''.join(random.choice(
            string.digits + string.ascii_lowercase
        )
            for _ in range(length))
    )


def build_child_item():
    schema = {
            "instance": {
                "instance_id": "",
                "class_name_key": {
                    "name": "",
                    "namespace": "",
                    "_links": {}
                },
                "dataset_id": "",
                "attributes": {
                    "ShortDescription": "d42"
                },
                "_links": {}
            },
            "deleteOption": "string",
            "operation": "POST",
            "_links": {}
    }


    

def perform_bulk_request(
    mapping,
    fields,
    match_map,
    _target,
    _resource,
    source,
    target_api,
    resource_api,
    existing_objects_map=None,
):

    bulk_payload = []

    print(
        '# of objects returned from D42: ', str(
            len(source[mapping.attrib['source']])
        )
    )

    # for each item returned from D42
    for item in source[mapping.attrib['source']]:
        print('device_id: ', item['device_id'])
        attributes = {}
        # schema will be filled with the content of each item
        schema = {
            "instance": {
                "instance_id": "",
                "class_name_key": {
                    "name": "",
                    "namespace": "",
                    "_links": {}
                },
                "dataset_id": "",
                "attributes": {
                    "ShortDescription": "d42"
                },
                "_links": {}
            },
            "deleteOption": "string",
            "operation": "POST",
            "_links": {}
        }
        # default / general values
        schema['instance']['instance_id'] = "%s_%s_d42" % (
            str(item['device_id']), random_string(7)  # to ensure random
        )
        namespace = mapping.attrib['namespace']
        classname = mapping.attrib['class']
        dataset = mapping.attrib['dataset']
        # filling default values, will overwrite where needed
        schema['instance']['class_name_key']['namespace'] = namespace
        schema['instance']['class_name_key']['name'] = classname
        schema['instance']['dataset_id'] = dataset

        # loop through devices
        # and find fields shared between the item and the mapping fields
        for field in fields:
            print('current field: ', str(field.attrib['resource']))
            # check if field overrides default class
            if field.get('child_class'):
                child_class = field.attrib['child_class']
                # schema['instance']['class_name_key']['name'] = child_class
                if field.get('dataset') and field.get('namespace'):
                    # override default values for this attribute
                    # ns = field.attrib['namespace']
                    # ds = field.attrib['dataset']

                    # build a child item schema externally and return it here
                    # to be added to the bulk payload
                    schema = build_child_item(field) 
                    
                    # schema['instance']['class_name_key']['namespace'] = ns
                    # schema['instance']['dataset_id'] = ds

            # check if field is a top level or nested
            # if nested
            if field.get('sub-key'):
                # if it has a subkey,
                # then we grab subkey from the resource @ field
                # then check to see if item has this resource.subkey
                if item[field.attrib['resource']][field.attrib['sub-key']]:
                    # then add to attributes
                    target = field.attrib['target']
                    resource = item[field.attrib['resource']][field.attrib['sub-key']]
                    attributes[target] = resource
            # if top level
            if item[field.attrib['resource']]:
                target = field.attrib['target']
                resource = item[field.attrib['resource']]
                attributes[target] = resource

        schema['instance']['attributes'] = attributes

        bulk_payload.append(schema)

    print('payload: ')
    print(json.dumps(bulk_payload, indent=4))
    print(type(target_api))
    response = target_api.request(_target.attrib['path'], 'POST', bulk_payload)
    print("bulk insert API response: %s" % json.dumps(response, indent=4))
    sys.exit


    # perform bulk insert

    # batch = {
    #     "saveRequests": [],
    #     "stopOnError": DEBUG
    # }

    # for item in source[mapping.attrib['source']]:
    #     batch["saveRequests"].append(
    #         fill_business_object(
    #             bus_object['fields'],
    #             item,
    #             configuration_item,
    #             match_map,
    #             existing_objects_map,
    #             mapping.attrib['key'],
    #             resource_api
    #         )
    #     )

    # response = target_api.request(_target.attrib['path'], 'POST', batch)

    # if response["hasError"] and DEBUG:
    #     print(response['responses'][-1:][0]["errorMessage"])
    #     return False

    # offset = source.get("offset", 0)
    # limit = source.get("limit", 100)
    # if offset + limit < source["total_count"]:
    #     print("Exported {} of {} records".format(offset + limit, source["total_count"]))
    #     source_url = _resource.attrib['path']
    #     if _resource.attrib.get("extra-filter"):
    #         source_url += _resource.attrib.get("extra-filter") + "&amp;"
    #     source = resource_api.request(
    #         "{}offset={}".format(source_url, offset + limit),
    #         _resource.attrib['method'])
        # perform_butch_request(
        #     bus_object,
        #     mapping,
        #     match_map,
        #     _target,
        #     _resource,
        #     source,
        #     existing_objects_map,
        #     target_api,
        #     resource_api,
        #     configuration_item
        # )
    return True


def from_d42(source, mapping, _target, _resource, target_api, resource_api):
    fields = mapping.findall('field')
    field_names = [field.attrib['target'] for field in fields]

    # match_map contains 'target field': field
    match_map = {field.attrib['target']: field for field in fields}

    namespace = mapping.attrib['namespace']
    # bus_object_config = {
    #     "busObId": configuration_item,
    #     "fieldNames": field_names
    # }

    # TODO: incorporate existing_object function
    # existing_objects = get_existing_cherwell_objects(target_api, configuration_item, 1, [])
    # existing_objects_map = get_existing_cherwell_objects_map(existing_objects)

    # bus_object = target_api.request('/api/V1/getbusinessobjecttemplate', 'POST', bus_object_config)
    success = perform_bulk_request(
        mapping,
        fields,
        match_map,
        _target,
        _resource,
        source,
        # existing_objects_map,
        target_api,
        resource_api,
    )

    if success:
        print("Success")
    else:
        print("Something bad happened")
