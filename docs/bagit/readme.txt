This zip file contains a HydroShare resource in Bagit format.  

The data for the resource you downloaded is in the "data/contents" directory.

The metadata for the resource is stored in the xml file "data/resourcemetadata.xml."

A "resource" is the primary unit of content within HydroShare. Because resources may be made up of one or more files and may also have a hierarchical file/directory structure, HydroShare needed a way to consistently package resources for transport over the Internet. We use the BagIt file packaging format for this purpose. We chose BagIt because it is widely used by a number of organizations and online repositories involved in digital preservation, including the U.S. Library of Congress.

You can find the full BagIt specification here: https://tools.ietf.org/html/draft-kunze-bagit-13. 

You can also find a much more detailed description of HydroShare's resource data model and packaging scheme in the following paper:

Horsburgh, J. S., Morsy, M. M., Castronova, A., Goodall, J. L., Gan, T., Yi, H., Stealey, M. J., and D.G. Tarboton (2015). HydroShare: Sharing diverse hydrologic data types and models as social objects within a Hydrologic Information System, Journal Of the American Water Resources Association(JAWRA), http://dx.doi.org/10.1111/1752-1688.12363.

We've summarized the important points below.

Zip File (the "bag") Structure
--------------------------------------
Once you unzip the downloaded file, you should see a single folder. This folder is called the "base directory." The name of this folder is the resource's unique identifier in the HydroShare system. Within the base directory is the content of the resource.  The following is an example of what you would get if you download a time series resource, but all resources use the same structure:

1a25b11fa1354773b6edb9495e754f4e/    # Base directory
    bagit.txt                        # Tag file with BagIt version number
    manifest-md5.txt                 # Tag file with resource file manifest
    readme.txt                       # this readme file
    tagmanifest-md5.txt              # Tag manifest file
    data/                            # Payload directory
        resourcemap.xml              # Resource map document
        resourcemetadata.xml         # Resource-level metadata document
        visualization/               # Tag directory for thumbnail visualization
            thumbnail.jpg            # Thumbnail visualization file
        contents/                    # Tag directory containing content files
            ODM2.sqlite              # Content file

Zip File Content 
---------------------
The following are descriptions of each element of the resource bag:

"1a25b11fa1354773b6edb9495e754f4e/" - This is the base directory named using the resource's HydroShare identifier. It is a container for the whole resource.

"bagit.txt" - This text file specifies which version of the BagIt specification was used to create the bag.

"manifest-md5.txt" - This is a manifest file that lists every file in the resource and provides a checksum for each file calculated using the MD5 algorithm. The file manifest and the checksums can be used to verify that all of the files within a resource have been retrieved with full integrity.

"readme.txt" - This readme file describes the downloaded HydroShare resource bag.

"tagmanifest-md5.txt" - This is a tag manifest file that lists tag files and their associated checksums calculated using the MD5 algorithm.

"data/" - This subdirectory also called the "payload directory." All of the content files of the resource are stored within the "data" directory.

"resourcemap.xml" - This XML document contains an Open Archives Initiative Object Reuse and Exchange (OAI-ORE) resource map. It is a list of all of the files within the resource and any relationships that exist between them. The purpose of this file is to enable a computer to discover the structure of the resource.

"resourcemetadata.xml" - This XML document stores the main metadata for the resource. It contains at least the standard Dublin Core metadata elements and may contain extended metadata elements, depending on the resource type.

"visualization/" - This is a subdirectory within which an optional thumbnail visualization of the resource may reside if present.

"contents/" - This is the subdirectory within which the content files of the resource will be stored. There can be any number of folders/files within this subdirectory, depending on the required structure of the resource.
