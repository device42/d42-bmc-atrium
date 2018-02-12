# Device42 BMC Atrium Integration 

## Introduction 

This integration will help those using both Device42 and BMC Atrium to syncrhnoize their datasets with up to date configuration data collected by Device42's continuous automated discovery tools.  This integration is written in Python3 and should be ran on a machine with access to both the API endpoints of Device42 and BMC Atrium.     

## Configuration 

Configuration is handled in the `mapping.xml` file.  

The Settings element should be filled with the URL and user crednetials for both your BMC Atrium and Device42 deployments.  

Individual *task* items are listed within the *Tasks* element.  Each *task* represents both a query to Device42 and a CI class to create instances of for the records returned from Device42. The *task* element contains two children: *api* and *mapping*.  

The *api* element contains a *target* and *resource*.  The *resource* element describes how to query Device42 for records, whereas the *target* element configures where to POST or PATCH bulk requests on BMC.    

The *mapping* element first sets some boilerplate. The *callback* attribute should always be set to "from_d42" as this integration only supports importing data from Device42 to BMC Atrium.  The  *source* attribute of the *mapping* element tells the integration script what key to access in the return data from Device42.  For example, on the `/api/1.0/devices/all/` endpoint, all the devices will be listed under a key named "Devices". The *mapping* element's *class, dataset,* and *namespace* attributes are important.  They represent the kind of BMC instance that will be created by the integration.  As seen in the second task in the `mapping.xml` file included within this repository, we are using devices returned from Device42 to create instances of the class `BMC\_ComputerSystem` under the `BMC.CORE` namespace in the `BMC.ASSET` dataset on Atrium's CMDB.  

Finally, the *mapping* element contains a list of *field* child elements.  These fields are used to associate fields in the dataset returned from the D42 API or DOQL response to attributes of the given BMC class being created.  In the included example, the second *task* element uses each device's `device_id`, along with a basic prefix and sufix rule, to create the `instance_id` for the `BMC\_ComputerSystem` instance being created or updated.   As you likely infered, prefixes and suffixes can be added using the *prefix* (appearing before the data from d42) and *suffix* (appearing after the data from d42) attributes.  

If you want to set an attribute on a BMC CI instnce to a hardcoded value instead of something stored on Device42, you can use the *value* attribute of the *field* element to do this, which is demonstrated in the third *task* element included in the `mapping.xml` file.  


## Notes 

[More information about the BMC Atrium REST API Endpoints](https://docs.bmc.com/docs/ac91/endpoints-in-the-rest-api-722593589.html)
[More information about the D42 REST API Endpoints](https://api.device42.com/)
