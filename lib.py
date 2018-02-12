import sys, json, random, string, logging
from importlib import reload
from doql import Doql_Util

reload(sys)

DEBUG = True

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
handler = logging.FileHandler("d42bmc.log")
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def get_existing_bmc_cis(ds, ns, cn, bmc_agent, bmc):
    # ds {datasetId}/ ns {namespace}/ cn{className}
    # /cmdb/v1.0/instances/{datasetId}/{namespace}/{className}
    path = "/api/cmdb/v1.0/instances/%s/%s/%s" % (ds, ns, cn)
    path = path + "?attributes=InstanceId"
    existing_ids = bmc_agent.request(path, 'GET')
    ids = []
    for i in existing_ids['instances']:
        ids.append(i['instance_id'])
    return ids


def random_string(length=10):
    # generates a pretty random string for use during testing
    return str(
        ''.join(random.choice(
            string.digits + string.ascii_lowercase
        )
            for _ in range(length))
    )

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
    namespace = mapping.attrib['namespace']
    classname = mapping.attrib['class']
    dataset = mapping.attrib['dataset']
    # get existing BMC CI instance ids 
    existing_ids = get_existing_bmc_cis(
        dataset,
        namespace,
        classname,
        target_api,
        _target
    )
    print("existing IDs ", json.dumps(existing_ids, indent=2))

    print("source: ", json.dumps(source, indent=2))
    # for each item returned from D42
    for item in source[mapping.attrib['source']]:
        # print("current item: \n %s" % json.dumps(item, indent=2))
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
            # check if field is a top level or nested
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
            if item.get(field.attrib['resource']): # if not empty
                target = field.attrib['target']
                print("target: ", target)
                resource = item[field.attrib['resource']]

                if field.get('prefix'):
                    # add prefix to resource
                    prefix = field.attrib['prefix']
                    resource = "%s%s" % (prefix, resource)

                if field.get('suffix'):
                    # add suffix to resource
                    suffix = field.attrib['suffix']
                    resource = "%s%s" % (resource, suffix)

                # unique instance_id is a required field outside attributes
                if target == "instance_id" or target == "InstanceId":
                    # resource = "OI-4A7D1B44286E43AB8C93B45CA52C73D0"
                    if resource in existing_ids:
                        schema['operation'] = "PATCH"
                    schema['instance']['instance_id'] = resource
                    attributes['InstanceId'] = resource 
                else:
                    attributes[target] = resource
            else: # resource is empty, check if value 
                if field.get('value'): # hardcoded value, not null
                    if item.get(field.attrib['value']): # dont try to get attrib if doesnt exist
                        target = field.attrib['target']
                        value = item[field.attrib['value']]
                        attributes[target] = value

        schema['instance']['attributes'] = attributes

        bulk_payload.append(schema)

    print("bulk payload: \n %s" % json.dumps(bulk_payload, indent=2))

    response = target_api.request(_target.attrib['path'], 'POST', bulk_payload)
    logger.info("BMC bulk insert response: %s" % json.dumps(response, indent=4))
    print("bulk insert API response: %s" % json.dumps(response, indent=4))

    return True


def from_d42(
    source, mapping, 
    _target, _resource, 
    target_api, resource_api, 
    doql=False
):
    fields = mapping.findall('field')
    field_names = [field.attrib['target'] for field in fields]
    print('field names: ', field_names)

    # convert CSV doql results to JSON
    if doql is True:
        doql_util = Doql_Util()
        source = doql_util.csv_to_json(
            source,
            mapping_source=mapping.attrib['source']
        )

    # match_map contains 'target field': field
    match_map = {field.attrib['target']: field for field in fields}
    print('match_map: ', match_map)

    # TODO: incorporate existing_object function
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
