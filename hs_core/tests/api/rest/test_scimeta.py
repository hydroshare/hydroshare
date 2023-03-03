import os
import tempfile
import shutil

from lxml import etree

from hs_core.hydroshare import resource
from .base import SciMetaTestCase


class TestScienceMetadata(SciMetaTestCase):
    def setUp(self):
        super(TestScienceMetadata, self).setUp()

        self.rtype = "CompositeResource"
        self.title = "My Test resource"
        res = resource.create_resource(self.rtype, self.user, self.title)
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_get_scimeta(self):
        # Get science metadata XML
        self.getScienceMetadata(self.pid)
        # TODO: test that content is reasonable!

    def test_put_scimeta_generic(self):
        # Update science metadata XML
        abstract_text = "This is an abstract"
        tmp_dir = tempfile.mkdtemp()

        try:
            # Get science metadata
            response = self.getScienceMetadata(self.pid, exhaust_stream=False)
            sci_meta_orig = os.path.join(tmp_dir, self.RESOURCE_METADATA_OLD)
            with open(sci_meta_orig, "wb") as f:
                for line in response.streaming_content:
                    f.write(line)

            scimeta = etree.parse(sci_meta_orig)
            self.getAbstract(
                scimeta, should_exist=False, rdf_type="hsterms:CompositeResource"
            )

            # Modify science metadata
            desc = scimeta.xpath(
                "/rdf:RDF/hsterms:CompositeResource[1]", namespaces=self.NS
            )[0]
            abs_dc_desc = etree.SubElement(desc, "{%s}description" % self.NS["dc"])
            abs_rdf_desc = etree.SubElement(
                abs_dc_desc, "{%s}Description" % self.NS["rdf"]
            )
            abstract = etree.SubElement(
                abs_rdf_desc, "{%s}abstract" % self.NS["dcterms"]
            )
            abstract.text = abstract_text
            # Write out to a file
            out = etree.tostring(scimeta, encoding="UTF-8", pretty_print=True).decode()
            sci_meta_new = os.path.join(tmp_dir, self.RESOURCE_METADATA)
            with open(sci_meta_new, "w") as f:
                f.writelines(out)

            #    Send updated metadata to REST API
            self.updateScimeta(self.pid, sci_meta_new)

            #    Get science metadata
            response = self.getScienceMetadata(self.pid, exhaust_stream=False)
            sci_meta_updated = os.path.join(tmp_dir, self.RESOURCE_METADATA_UPDATED)
            with open(sci_meta_updated, "wb") as f:
                for line in response.streaming_content:
                    f.write(line)

            scimeta = etree.parse(sci_meta_updated)
            abstract = self.getAbstract(scimeta, rdf_type="hsterms:CompositeResource")
            self.assertEqual(abstract, abstract_text)

            # Make sure metadata update is idempotent
            #   Resend the previous request
            self.updateScimeta(self.pid, sci_meta_new)

            # Make sure changing the resource ID in the resource metadata causes an error
            self.updateScimetaResourceID(
                scimeta, "THISISNOTARESOURCEID", rdf_type="hsterms:CompositeResource"
            )
            #    Write out to a file
            out = etree.tostring(scimeta, encoding="UTF-8", pretty_print=True).decode()
            with open(sci_meta_new, "w") as f:
                f.writelines(out)

            #    Send broken metadata to REST API
            self.updateScimeta(self.pid, sci_meta_new, should_succeed=False)

        finally:
            shutil.rmtree(tmp_dir)
