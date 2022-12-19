# -*- coding: utf-8 -*-


from django.db import migrations
from django import db


class Migration(migrations.Migration):

    dependencies = [
        ("hs_tools_resource", "0020_auto_20180604_1845"),
    ]

    def forwards(self, orm):
        db.rename_column(
            "hs_tools_resource_toolmetadata", "mailing_list_url", "_mailing_list_url"
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata",
            "testing_protocol_url",
            "_testing_protocol_url",
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata", "help_page_url", "_help_page_url"
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata", "source_code_url", "_source_code_url"
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata", "issues_page_url", "_issues_page_url"
        )
        db.rename_column("hs_tools_resource_toolmetadata", "roadmap", "_roadmap")

    def backwards(self, orm):
        db.rename_column(
            "hs_tools_resource_toolmetadata", "_mailing_list_url", "mailing_list_url"
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata",
            "_testing_protocol_url",
            "testing_protocol_url",
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata", "_help_page_url", "help_page_url"
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata", "_source_code_url", "source_code_url"
        )
        db.rename_column(
            "hs_tools_resource_toolmetadata", "_issues_page_url", "issues_page_url"
        )
        db.rename_column("hs_tools_resource_toolmetadata", "_roadmap", "roadmap")
