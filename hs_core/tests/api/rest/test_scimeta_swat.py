import os
import tempfile
import shutil

from lxml import etree

from hs_core.hydroshare import resource
from .base import ModelInstanceSciMetaTestCase


class TestScienceMetadataSWAT(ModelInstanceSciMetaTestCase):

    def test_put_scimeta_swat_model_instance(self):
        # Update science metadata XML
        title_1 = 'Flat River SWAT Instance'
        title_2 = 'Cannon river'
        abstract_text_1 = 'This model is created for Flat River.'
        abstract_text_2 = ('This is a test to the SWAT Model Instance resource. '
                           'All the data had been obtained from real share SWAT '
                           'model from SWATShare https://mygeohub.org/groups/water-hub/swatshare. '
                           'Some of the metadata entries are assumed just used '
                           'to test the resource implementation')
        kwords_1 = ('SWAT2009', 'FlatRIver')
        kwords_2 = ('Cannon River', 'SWAT', 'SWATShare')
        model_output_1 = 'No'
        model_output_2 = 'Yes'
        model_prog_name_1 = 'Unspecified'
        model_prog_name_2 = self.title_prog
        model_prog_id_1 = 'None'
        model_prog_id_2 = self.pid_prog
        _, tmp_dir = tempfile.mkstemp()

        res = resource.create_resource('SWATModelInstanceResource',
                                       self.user,
                                       'Test SWAT Model Instance Resource')
        pid = res.short_id
        self.resources_to_delete.append(pid)

        try:
            # Apply metadata from saved file
            #   First update the resource ID so that it matches the ID of the
            #   newly created resource.
            scimeta = etree.parse('hs_core/tests/data/swat-resourcemetadata-1.xml')
            self.updateScimetaResourceID(scimeta, pid)
            #   Write out to a file
            out = etree.tostring(scimeta, pretty_print=True)
            sci_meta_new = os.path.join(tmp_dir, self.RESOURCE_METADATA)
            with open(sci_meta_new, 'w') as f:
                f.writelines(out)

            #   Send updated metadata to REST API
            self.updateScimeta(pid, sci_meta_new)

            #   Get science metadata
            response = self.getScienceMetadata(pid, exhaust_stream=False)
            sci_meta_updated = os.path.join(tmp_dir, self.RESOURCE_METADATA_UPDATED)
            with open(sci_meta_updated, 'w') as f:
                for l in response.streaming_content:
                    f.write(l)

            scimeta = etree.parse(sci_meta_updated)
            abstract = self.getAbstract(scimeta)
            self.assertEqual(abstract, abstract_text_1)

            title = self.getTitle(scimeta)
            self.assertEqual(title, title_1)

            keywords = self.getKeywords(scimeta)
            kw_comp = zip(kwords_1, keywords)
            for k in kw_comp:
                self.assertEqual(k[0], k[1])

            model_output = scimeta.xpath(self.MOD_OUT_PATH,
                                         namespaces=self.NS)
            self.assertEqual(len(model_output), 1)
            self.assertEqual(model_output_1, model_output[0].text)

            prog_name = scimeta.xpath(self.EXECUTED_BY_NAME_PATH,
                                      namespaces=self.NS)
            self.assertEqual(len(prog_name), 1)
            self.assertEqual(model_prog_name_1, prog_name[0].text)

            prog_id = scimeta.xpath(self.EXECUTED_BY_ID_PATH,
                                    namespaces=self.NS)
            self.assertEqual(len(prog_id), 1)
            self.assertEqual(model_prog_id_1, prog_id[0].text)

            # Make sure metadata update is idempotent
            self.updateScimeta(pid, sci_meta_new)

            #    Get science metadata
            response = self.getScienceMetadata(pid, exhaust_stream=False)
            sci_meta_updated = os.path.join(tmp_dir, self.RESOURCE_METADATA_UPDATED)
            with open(sci_meta_updated, 'w') as f:
                for l in response.streaming_content:
                    f.write(l)

            scimeta = etree.parse(sci_meta_updated)
            abstract = self.getAbstract(scimeta)
            self.assertEqual(abstract, abstract_text_1)

            title = self.getTitle(scimeta)
            self.assertEqual(title, title_1)

            keywords = self.getKeywords(scimeta)
            kw_comp = zip(kwords_1, keywords)
            for k in kw_comp:
                self.assertEqual(k[0], k[1])

            model_output = scimeta.xpath(self.MOD_OUT_PATH,
                             namespaces=self.NS)
            self.assertEqual(len(model_output), 1)
            self.assertEqual(model_output_1, model_output[0].text)

            prog_name = scimeta.xpath(self.EXECUTED_BY_NAME_PATH,
                                      namespaces=self.NS)
            self.assertEqual(len(prog_name), 1)
            self.assertEqual(model_prog_name_1, prog_name[0].text)

            prog_id = scimeta.xpath(self.EXECUTED_BY_ID_PATH,
                                    namespaces=self.NS)
            self.assertEqual(len(prog_id), 1)
            self.assertEqual(model_prog_id_1, prog_id[0].text)

            # Overwrite metadata with other resource metadata
            #   First update the resource ID so that it matches the ID of the
            #   newly created resource.
            scimeta = etree.parse('hs_core/tests/data/swat-resourcemetadata-2.xml')
            self.updateScimetaResourceID(scimeta, pid)
            self.updateExecutedBy(scimeta, model_prog_name_2, model_prog_id_2)
            #   Write out to a file
            out = etree.tostring(scimeta, pretty_print=True)
            sci_meta_new = os.path.join(tmp_dir, self.RESOURCE_METADATA)
            with open(sci_meta_new, 'w') as f:
                f.writelines(out)

            #   Send updated metadata to REST API
            self.updateScimeta(pid, sci_meta_new)

            #   Get science metadata
            response = self.getScienceMetadata(pid, exhaust_stream=False)
            sci_meta_updated = os.path.join(tmp_dir, self.RESOURCE_METADATA_UPDATED)
            with open(sci_meta_updated, 'w') as f:
                for l in response.streaming_content:
                    f.write(l)

            scimeta = etree.parse(sci_meta_updated)

            abstract = self.getAbstract(scimeta)
            self.assertEqual(abstract, abstract_text_2)

            title = self.getTitle(scimeta)
            self.assertEqual(title, title_2)

            keywords = self.getKeywords(scimeta)
            kw_comp = zip(kwords_2, keywords)
            for k in kw_comp:
                self.assertEqual(k[0], k[1])

            model_output = scimeta.xpath(self.MOD_OUT_PATH,
                             namespaces=self.NS)
            self.assertEqual(len(model_output), 1)
            self.assertEqual(model_output_2, model_output[0].text)

            prog_name = scimeta.xpath(self.EXECUTED_BY_NAME_PATH,
                                      namespaces=self.NS)
            self.assertEqual(len(prog_name), 1)
            self.assertEqual(model_prog_name_2, prog_name[0].text)

            prog_id = scimeta.xpath(self.EXECUTED_BY_ID_PATH,
                                    namespaces=self.NS)
            self.assertEqual(len(prog_id), 1)

            prog_id_2 = prog_id[0].text.strip('/').rpartition('/')[-1]
            self.assertEqual(model_prog_id_2, prog_id_2)

        finally:
            shutil.rmtree(tmp_dir)
