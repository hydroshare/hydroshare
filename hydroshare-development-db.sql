--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'SQL_ASCII';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

ALTER TABLE ONLY public.djcelery_taskstate DROP CONSTRAINT worker_id_refs_id_6fd8ce95;
ALTER TABLE ONLY public.hs_core_genericresource_edit_groups DROP CONSTRAINT user_id_refs_id_ba84458b;
ALTER TABLE ONLY public.generic_rating DROP CONSTRAINT user_id_refs_id_9436ba96;
ALTER TABLE ONLY public.blog_blogpost DROP CONSTRAINT user_id_refs_id_01a962b8;
ALTER TABLE ONLY public.blog_blogpost_related_posts DROP CONSTRAINT to_blogpost_id_refs_id_6404941b;
ALTER TABLE ONLY public.ga_resources_renderedlayer_styles DROP CONSTRAINT style_id_refs_page_ptr_id_934fbf43;
ALTER TABLE ONLY public.core_sitepermission_sites DROP CONSTRAINT sitepermission_id_refs_id_7dccdcbd;
ALTER TABLE ONLY public.generic_keyword DROP CONSTRAINT site_id_refs_id_f6393455;
ALTER TABLE ONLY public.hs_scholar_profile_organization DROP CONSTRAINT site_id_refs_id_bf232785;
ALTER TABLE ONLY public.blog_blogpost DROP CONSTRAINT site_id_refs_id_ac21095f;
ALTER TABLE ONLY public.blog_blogcategory DROP CONSTRAINT site_id_refs_id_93afc60f;
ALTER TABLE ONLY public.core_sitepermission_sites DROP CONSTRAINT site_id_refs_id_91a6d9d4;
ALTER TABLE ONLY public.theme_siteconfiguration DROP CONSTRAINT site_id_refs_id_8ee83179;
ALTER TABLE ONLY public.hs_party_organization DROP CONSTRAINT site_id_refs_id_8566506f;
ALTER TABLE ONLY public.pages_page DROP CONSTRAINT site_id_refs_id_70c9ac77;
ALTER TABLE ONLY public.hs_party_group DROP CONSTRAINT site_id_refs_id_6c5d0e92;
ALTER TABLE ONLY public.hs_party_person DROP CONSTRAINT site_id_refs_id_550d54a5;
ALTER TABLE ONLY public.django_redirect DROP CONSTRAINT site_id_refs_id_390e2add;
ALTER TABLE ONLY public.conf_setting DROP CONSTRAINT site_id_refs_id_29e7e142;
ALTER TABLE ONLY public.hs_scholar_profile_scholargroup DROP CONSTRAINT site_id_refs_id_242b097b;
ALTER TABLE ONLY public.hs_scholar_profile_person DROP CONSTRAINT site_id_refs_id_1ba836f6;
ALTER TABLE ONLY public.hs_scholar_profile_scholarexternalidentifiers DROP CONSTRAINT scholar_id_refs_person_ptr_id_2aa668e3;
ALTER TABLE ONLY public.ga_resources_orderedresource DROP CONSTRAINT resource_group_id_refs_page_ptr_id_9dce21a0;
ALTER TABLE ONLY public.generic_threadedcomment DROP CONSTRAINT replied_to_id_refs_comment_ptr_id_83bd8e31;
ALTER TABLE ONLY public.ga_resources_renderedlayer_styles DROP CONSTRAINT renderedlayer_id_refs_page_ptr_id_7bc3ed6b;
ALTER TABLE ONLY public.hs_scholar_profile_userdemographics DROP CONSTRAINT region_id_refs_id_ee73987e;
ALTER TABLE ONLY public.dublincore_qualifieddublincoreelementhistory DROP CONSTRAINT qdce_id_refs_id_7eb27ec4;
ALTER TABLE ONLY public.hs_party_person DROP CONSTRAINT "primaryOrganizationRecord_id_refs_party_ptr_id_fed37680";
ALTER TABLE ONLY public.hs_party_organizationphone DROP CONSTRAINT phone_type_id_refs_code_9880d355;
ALTER TABLE ONLY public.hs_party_personphone DROP CONSTRAINT phone_type_id_refs_code_1a00e417;
ALTER TABLE ONLY public.hs_party_othername DROP CONSTRAINT persons_id_refs_party_ptr_id_08307bb2;
ALTER TABLE ONLY public.hs_scholar_profile_othernames DROP CONSTRAINT persons_id_refs_id_9a63bcca;
ALTER TABLE ONLY public.hs_scholar_profile_scholar DROP CONSTRAINT person_ptr_id_refs_id_68cfedf7;
ALTER TABLE ONLY public.hs_party_personemail DROP CONSTRAINT person_id_refs_party_ptr_id_a7a2c64b;
ALTER TABLE ONLY public.hs_party_personexternalidentifier DROP CONSTRAINT person_id_refs_party_ptr_id_8c5cca63;
ALTER TABLE ONLY public.hs_party_personlocation DROP CONSTRAINT person_id_refs_party_ptr_id_679331e1;
ALTER TABLE ONLY public.hs_party_personphone DROP CONSTRAINT person_id_refs_party_ptr_id_3af9b7d7;
ALTER TABLE ONLY public.hs_party_organizationassociation DROP CONSTRAINT person_id_refs_party_ptr_id_37520c31;
ALTER TABLE ONLY public.hs_scholar_profile_personlocation DROP CONSTRAINT person_id_refs_id_cd05bc69;
ALTER TABLE ONLY public.hs_scholar_profile_personemail DROP CONSTRAINT person_id_refs_id_988d2157;
ALTER TABLE ONLY public.hs_scholar_profile_userkeywords DROP CONSTRAINT person_id_refs_id_7066e467;
ALTER TABLE ONLY public.hs_scholar_profile_orgassociations DROP CONSTRAINT person_id_refs_id_15958bad;
ALTER TABLE ONLY public.hs_scholar_profile_personphone DROP CONSTRAINT person_id_refs_id_0f828f02;
ALTER TABLE ONLY public.hs_party_organization DROP CONSTRAINT party_ptr_id_refs_id_c897f9af;
ALTER TABLE ONLY public.hs_party_group DROP CONSTRAINT party_ptr_id_refs_id_b233f9c9;
ALTER TABLE ONLY public.hs_party_person DROP CONSTRAINT party_ptr_id_refs_id_a4c921fd;
ALTER TABLE ONLY public.pages_page DROP CONSTRAINT parent_id_refs_id_68963b8e;
ALTER TABLE ONLY public.hs_party_organization DROP CONSTRAINT "parentOrganization_id_refs_party_ptr_id_fb22991c";
ALTER TABLE ONLY public.hs_scholar_profile_organization DROP CONSTRAINT "parentOrganization_id_refs_id_0d5d7e04";
ALTER TABLE ONLY public.forms_form DROP CONSTRAINT page_ptr_id_refs_id_fe19b67b;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT page_ptr_id_refs_id_f73583c5;
ALTER TABLE ONLY public.theme_homepage DROP CONSTRAINT page_ptr_id_refs_id_bf381bd5;
ALTER TABLE ONLY public.ga_resources_style DROP CONSTRAINT page_ptr_id_refs_id_ae3b1c29;
ALTER TABLE ONLY public.ga_resources_catalogpage DROP CONSTRAINT page_ptr_id_refs_id_a8ba09aa;
ALTER TABLE ONLY public.ga_resources_resourcegroup DROP CONSTRAINT page_ptr_id_refs_id_93df8296;
ALTER TABLE ONLY public.galleries_gallery DROP CONSTRAINT page_ptr_id_refs_id_75804475;
ALTER TABLE ONLY public.ga_resources_dataresource DROP CONSTRAINT page_ptr_id_refs_id_5ea3a75a;
ALTER TABLE ONLY public.pages_richtextpage DROP CONSTRAINT page_ptr_id_refs_id_558d29bc;
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT page_ptr_id_refs_id_41a57472;
ALTER TABLE ONLY public.pages_link DROP CONSTRAINT page_ptr_id_refs_id_2adddb0b;
ALTER TABLE ONLY public.ga_resources_relatedresource DROP CONSTRAINT page_ptr_id_refs_id_1f0514ba;
ALTER TABLE ONLY public.ga_resources_style DROP CONSTRAINT owner_id_refs_id_f919891d;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT owner_id_refs_id_ee8494bc;
ALTER TABLE ONLY public.hs_core_groupownership DROP CONSTRAINT owner_id_refs_id_e2271514;
ALTER TABLE ONLY public.ga_resources_catalogpage DROP CONSTRAINT owner_id_refs_id_d528c757;
ALTER TABLE ONLY public.ga_resources_dataresource DROP CONSTRAINT owner_id_refs_id_4a4141f5;
ALTER TABLE ONLY public.hs_party_organizationlocation DROP CONSTRAINT organization_id_refs_party_ptr_id_fd2c3320;
ALTER TABLE ONLY public.hs_party_organizationname DROP CONSTRAINT organization_id_refs_party_ptr_id_e8cc2840;
ALTER TABLE ONLY public.hs_party_organizationassociation DROP CONSTRAINT organization_id_refs_party_ptr_id_aeafced6;
ALTER TABLE ONLY public.hs_party_organizationemail DROP CONSTRAINT organization_id_refs_party_ptr_id_933e120e;
ALTER TABLE ONLY public.hs_party_externalorgidentifier DROP CONSTRAINT organization_id_refs_party_ptr_id_3d58b415;
ALTER TABLE ONLY public.hs_party_organizationphone DROP CONSTRAINT organization_id_refs_party_ptr_id_3414fe3c;
ALTER TABLE ONLY public.hs_scholar_profile_externalorgidentifiers DROP CONSTRAINT organization_id_refs_id_e49f9749;
ALTER TABLE ONLY public.hs_scholar_profile_organizationemail DROP CONSTRAINT organization_id_refs_id_d3109675;
ALTER TABLE ONLY public.hs_scholar_profile_orgassociations DROP CONSTRAINT organization_id_refs_id_bf864794;
ALTER TABLE ONLY public.hs_scholar_profile_organizationlocation DROP CONSTRAINT organization_id_refs_id_902d1e8d;
ALTER TABLE ONLY public.hs_scholar_profile_organizationphone DROP CONSTRAINT organization_id_refs_id_3dc2b44d;
ALTER TABLE ONLY public.hs_party_organization DROP CONSTRAINT "organizationType_id_refs_code_f5cc1b06";
ALTER TABLE ONLY public.generic_assignedkeyword DROP CONSTRAINT keyword_id_refs_id_aa70ce50;
ALTER TABLE ONLY public.djcelery_periodictask DROP CONSTRAINT interval_id_refs_id_1829f358;
ALTER TABLE ONLY public.hs_party_externalorgidentifier DROP CONSTRAINT "identifierName_id_refs_code_fbc35c1f";
ALTER TABLE ONLY public.hs_party_personexternalidentifier DROP CONSTRAINT "identifierName_id_refs_code_d53ad41b";
ALTER TABLE ONLY public.theme_iconbox DROP CONSTRAINT homepage_id_refs_page_ptr_id_f766bdfd;
ALTER TABLE ONLY public.hs_scholar_profile_scholargroup DROP CONSTRAINT group_ptr_id_refs_id_5deda983;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT group_id_refs_id_f4b32aac;
ALTER TABLE ONLY public.hs_core_genericresource_view_groups DROP CONSTRAINT group_id_refs_id_2bf6790f;
ALTER TABLE ONLY public.hs_core_groupownership DROP CONSTRAINT group_id_refs_id_07cb9889;
ALTER TABLE ONLY public.hs_core_genericresource_owners DROP CONSTRAINT genericresource_id_refs_page_ptr_id_f3be5566;
ALTER TABLE ONLY public.hs_core_genericresource_view_users DROP CONSTRAINT genericresource_id_refs_page_ptr_id_8ba7d05f;
ALTER TABLE ONLY public.hs_core_genericresource_edit_users DROP CONSTRAINT genericresource_id_refs_page_ptr_id_2d0a4979;
ALTER TABLE ONLY public.hs_core_genericresource_view_groups DROP CONSTRAINT genericresource_id_refs_page_ptr_id_1b325f2a;
ALTER TABLE ONLY public.hs_core_genericresource_edit_groups DROP CONSTRAINT genericresource_id_refs_page_ptr_id_063888a3;
ALTER TABLE ONLY public.galleries_galleryimage DROP CONSTRAINT gallery_id_refs_page_ptr_id_d6457fc6;
ALTER TABLE ONLY public.ga_irods_rodsenvironment DROP CONSTRAINT ga_irods_rodsenvironment_owner_id_fkey;
ALTER TABLE ONLY public.blog_blogpost_related_posts DROP CONSTRAINT from_blogpost_id_refs_id_6404941b;
ALTER TABLE ONLY public.forms_field DROP CONSTRAINT form_id_refs_page_ptr_id_5a752766;
ALTER TABLE ONLY public.forms_formentry DROP CONSTRAINT form_id_refs_page_ptr_id_4d605921;
ALTER TABLE ONLY public.ga_resources_relatedresource DROP CONSTRAINT foreign_resource_id_refs_page_ptr_id_f3121e9c;
ALTER TABLE ONLY public.hs_scholar_profile_scholarexternalidentifiers DROP CONSTRAINT externalidentifiers_ptr_id_refs_id_53f620d2;
ALTER TABLE ONLY public.forms_fieldentry DROP CONSTRAINT entry_id_refs_id_e329b086;
ALTER TABLE ONLY public.hs_party_organizationemail DROP CONSTRAINT email_type_id_refs_code_d463e90b;
ALTER TABLE ONLY public.hs_party_personemail DROP CONSTRAINT email_type_id_refs_code_56e785f9;
ALTER TABLE ONLY public.django_irods_rodsenvironment DROP CONSTRAINT django_irods_rodsenvironment_owner_id_fkey;
ALTER TABLE ONLY public.django_comments DROP CONSTRAINT django_comments_site_id_fkey;
ALTER TABLE ONLY public.django_comments DROP CONSTRAINT django_comments_content_type_id_fkey;
ALTER TABLE ONLY public.django_comment_flags DROP CONSTRAINT django_comment_flags_user_id_fkey;
ALTER TABLE ONLY public.django_comment_flags DROP CONSTRAINT django_comment_flags_comment_id_fkey;
ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_content_type_id_fkey;
ALTER TABLE ONLY public.hs_scholar_profile_scholar DROP CONSTRAINT demographics_id_refs_id_14c866dc;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT default_style_id_refs_page_ptr_id_1538365b;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT data_resource_id_refs_page_ptr_id_e2b8544b;
ALTER TABLE ONLY public.ga_resources_orderedresource DROP CONSTRAINT data_resource_id_refs_page_ptr_id_a59a4665;
ALTER TABLE ONLY public.djcelery_periodictask DROP CONSTRAINT crontab_id_refs_id_286da0d1;
ALTER TABLE ONLY public.hs_scholar_profile_scholargroup DROP CONSTRAINT "createdBy_id_refs_person_ptr_id_24851b27";
ALTER TABLE ONLY public.hs_scholar_profile_userdemographics DROP CONSTRAINT country_id_refs_id_7a53f3f7;
ALTER TABLE ONLY public.dublincore_qualifieddublincoreelement DROP CONSTRAINT content_type_id_refs_id_fc6222af;
ALTER TABLE ONLY public.hs_core_rights DROP CONSTRAINT content_type_id_refs_id_f2470641;
ALTER TABLE ONLY public.hs_core_creator DROP CONSTRAINT content_type_id_refs_id_db605579;
ALTER TABLE ONLY public.auth_permission DROP CONSTRAINT content_type_id_refs_id_d043b34a;
ALTER TABLE ONLY public.hs_core_bags DROP CONSTRAINT content_type_id_refs_id_c88d0ee7;
ALTER TABLE ONLY public.hs_core_format DROP CONSTRAINT content_type_id_refs_id_c639bc3f;
ALTER TABLE ONLY public.hs_core_description DROP CONSTRAINT content_type_id_refs_id_c5f70efd;
ALTER TABLE ONLY public.generic_assignedkeyword DROP CONSTRAINT content_type_id_refs_id_c36d959c;
ALTER TABLE ONLY public.hs_core_coverage DROP CONSTRAINT content_type_id_refs_id_a73b225b;
ALTER TABLE ONLY public.hs_core_date DROP CONSTRAINT content_type_id_refs_id_a4717fc0;
ALTER TABLE ONLY public.hs_core_source DROP CONSTRAINT content_type_id_refs_id_9cf1fb54;
ALTER TABLE ONLY public.hs_core_identifier DROP CONSTRAINT content_type_id_refs_id_8af9db16;
ALTER TABLE ONLY public.hs_core_contributor DROP CONSTRAINT content_type_id_refs_id_7fb920c4;
ALTER TABLE ONLY public.hs_core_relation DROP CONSTRAINT content_type_id_refs_id_7b5f3840;
ALTER TABLE ONLY public.dublincore_qualifieddublincoreelementhistory DROP CONSTRAINT content_type_id_refs_id_7504b98d;
ALTER TABLE ONLY public.hs_core_resourcefile DROP CONSTRAINT content_type_id_refs_id_4285c85f;
ALTER TABLE ONLY public.hs_core_externalprofilelink DROP CONSTRAINT content_type_id_refs_id_408804a4;
ALTER TABLE ONLY public.hs_core_title DROP CONSTRAINT content_type_id_refs_id_2efc891d;
ALTER TABLE ONLY public.generic_rating DROP CONSTRAINT content_type_id_refs_id_1c638e93;
ALTER TABLE ONLY public.hs_core_language DROP CONSTRAINT content_type_id_refs_id_14a23aea;
ALTER TABLE ONLY public.hs_core_type DROP CONSTRAINT content_type_id_refs_id_0f7fd1d0;
ALTER TABLE ONLY public.hs_core_subject DROP CONSTRAINT content_type_id_refs_id_0dbe97eb;
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT content_type_id_refs_id_07d4acf0;
ALTER TABLE ONLY public.hs_core_publisher DROP CONSTRAINT content_type_id_refs_id_016474ea;
ALTER TABLE ONLY public.generic_threadedcomment DROP CONSTRAINT comment_ptr_id_refs_id_d4c241e5;
ALTER TABLE ONLY public.hs_scholar_profile_userdemographics DROP CONSTRAINT city_id_refs_id_19f81b19;
ALTER TABLE ONLY public.blog_blogpost_categories DROP CONSTRAINT blogpost_id_refs_id_6a2ad936;
ALTER TABLE ONLY public.blog_blogpost_categories DROP CONSTRAINT blogcategory_id_refs_id_91693b1c;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_permission_id_fkey;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_group_id_fkey;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_permission_id_fkey;
ALTER TABLE ONLY public.hs_party_organizationname DROP CONSTRAINT annotation_id_refs_code_8fed8f55;
ALTER TABLE ONLY public.hs_party_othername DROP CONSTRAINT annotation_id_refs_code_7baf2f4c;
ALTER TABLE ONLY public.hs_party_personlocation DROP CONSTRAINT address_type_id_refs_code_d0fdde8c;
ALTER TABLE ONLY public.hs_party_organizationlocation DROP CONSTRAINT address_type_id_refs_code_540b122d;
DROP INDEX public.theme_siteconfiguration_site_id;
DROP INDEX public.theme_iconbox_homepage_id;
DROP INDEX public.tastypie_apikey_key;
DROP INDEX public.pages_page_site_id;
DROP INDEX public.pages_page_parent_id;
DROP INDEX public.hs_scholar_profile_userkeywords_person_id;
DROP INDEX public.hs_scholar_profile_userdemographics_region_id;
DROP INDEX public.hs_scholar_profile_userdemographics_country_id;
DROP INDEX public.hs_scholar_profile_userdemographics_city_id;
DROP INDEX public.hs_scholar_profile_scholargroup_site_id;
DROP INDEX public.hs_scholar_profile_scholarexternalidentifiers_scholar_id;
DROP INDEX public.hs_scholar_profile_scholar_demographics_id;
DROP INDEX public.hs_scholar_profile_personphone_person_id;
DROP INDEX public.hs_scholar_profile_personlocation_person_id;
DROP INDEX public.hs_scholar_profile_personemail_person_id;
DROP INDEX public.hs_scholar_profile_person_site_id;
DROP INDEX public.hs_scholar_profile_othernames_persons_id;
DROP INDEX public.hs_scholar_profile_orgassociations_person_id;
DROP INDEX public.hs_scholar_profile_orgassociations_organization_id;
DROP INDEX public.hs_scholar_profile_organizationphone_organization_id;
DROP INDEX public.hs_scholar_profile_organizationlocation_organization_id;
DROP INDEX public.hs_scholar_profile_organizationemail_organization_id;
DROP INDEX public.hs_scholar_profile_organization_site_id;
DROP INDEX public."hs_scholar_profile_organization_parentOrganization_id";
DROP INDEX public.hs_scholar_profile_externalorgidentifiers_organization_id;
DROP INDEX public.hs_party_usercodelist_code_like;
DROP INDEX public.hs_party_phonecodelist_code_like;
DROP INDEX public.hs_party_personphone_phone_type_id_like;
DROP INDEX public.hs_party_personphone_phone_type_id;
DROP INDEX public.hs_party_personphone_person_id;
DROP INDEX public.hs_party_personlocation_person_id;
DROP INDEX public.hs_party_personlocation_address_type_id_like;
DROP INDEX public.hs_party_personlocation_address_type_id;
DROP INDEX public.hs_party_personexternalidentifier_person_id;
DROP INDEX public."hs_party_personexternalidentifier_identifierName_id_like";
DROP INDEX public."hs_party_personexternalidentifier_identifierName_id";
DROP INDEX public.hs_party_personemail_person_id;
DROP INDEX public.hs_party_personemail_email_type_id_like;
DROP INDEX public.hs_party_personemail_email_type_id;
DROP INDEX public.hs_party_person_site_id;
DROP INDEX public."hs_party_person_primaryOrganizationRecord_id";
DROP INDEX public.hs_party_othername_persons_id;
DROP INDEX public.hs_party_othername_annotation_id_like;
DROP INDEX public.hs_party_othername_annotation_id;
DROP INDEX public.hs_party_organizationphone_phone_type_id_like;
DROP INDEX public.hs_party_organizationphone_phone_type_id;
DROP INDEX public.hs_party_organizationphone_organization_id;
DROP INDEX public.hs_party_organizationname_organization_id;
DROP INDEX public.hs_party_organizationname_annotation_id_like;
DROP INDEX public.hs_party_organizationname_annotation_id;
DROP INDEX public.hs_party_organizationlocation_organization_id;
DROP INDEX public.hs_party_organizationlocation_address_type_id_like;
DROP INDEX public.hs_party_organizationlocation_address_type_id;
DROP INDEX public.hs_party_organizationemail_organization_id;
DROP INDEX public.hs_party_organizationemail_email_type_id_like;
DROP INDEX public.hs_party_organizationemail_email_type_id;
DROP INDEX public.hs_party_organizationcodelist_code_like;
DROP INDEX public.hs_party_organizationassociation_person_id;
DROP INDEX public.hs_party_organizationassociation_organization_id;
DROP INDEX public.hs_party_organization_site_id;
DROP INDEX public."hs_party_organization_parentOrganization_id";
DROP INDEX public."hs_party_organization_organizationType_id_like";
DROP INDEX public."hs_party_organization_organizationType_id";
DROP INDEX public.hs_party_namealiascodelist_code_like;
DROP INDEX public.hs_party_group_site_id;
DROP INDEX public.hs_party_externalorgidentifier_organization_id;
DROP INDEX public."hs_party_externalorgidentifier_identifierName_id_like";
DROP INDEX public."hs_party_externalorgidentifier_identifierName_id";
DROP INDEX public.hs_party_externalidentifiercodelist_code_like;
DROP INDEX public.hs_party_emailcodelist_code_like;
DROP INDEX public.hs_party_addresscodelist_code_like;
DROP INDEX public.hs_core_type_content_type_id;
DROP INDEX public.hs_core_title_content_type_id;
DROP INDEX public.hs_core_subject_content_type_id;
DROP INDEX public.hs_core_source_content_type_id;
DROP INDEX public.hs_core_rights_content_type_id;
DROP INDEX public.hs_core_resourcefile_content_type_id;
DROP INDEX public.hs_core_relation_content_type_id;
DROP INDEX public.hs_core_publisher_content_type_id;
DROP INDEX public.hs_core_language_content_type_id;
DROP INDEX public.hs_core_identifier_url_like;
DROP INDEX public.hs_core_identifier_content_type_id;
DROP INDEX public.hs_core_groupownership_owner_id;
DROP INDEX public.hs_core_groupownership_group_id;
DROP INDEX public.hs_core_genericresource_view_users_user_id;
DROP INDEX public.hs_core_genericresource_view_users_genericresource_id;
DROP INDEX public.hs_core_genericresource_view_groups_group_id;
DROP INDEX public.hs_core_genericresource_view_groups_genericresource_id;
DROP INDEX public.hs_core_genericresource_user_id;
DROP INDEX public.hs_core_genericresource_short_id_like;
DROP INDEX public.hs_core_genericresource_short_id;
DROP INDEX public.hs_core_genericresource_owners_user_id;
DROP INDEX public.hs_core_genericresource_owners_genericresource_id;
DROP INDEX public.hs_core_genericresource_last_changed_by_id;
DROP INDEX public.hs_core_genericresource_edit_users_user_id;
DROP INDEX public.hs_core_genericresource_edit_users_genericresource_id;
DROP INDEX public.hs_core_genericresource_edit_groups_user_id;
DROP INDEX public.hs_core_genericresource_edit_groups_genericresource_id;
DROP INDEX public.hs_core_genericresource_doi_like;
DROP INDEX public.hs_core_genericresource_doi;
DROP INDEX public.hs_core_genericresource_creator_id;
DROP INDEX public.hs_core_genericresource_content_type_id;
DROP INDEX public.hs_core_format_content_type_id;
DROP INDEX public.hs_core_externalprofilelink_content_type_id;
DROP INDEX public.hs_core_description_content_type_id;
DROP INDEX public.hs_core_date_content_type_id;
DROP INDEX public.hs_core_creator_content_type_id;
DROP INDEX public.hs_core_coverage_content_type_id;
DROP INDEX public.hs_core_contributor_content_type_id;
DROP INDEX public.hs_core_bags_timestamp;
DROP INDEX public.hs_core_bags_content_type_id;
DROP INDEX public.generic_threadedcomment_replied_to_id;
DROP INDEX public.generic_rating_user_id;
DROP INDEX public.generic_rating_content_type_id;
DROP INDEX public.generic_keyword_site_id;
DROP INDEX public.generic_assignedkeyword_keyword_id;
DROP INDEX public.generic_assignedkeyword_content_type_id;
DROP INDEX public.galleries_galleryimage_gallery_id;
DROP INDEX public.ga_resources_style_owner_id;
DROP INDEX public.ga_resources_renderedlayer_styles_style_id;
DROP INDEX public.ga_resources_renderedlayer_styles_renderedlayer_id;
DROP INDEX public.ga_resources_renderedlayer_owner_id;
DROP INDEX public.ga_resources_renderedlayer_default_style_id;
DROP INDEX public.ga_resources_renderedlayer_data_resource_id;
DROP INDEX public.ga_resources_relatedresource_foreign_resource_id;
DROP INDEX public.ga_resources_orderedresource_resource_group_id;
DROP INDEX public.ga_resources_orderedresource_data_resource_id;
DROP INDEX public.ga_resources_dataresource_owner_id;
DROP INDEX public.ga_resources_dataresource_next_refresh;
DROP INDEX public.ga_resources_dataresource_native_bounding_box_id;
DROP INDEX public.ga_resources_dataresource_bounding_box_id;
DROP INDEX public.ga_resources_catalogpage_owner_id;
DROP INDEX public.ga_irods_rodsenvironment_owner_id;
DROP INDEX public.forms_formentry_form_id;
DROP INDEX public.forms_fieldentry_entry_id;
DROP INDEX public.forms_field_form_id;
DROP INDEX public.dublincore_qualifieddublincoreelementhistory_qdce_id;
DROP INDEX public.dublincore_qualifieddublincoreelementhistory_content_type_id;
DROP INDEX public.dublincore_qualifieddublincoreelement_content_type_id;
DROP INDEX public.djcelery_workerstate_last_heartbeat;
DROP INDEX public.djcelery_workerstate_hostname_like;
DROP INDEX public.djcelery_taskstate_worker_id;
DROP INDEX public.djcelery_taskstate_tstamp;
DROP INDEX public.djcelery_taskstate_task_id_like;
DROP INDEX public.djcelery_taskstate_state_like;
DROP INDEX public.djcelery_taskstate_state;
DROP INDEX public.djcelery_taskstate_name_like;
DROP INDEX public.djcelery_taskstate_name;
DROP INDEX public.djcelery_taskstate_hidden;
DROP INDEX public.djcelery_periodictask_name_like;
DROP INDEX public.djcelery_periodictask_interval_id;
DROP INDEX public.djcelery_periodictask_crontab_id;
DROP INDEX public.django_session_session_key_like;
DROP INDEX public.django_session_expire_date;
DROP INDEX public.django_redirect_site_id;
DROP INDEX public.django_redirect_old_path_like;
DROP INDEX public.django_redirect_old_path;
DROP INDEX public.django_irods_rodsenvironment_owner_id;
DROP INDEX public.django_comments_user_id;
DROP INDEX public.django_comments_site_id;
DROP INDEX public.django_comments_content_type_id;
DROP INDEX public.django_comment_flags_user_id;
DROP INDEX public.django_comment_flags_flag_like;
DROP INDEX public.django_comment_flags_flag;
DROP INDEX public.django_comment_flags_comment_id;
DROP INDEX public.django_admin_log_user_id;
DROP INDEX public.django_admin_log_content_type_id;
DROP INDEX public.core_sitepermission_sites_sitepermission_id;
DROP INDEX public.core_sitepermission_sites_site_id;
DROP INDEX public.conf_setting_site_id;
DROP INDEX public.celery_tasksetmeta_taskset_id_like;
DROP INDEX public.celery_tasksetmeta_hidden;
DROP INDEX public.celery_taskmeta_task_id_like;
DROP INDEX public.celery_taskmeta_hidden;
DROP INDEX public.blog_blogpost_user_id;
DROP INDEX public.blog_blogpost_site_id;
DROP INDEX public.blog_blogpost_related_posts_to_blogpost_id;
DROP INDEX public.blog_blogpost_related_posts_from_blogpost_id;
DROP INDEX public.blog_blogpost_categories_blogpost_id;
DROP INDEX public.blog_blogpost_categories_blogcategory_id;
DROP INDEX public.blog_blogcategory_site_id;
DROP INDEX public.auth_user_username_like;
DROP INDEX public.auth_user_user_permissions_user_id;
DROP INDEX public.auth_user_user_permissions_permission_id;
DROP INDEX public.auth_user_groups_user_id;
DROP INDEX public.auth_user_groups_group_id;
DROP INDEX public.auth_permission_content_type_id;
DROP INDEX public.auth_group_permissions_permission_id;
DROP INDEX public.auth_group_permissions_group_id;
DROP INDEX public.auth_group_name_like;
ALTER TABLE ONLY public.theme_userprofile DROP CONSTRAINT theme_userprofile_user_id_key;
ALTER TABLE ONLY public.theme_userprofile DROP CONSTRAINT theme_userprofile_pkey;
ALTER TABLE ONLY public.theme_siteconfiguration DROP CONSTRAINT theme_siteconfiguration_pkey;
ALTER TABLE ONLY public.theme_iconbox DROP CONSTRAINT theme_iconbox_pkey;
ALTER TABLE ONLY public.theme_homepage DROP CONSTRAINT theme_homepage_pkey;
ALTER TABLE ONLY public.tastypie_apikey DROP CONSTRAINT tastypie_apikey_user_id_key;
ALTER TABLE ONLY public.tastypie_apikey DROP CONSTRAINT tastypie_apikey_pkey;
ALTER TABLE ONLY public.tastypie_apiaccess DROP CONSTRAINT tastypie_apiaccess_pkey;
ALTER TABLE ONLY public.south_migrationhistory DROP CONSTRAINT south_migrationhistory_pkey;
ALTER TABLE ONLY public.pages_page DROP CONSTRAINT pages_page_pkey;
ALTER TABLE ONLY public.pages_link DROP CONSTRAINT pages_link_pkey;
ALTER TABLE ONLY public.pages_richtextpage DROP CONSTRAINT pages_contentpage_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_userkeywords DROP CONSTRAINT hs_scholar_profile_userkeywords_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_userdemographics DROP CONSTRAINT hs_scholar_profile_userdemographics_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_scholargroup DROP CONSTRAINT hs_scholar_profile_scholargroup_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_scholargroup DROP CONSTRAINT "hs_scholar_profile_scholargroup_createdBy_id_key";
ALTER TABLE ONLY public.hs_scholar_profile_scholarexternalidentifiers DROP CONSTRAINT hs_scholar_profile_scholarexternalidentifiers_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_scholar DROP CONSTRAINT hs_scholar_profile_scholar_user_id_key;
ALTER TABLE ONLY public.hs_scholar_profile_scholar DROP CONSTRAINT hs_scholar_profile_scholar_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_region DROP CONSTRAINT hs_scholar_profile_region_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_personphone DROP CONSTRAINT hs_scholar_profile_personphone_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_personlocation DROP CONSTRAINT hs_scholar_profile_personlocation_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_personemail DROP CONSTRAINT hs_scholar_profile_personemail_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_person DROP CONSTRAINT hs_scholar_profile_person_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_othernames DROP CONSTRAINT hs_scholar_profile_othernames_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_orgassociations DROP CONSTRAINT hs_scholar_profile_orgassociations_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_organizationphone DROP CONSTRAINT hs_scholar_profile_organizationphone_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_organizationlocation DROP CONSTRAINT hs_scholar_profile_organizationlocation_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_organizationemail DROP CONSTRAINT hs_scholar_profile_organizationemail_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_organization DROP CONSTRAINT hs_scholar_profile_organization_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_externalorgidentifiers DROP CONSTRAINT hs_scholar_profile_externalorgidentifiers_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_externalidentifiers DROP CONSTRAINT hs_scholar_profile_externalidentifiers_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_country DROP CONSTRAINT hs_scholar_profile_country_pkey;
ALTER TABLE ONLY public.hs_scholar_profile_city DROP CONSTRAINT hs_scholar_profile_city_pkey;
ALTER TABLE ONLY public.hs_party_usercodelist DROP CONSTRAINT hs_party_usercodelist_pkey;
ALTER TABLE ONLY public.hs_party_region DROP CONSTRAINT hs_party_region_pkey;
ALTER TABLE ONLY public.hs_party_phonecodelist DROP CONSTRAINT hs_party_phonecodelist_pkey;
ALTER TABLE ONLY public.hs_party_personphone DROP CONSTRAINT hs_party_personphone_pkey;
ALTER TABLE ONLY public.hs_party_personlocation DROP CONSTRAINT hs_party_personlocation_pkey;
ALTER TABLE ONLY public.hs_party_personexternalidentifier DROP CONSTRAINT hs_party_personexternalidentifier_pkey;
ALTER TABLE ONLY public.hs_party_personemail DROP CONSTRAINT hs_party_personemail_pkey;
ALTER TABLE ONLY public.hs_party_person DROP CONSTRAINT hs_party_person_pkey;
ALTER TABLE ONLY public.hs_party_party DROP CONSTRAINT hs_party_party_pkey;
ALTER TABLE ONLY public.hs_party_othername DROP CONSTRAINT hs_party_othername_pkey;
ALTER TABLE ONLY public.hs_party_organizationphone DROP CONSTRAINT hs_party_organizationphone_pkey;
ALTER TABLE ONLY public.hs_party_organizationname DROP CONSTRAINT hs_party_organizationname_pkey;
ALTER TABLE ONLY public.hs_party_organizationlocation DROP CONSTRAINT hs_party_organizationlocation_pkey;
ALTER TABLE ONLY public.hs_party_organizationemail DROP CONSTRAINT hs_party_organizationemail_pkey;
ALTER TABLE ONLY public.hs_party_organizationcodelist DROP CONSTRAINT hs_party_organizationcodelist_pkey;
ALTER TABLE ONLY public.hs_party_organizationassociation DROP CONSTRAINT hs_party_organizationassociation_pkey;
ALTER TABLE ONLY public.hs_party_organization DROP CONSTRAINT hs_party_organization_pkey;
ALTER TABLE ONLY public.hs_party_namealiascodelist DROP CONSTRAINT hs_party_namealiascodelist_pkey;
ALTER TABLE ONLY public.hs_party_group DROP CONSTRAINT hs_party_group_pkey;
ALTER TABLE ONLY public.hs_party_externalorgidentifier DROP CONSTRAINT hs_party_externalorgidentifier_pkey;
ALTER TABLE ONLY public.hs_party_externalidentifiercodelist DROP CONSTRAINT hs_party_externalidentifiercodelist_pkey;
ALTER TABLE ONLY public.hs_party_emailcodelist DROP CONSTRAINT hs_party_emailcodelist_pkey;
ALTER TABLE ONLY public.hs_party_country DROP CONSTRAINT hs_party_country_pkey;
ALTER TABLE ONLY public.hs_party_city DROP CONSTRAINT hs_party_city_pkey;
ALTER TABLE ONLY public.hs_party_choicetype DROP CONSTRAINT hs_party_choicetype_pkey;
ALTER TABLE ONLY public.hs_party_addresscodelist DROP CONSTRAINT hs_party_addresscodelist_pkey;
ALTER TABLE ONLY public.hs_core_type DROP CONSTRAINT hs_core_type_pkey;
ALTER TABLE ONLY public.hs_core_type DROP CONSTRAINT hs_core_type_content_type_id_18ed89604613f1ed_uniq;
ALTER TABLE ONLY public.hs_core_title DROP CONSTRAINT hs_core_title_pkey;
ALTER TABLE ONLY public.hs_core_title DROP CONSTRAINT hs_core_title_content_type_id_558a1cad4b729d8a_uniq;
ALTER TABLE ONLY public.hs_core_subject DROP CONSTRAINT hs_core_subject_pkey;
ALTER TABLE ONLY public.hs_core_source DROP CONSTRAINT hs_core_source_pkey;
ALTER TABLE ONLY public.hs_core_rights DROP CONSTRAINT hs_core_rights_pkey;
ALTER TABLE ONLY public.hs_core_rights DROP CONSTRAINT hs_core_rights_content_type_id_ef5b26c774a3f32_uniq;
ALTER TABLE ONLY public.hs_core_resourcefile DROP CONSTRAINT hs_core_resourcefile_pkey;
ALTER TABLE ONLY public.hs_core_relation DROP CONSTRAINT hs_core_relation_pkey;
ALTER TABLE ONLY public.hs_core_publisher DROP CONSTRAINT hs_core_publisher_pkey;
ALTER TABLE ONLY public.hs_core_publisher DROP CONSTRAINT hs_core_publisher_content_type_id_1d402c032dd55330_uniq;
ALTER TABLE ONLY public.hs_core_language DROP CONSTRAINT hs_core_language_pkey;
ALTER TABLE ONLY public.hs_core_identifier DROP CONSTRAINT hs_core_identifier_url_key;
ALTER TABLE ONLY public.hs_core_identifier DROP CONSTRAINT hs_core_identifier_pkey;
ALTER TABLE ONLY public.hs_core_groupownership DROP CONSTRAINT hs_core_groupownership_pkey;
ALTER TABLE ONLY public.hs_core_genericresource_view_users DROP CONSTRAINT hs_core_genericresource_view_users_pkey;
ALTER TABLE ONLY public.hs_core_genericresource_view_groups DROP CONSTRAINT hs_core_genericresource_view_groups_pkey;
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT hs_core_genericresource_pkey;
ALTER TABLE ONLY public.hs_core_genericresource_owners DROP CONSTRAINT hs_core_genericresource_owners_pkey;
ALTER TABLE ONLY public.hs_core_genericresource_edit_users DROP CONSTRAINT hs_core_genericresource_edit_users_pkey;
ALTER TABLE ONLY public.hs_core_genericresource_edit_groups DROP CONSTRAINT hs_core_genericresource_edit_groups_pkey;
ALTER TABLE ONLY public.hs_core_genericresource_edit_users DROP CONSTRAINT hs_core_genericresourc_genericresource_id_65437b438fb7ae44_uniq;
ALTER TABLE ONLY public.hs_core_genericresource_view_users DROP CONSTRAINT hs_core_genericresourc_genericresource_id_38e78a60f4d4ff6f_uniq;
ALTER TABLE ONLY public.hs_core_genericresource_edit_groups DROP CONSTRAINT hs_core_genericresourc_genericresource_id_2f4e7822117b5a55_uniq;
ALTER TABLE ONLY public.hs_core_genericresource_owners DROP CONSTRAINT hs_core_genericresourc_genericresource_id_17ca1f2998d362d9_uniq;
ALTER TABLE ONLY public.hs_core_genericresource_view_groups DROP CONSTRAINT hs_core_genericresourc_genericresource_id_1066ca4ece8eaae9_uniq;
ALTER TABLE ONLY public.hs_core_format DROP CONSTRAINT hs_core_format_pkey;
ALTER TABLE ONLY public.hs_core_externalprofilelink DROP CONSTRAINT hs_core_externalprofilelink_type_58d89d5b73bb6a79_uniq;
ALTER TABLE ONLY public.hs_core_externalprofilelink DROP CONSTRAINT hs_core_externalprofilelink_pkey;
ALTER TABLE ONLY public.hs_core_description DROP CONSTRAINT hs_core_description_pkey;
ALTER TABLE ONLY public.hs_core_description DROP CONSTRAINT hs_core_description_content_type_id_101f8a6db2013e88_uniq;
ALTER TABLE ONLY public.hs_core_date DROP CONSTRAINT hs_core_date_pkey;
ALTER TABLE ONLY public.hs_core_creator DROP CONSTRAINT hs_core_creator_pkey;
ALTER TABLE ONLY public.hs_core_coverage DROP CONSTRAINT hs_core_coverage_pkey;
ALTER TABLE ONLY public.hs_core_coremetadata DROP CONSTRAINT hs_core_coremetadata_pkey;
ALTER TABLE ONLY public.hs_core_contributor DROP CONSTRAINT hs_core_contributor_pkey;
ALTER TABLE ONLY public.hs_core_bags DROP CONSTRAINT hs_core_bags_pkey;
ALTER TABLE ONLY public.generic_threadedcomment DROP CONSTRAINT generic_threadedcomment_pkey;
ALTER TABLE ONLY public.generic_rating DROP CONSTRAINT generic_rating_pkey;
ALTER TABLE ONLY public.generic_keyword DROP CONSTRAINT generic_keyword_pkey;
ALTER TABLE ONLY public.generic_assignedkeyword DROP CONSTRAINT generic_assignedkeyword_pkey;
ALTER TABLE ONLY public.galleries_galleryimage DROP CONSTRAINT galleries_galleryimage_pkey;
ALTER TABLE ONLY public.galleries_gallery DROP CONSTRAINT galleries_gallery_pkey;
ALTER TABLE ONLY public.ga_resources_style DROP CONSTRAINT ga_resources_style_pkey;
ALTER TABLE ONLY public.ga_resources_resourcegroup DROP CONSTRAINT ga_resources_resourcegroup_pkey;
ALTER TABLE ONLY public.ga_resources_renderedlayer_styles DROP CONSTRAINT ga_resources_renderedlayer_styles_pkey;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT ga_resources_renderedlayer_pkey;
ALTER TABLE ONLY public.ga_resources_renderedlayer_styles DROP CONSTRAINT ga_resources_renderedlay_renderedlayer_id_12fa6280828b775a_uniq;
ALTER TABLE ONLY public.ga_resources_relatedresource DROP CONSTRAINT ga_resources_relatedresource_pkey;
ALTER TABLE ONLY public.ga_resources_orderedresource DROP CONSTRAINT ga_resources_orderedresource_pkey;
ALTER TABLE ONLY public.ga_resources_dataresource DROP CONSTRAINT ga_resources_dataresource_pkey;
ALTER TABLE ONLY public.ga_resources_catalogpage DROP CONSTRAINT ga_resources_catalogpage_pkey;
ALTER TABLE ONLY public.ga_irods_rodsenvironment DROP CONSTRAINT ga_irods_rodsenvironment_pkey;
ALTER TABLE ONLY public.forms_formentry DROP CONSTRAINT forms_formentry_pkey;
ALTER TABLE ONLY public.forms_form DROP CONSTRAINT forms_form_pkey;
ALTER TABLE ONLY public.forms_fieldentry DROP CONSTRAINT forms_fieldentry_pkey;
ALTER TABLE ONLY public.forms_field DROP CONSTRAINT forms_field_pkey;
ALTER TABLE ONLY public.dublincore_qualifieddublincoreelementhistory DROP CONSTRAINT dublincore_qualifieddublincoreelementhistory_pkey;
ALTER TABLE ONLY public.dublincore_qualifieddublincoreelement DROP CONSTRAINT dublincore_qualifieddublincoreelement_pkey;
ALTER TABLE ONLY public.djcelery_workerstate DROP CONSTRAINT djcelery_workerstate_pkey;
ALTER TABLE ONLY public.djcelery_workerstate DROP CONSTRAINT djcelery_workerstate_hostname_key;
ALTER TABLE ONLY public.djcelery_taskstate DROP CONSTRAINT djcelery_taskstate_task_id_key;
ALTER TABLE ONLY public.djcelery_taskstate DROP CONSTRAINT djcelery_taskstate_pkey;
ALTER TABLE ONLY public.djcelery_periodictasks DROP CONSTRAINT djcelery_periodictasks_pkey;
ALTER TABLE ONLY public.djcelery_periodictask DROP CONSTRAINT djcelery_periodictask_pkey;
ALTER TABLE ONLY public.djcelery_periodictask DROP CONSTRAINT djcelery_periodictask_name_key;
ALTER TABLE ONLY public.djcelery_intervalschedule DROP CONSTRAINT djcelery_intervalschedule_pkey;
ALTER TABLE ONLY public.djcelery_crontabschedule DROP CONSTRAINT djcelery_crontabschedule_pkey;
ALTER TABLE ONLY public.django_site DROP CONSTRAINT django_site_pkey;
ALTER TABLE ONLY public.django_session DROP CONSTRAINT django_session_pkey;
ALTER TABLE ONLY public.django_redirect DROP CONSTRAINT django_redirect_site_id_old_path_key;
ALTER TABLE ONLY public.django_redirect DROP CONSTRAINT django_redirect_pkey;
ALTER TABLE ONLY public.django_irods_rodsenvironment DROP CONSTRAINT django_irods_rodsenvironment_pkey;
ALTER TABLE ONLY public.django_content_type DROP CONSTRAINT django_content_type_pkey;
ALTER TABLE ONLY public.django_content_type DROP CONSTRAINT django_content_type_app_label_model_key;
ALTER TABLE ONLY public.django_comments DROP CONSTRAINT django_comments_pkey;
ALTER TABLE ONLY public.django_comment_flags DROP CONSTRAINT django_comment_flags_user_id_comment_id_flag_key;
ALTER TABLE ONLY public.django_comment_flags DROP CONSTRAINT django_comment_flags_pkey;
ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_pkey;
ALTER TABLE ONLY public.core_sitepermission DROP CONSTRAINT core_sitepermission_user_id_key;
ALTER TABLE ONLY public.core_sitepermission_sites DROP CONSTRAINT core_sitepermission_sites_pkey;
ALTER TABLE ONLY public.core_sitepermission_sites DROP CONSTRAINT core_sitepermission_sit_sitepermission_id_31fc3b7b7e3badd5_uniq;
ALTER TABLE ONLY public.core_sitepermission DROP CONSTRAINT core_sitepermission_pkey;
ALTER TABLE ONLY public.conf_setting DROP CONSTRAINT conf_setting_pkey;
ALTER TABLE ONLY public.celery_tasksetmeta DROP CONSTRAINT celery_tasksetmeta_taskset_id_key;
ALTER TABLE ONLY public.celery_tasksetmeta DROP CONSTRAINT celery_tasksetmeta_pkey;
ALTER TABLE ONLY public.celery_taskmeta DROP CONSTRAINT celery_taskmeta_task_id_key;
ALTER TABLE ONLY public.celery_taskmeta DROP CONSTRAINT celery_taskmeta_pkey;
ALTER TABLE ONLY public.blog_blogpost_related_posts DROP CONSTRAINT blog_blogpost_related_posts_pkey;
ALTER TABLE ONLY public.blog_blogpost_related_posts DROP CONSTRAINT blog_blogpost_related_po_from_blogpost_id_3007eb9b6b16df8b_uniq;
ALTER TABLE ONLY public.blog_blogpost DROP CONSTRAINT blog_blogpost_pkey;
ALTER TABLE ONLY public.blog_blogpost_categories DROP CONSTRAINT blog_blogpost_categories_pkey;
ALTER TABLE ONLY public.blog_blogpost_categories DROP CONSTRAINT blog_blogpost_categories_blogpost_id_79f2a5569187bd14_uniq;
ALTER TABLE ONLY public.blog_blogcategory DROP CONSTRAINT blog_blogcategory_pkey;
ALTER TABLE ONLY public.auth_user DROP CONSTRAINT auth_user_username_key;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_user_id_permission_id_key;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_pkey;
ALTER TABLE ONLY public.auth_user DROP CONSTRAINT auth_user_pkey;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_user_id_group_id_key;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_pkey;
ALTER TABLE ONLY public.auth_permission DROP CONSTRAINT auth_permission_pkey;
ALTER TABLE ONLY public.auth_permission DROP CONSTRAINT auth_permission_content_type_id_codename_key;
ALTER TABLE ONLY public.auth_group DROP CONSTRAINT auth_group_pkey;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_pkey;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_group_id_permission_id_key;
ALTER TABLE ONLY public.auth_group DROP CONSTRAINT auth_group_name_key;
ALTER TABLE public.theme_userprofile ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.theme_siteconfiguration ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.theme_iconbox ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.tastypie_apikey ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.tastypie_apiaccess ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.south_migrationhistory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.pages_page ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_userkeywords ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_userdemographics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_region ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_personphone ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_personlocation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_personemail ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_person ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_othernames ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_orgassociations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_organizationphone ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_organizationlocation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_organizationemail ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_organization ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_externalorgidentifiers ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_externalidentifiers ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_country ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_scholar_profile_city ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_region ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_personphone ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_personlocation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_personexternalidentifier ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_personemail ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_party ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_othername ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_organizationphone ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_organizationname ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_organizationlocation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_organizationemail ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_organizationassociation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_externalorgidentifier ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_country ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_city ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_party_choicetype ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_type ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_title ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_subject ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_source ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_rights ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_resourcefile ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_relation ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_publisher ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_language ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_identifier ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_groupownership ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_genericresource_view_users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_genericresource_view_groups ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_genericresource_owners ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_genericresource_edit_users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_genericresource_edit_groups ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_format ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_externalprofilelink ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_description ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_date ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_creator ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_coverage ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_coremetadata ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_contributor ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_core_bags ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.generic_rating ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.generic_keyword ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.generic_assignedkeyword ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.galleries_galleryimage ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.ga_resources_renderedlayer_styles ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.ga_resources_orderedresource ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.ga_irods_rodsenvironment ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.forms_formentry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.forms_fieldentry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.forms_field ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.dublincore_qualifieddublincoreelementhistory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.dublincore_qualifieddublincoreelement ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.djcelery_workerstate ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.djcelery_taskstate ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.djcelery_periodictask ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.djcelery_intervalschedule ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.djcelery_crontabschedule ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_site ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_redirect ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_irods_rodsenvironment ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_content_type ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_comments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_comment_flags ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_admin_log ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.core_sitepermission_sites ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.core_sitepermission ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.conf_setting ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.celery_tasksetmeta ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.celery_taskmeta ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.blog_blogpost_related_posts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.blog_blogpost_categories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.blog_blogpost ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.blog_blogcategory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_user_groups ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_user ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_permission ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_group_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.auth_group ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.theme_userprofile_id_seq;
DROP TABLE public.theme_userprofile;
DROP SEQUENCE public.theme_siteconfiguration_id_seq;
DROP TABLE public.theme_siteconfiguration;
DROP SEQUENCE public.theme_iconbox_id_seq;
DROP TABLE public.theme_iconbox;
DROP TABLE public.theme_homepage;
DROP SEQUENCE public.tastypie_apikey_id_seq;
DROP TABLE public.tastypie_apikey;
DROP SEQUENCE public.tastypie_apiaccess_id_seq;
DROP TABLE public.tastypie_apiaccess;
DROP SEQUENCE public.south_migrationhistory_id_seq;
DROP TABLE public.south_migrationhistory;
DROP TABLE public.pages_richtextpage;
DROP SEQUENCE public.pages_page_id_seq;
DROP TABLE public.pages_page;
DROP TABLE public.pages_link;
DROP SEQUENCE public.hs_scholar_profile_userkeywords_id_seq;
DROP TABLE public.hs_scholar_profile_userkeywords;
DROP SEQUENCE public.hs_scholar_profile_userdemographics_id_seq;
DROP TABLE public.hs_scholar_profile_userdemographics;
DROP TABLE public.hs_scholar_profile_scholargroup;
DROP TABLE public.hs_scholar_profile_scholarexternalidentifiers;
DROP TABLE public.hs_scholar_profile_scholar;
DROP SEQUENCE public.hs_scholar_profile_region_id_seq;
DROP TABLE public.hs_scholar_profile_region;
DROP SEQUENCE public.hs_scholar_profile_personphone_id_seq;
DROP TABLE public.hs_scholar_profile_personphone;
DROP SEQUENCE public.hs_scholar_profile_personlocation_id_seq;
DROP TABLE public.hs_scholar_profile_personlocation;
DROP SEQUENCE public.hs_scholar_profile_personemail_id_seq;
DROP TABLE public.hs_scholar_profile_personemail;
DROP SEQUENCE public.hs_scholar_profile_person_id_seq;
DROP TABLE public.hs_scholar_profile_person;
DROP SEQUENCE public.hs_scholar_profile_othernames_id_seq;
DROP TABLE public.hs_scholar_profile_othernames;
DROP SEQUENCE public.hs_scholar_profile_orgassociations_id_seq;
DROP TABLE public.hs_scholar_profile_orgassociations;
DROP SEQUENCE public.hs_scholar_profile_organizationphone_id_seq;
DROP TABLE public.hs_scholar_profile_organizationphone;
DROP SEQUENCE public.hs_scholar_profile_organizationlocation_id_seq;
DROP TABLE public.hs_scholar_profile_organizationlocation;
DROP SEQUENCE public.hs_scholar_profile_organizationemail_id_seq;
DROP TABLE public.hs_scholar_profile_organizationemail;
DROP SEQUENCE public.hs_scholar_profile_organization_id_seq;
DROP TABLE public.hs_scholar_profile_organization;
DROP SEQUENCE public.hs_scholar_profile_externalorgidentifiers_id_seq;
DROP TABLE public.hs_scholar_profile_externalorgidentifiers;
DROP SEQUENCE public.hs_scholar_profile_externalidentifiers_id_seq;
DROP TABLE public.hs_scholar_profile_externalidentifiers;
DROP SEQUENCE public.hs_scholar_profile_country_id_seq;
DROP TABLE public.hs_scholar_profile_country;
DROP SEQUENCE public.hs_scholar_profile_city_id_seq;
DROP TABLE public.hs_scholar_profile_city;
DROP TABLE public.hs_party_usercodelist;
DROP SEQUENCE public.hs_party_region_id_seq;
DROP TABLE public.hs_party_region;
DROP TABLE public.hs_party_phonecodelist;
DROP SEQUENCE public.hs_party_personphone_id_seq;
DROP TABLE public.hs_party_personphone;
DROP SEQUENCE public.hs_party_personlocation_id_seq;
DROP TABLE public.hs_party_personlocation;
DROP SEQUENCE public.hs_party_personexternalidentifier_id_seq;
DROP TABLE public.hs_party_personexternalidentifier;
DROP SEQUENCE public.hs_party_personemail_id_seq;
DROP TABLE public.hs_party_personemail;
DROP TABLE public.hs_party_person;
DROP SEQUENCE public.hs_party_party_id_seq;
DROP TABLE public.hs_party_party;
DROP SEQUENCE public.hs_party_othername_id_seq;
DROP TABLE public.hs_party_othername;
DROP SEQUENCE public.hs_party_organizationphone_id_seq;
DROP TABLE public.hs_party_organizationphone;
DROP SEQUENCE public.hs_party_organizationname_id_seq;
DROP TABLE public.hs_party_organizationname;
DROP SEQUENCE public.hs_party_organizationlocation_id_seq;
DROP TABLE public.hs_party_organizationlocation;
DROP SEQUENCE public.hs_party_organizationemail_id_seq;
DROP TABLE public.hs_party_organizationemail;
DROP TABLE public.hs_party_organizationcodelist;
DROP SEQUENCE public.hs_party_organizationassociation_id_seq;
DROP TABLE public.hs_party_organizationassociation;
DROP TABLE public.hs_party_organization;
DROP TABLE public.hs_party_namealiascodelist;
DROP TABLE public.hs_party_group;
DROP SEQUENCE public.hs_party_externalorgidentifier_id_seq;
DROP TABLE public.hs_party_externalorgidentifier;
DROP TABLE public.hs_party_externalidentifiercodelist;
DROP TABLE public.hs_party_emailcodelist;
DROP SEQUENCE public.hs_party_country_id_seq;
DROP TABLE public.hs_party_country;
DROP SEQUENCE public.hs_party_city_id_seq;
DROP TABLE public.hs_party_city;
DROP SEQUENCE public.hs_party_choicetype_id_seq;
DROP TABLE public.hs_party_choicetype;
DROP TABLE public.hs_party_addresscodelist;
DROP SEQUENCE public.hs_core_type_id_seq;
DROP TABLE public.hs_core_type;
DROP SEQUENCE public.hs_core_title_id_seq;
DROP TABLE public.hs_core_title;
DROP SEQUENCE public.hs_core_subject_id_seq;
DROP TABLE public.hs_core_subject;
DROP SEQUENCE public.hs_core_source_id_seq;
DROP TABLE public.hs_core_source;
DROP SEQUENCE public.hs_core_rights_id_seq;
DROP TABLE public.hs_core_rights;
DROP SEQUENCE public.hs_core_resourcefile_id_seq;
DROP TABLE public.hs_core_resourcefile;
DROP SEQUENCE public.hs_core_relation_id_seq;
DROP TABLE public.hs_core_relation;
DROP SEQUENCE public.hs_core_publisher_id_seq;
DROP TABLE public.hs_core_publisher;
DROP SEQUENCE public.hs_core_language_id_seq;
DROP TABLE public.hs_core_language;
DROP SEQUENCE public.hs_core_identifier_id_seq;
DROP TABLE public.hs_core_identifier;
DROP SEQUENCE public.hs_core_groupownership_id_seq;
DROP TABLE public.hs_core_groupownership;
DROP SEQUENCE public.hs_core_genericresource_view_users_id_seq;
DROP TABLE public.hs_core_genericresource_view_users;
DROP SEQUENCE public.hs_core_genericresource_view_groups_id_seq;
DROP TABLE public.hs_core_genericresource_view_groups;
DROP SEQUENCE public.hs_core_genericresource_owners_id_seq;
DROP TABLE public.hs_core_genericresource_owners;
DROP SEQUENCE public.hs_core_genericresource_edit_users_id_seq;
DROP TABLE public.hs_core_genericresource_edit_users;
DROP SEQUENCE public.hs_core_genericresource_edit_groups_id_seq;
DROP TABLE public.hs_core_genericresource_edit_groups;
DROP TABLE public.hs_core_genericresource;
DROP SEQUENCE public.hs_core_format_id_seq;
DROP TABLE public.hs_core_format;
DROP SEQUENCE public.hs_core_externalprofilelink_id_seq;
DROP TABLE public.hs_core_externalprofilelink;
DROP SEQUENCE public.hs_core_description_id_seq;
DROP TABLE public.hs_core_description;
DROP SEQUENCE public.hs_core_date_id_seq;
DROP TABLE public.hs_core_date;
DROP SEQUENCE public.hs_core_creator_id_seq;
DROP TABLE public.hs_core_creator;
DROP SEQUENCE public.hs_core_coverage_id_seq;
DROP TABLE public.hs_core_coverage;
DROP SEQUENCE public.hs_core_coremetadata_id_seq;
DROP TABLE public.hs_core_coremetadata;
DROP SEQUENCE public.hs_core_contributor_id_seq;
DROP TABLE public.hs_core_contributor;
DROP SEQUENCE public.hs_core_bags_id_seq;
DROP TABLE public.hs_core_bags;
DROP TABLE public.generic_threadedcomment;
DROP SEQUENCE public.generic_rating_id_seq;
DROP TABLE public.generic_rating;
DROP SEQUENCE public.generic_keyword_id_seq;
DROP TABLE public.generic_keyword;
DROP SEQUENCE public.generic_assignedkeyword_id_seq;
DROP TABLE public.generic_assignedkeyword;
DROP SEQUENCE public.galleries_galleryimage_id_seq;
DROP TABLE public.galleries_galleryimage;
DROP TABLE public.galleries_gallery;
DROP TABLE public.ga_resources_style;
DROP TABLE public.ga_resources_resourcegroup;
DROP SEQUENCE public.ga_resources_renderedlayer_styles_id_seq;
DROP TABLE public.ga_resources_renderedlayer_styles;
DROP TABLE public.ga_resources_renderedlayer;
DROP TABLE public.ga_resources_relatedresource;
DROP SEQUENCE public.ga_resources_orderedresource_id_seq;
DROP TABLE public.ga_resources_orderedresource;
DROP TABLE public.ga_resources_dataresource;
DROP TABLE public.ga_resources_catalogpage;
DROP SEQUENCE public.ga_irods_rodsenvironment_id_seq;
DROP TABLE public.ga_irods_rodsenvironment;
DROP SEQUENCE public.forms_formentry_id_seq;
DROP TABLE public.forms_formentry;
DROP TABLE public.forms_form;
DROP SEQUENCE public.forms_fieldentry_id_seq;
DROP TABLE public.forms_fieldentry;
DROP SEQUENCE public.forms_field_id_seq;
DROP TABLE public.forms_field;
DROP SEQUENCE public.dublincore_qualifieddublincoreelementhistory_id_seq;
DROP TABLE public.dublincore_qualifieddublincoreelementhistory;
DROP SEQUENCE public.dublincore_qualifieddublincoreelement_id_seq;
DROP TABLE public.dublincore_qualifieddublincoreelement;
DROP SEQUENCE public.djcelery_workerstate_id_seq;
DROP TABLE public.djcelery_workerstate;
DROP SEQUENCE public.djcelery_taskstate_id_seq;
DROP TABLE public.djcelery_taskstate;
DROP TABLE public.djcelery_periodictasks;
DROP SEQUENCE public.djcelery_periodictask_id_seq;
DROP TABLE public.djcelery_periodictask;
DROP SEQUENCE public.djcelery_intervalschedule_id_seq;
DROP TABLE public.djcelery_intervalschedule;
DROP SEQUENCE public.djcelery_crontabschedule_id_seq;
DROP TABLE public.djcelery_crontabschedule;
DROP SEQUENCE public.django_site_id_seq;
DROP TABLE public.django_site;
DROP TABLE public.django_session;
DROP SEQUENCE public.django_redirect_id_seq;
DROP TABLE public.django_redirect;
DROP SEQUENCE public.django_irods_rodsenvironment_id_seq;
DROP TABLE public.django_irods_rodsenvironment;
DROP SEQUENCE public.django_content_type_id_seq;
DROP TABLE public.django_content_type;
DROP SEQUENCE public.django_comments_id_seq;
DROP TABLE public.django_comments;
DROP SEQUENCE public.django_comment_flags_id_seq;
DROP TABLE public.django_comment_flags;
DROP SEQUENCE public.django_admin_log_id_seq;
DROP TABLE public.django_admin_log;
DROP SEQUENCE public.core_sitepermission_sites_id_seq;
DROP TABLE public.core_sitepermission_sites;
DROP SEQUENCE public.core_sitepermission_id_seq;
DROP TABLE public.core_sitepermission;
DROP SEQUENCE public.conf_setting_id_seq;
DROP TABLE public.conf_setting;
DROP SEQUENCE public.celery_tasksetmeta_id_seq;
DROP TABLE public.celery_tasksetmeta;
DROP SEQUENCE public.celery_taskmeta_id_seq;
DROP TABLE public.celery_taskmeta;
DROP SEQUENCE public.blog_blogpost_related_posts_id_seq;
DROP TABLE public.blog_blogpost_related_posts;
DROP SEQUENCE public.blog_blogpost_id_seq;
DROP SEQUENCE public.blog_blogpost_categories_id_seq;
DROP TABLE public.blog_blogpost_categories;
DROP TABLE public.blog_blogpost;
DROP SEQUENCE public.blog_blogcategory_id_seq;
DROP TABLE public.blog_blogcategory;
DROP SEQUENCE public.auth_user_user_permissions_id_seq;
DROP TABLE public.auth_user_user_permissions;
DROP SEQUENCE public.auth_user_id_seq;
DROP SEQUENCE public.auth_user_groups_id_seq;
DROP TABLE public.auth_user_groups;
DROP TABLE public.auth_user;
DROP SEQUENCE public.auth_permission_id_seq;
DROP TABLE public.auth_permission;
DROP SEQUENCE public.auth_group_permissions_id_seq;
DROP TABLE public.auth_group_permissions;
DROP SEQUENCE public.auth_group_id_seq;
DROP TABLE public.auth_group;
DROP EXTENSION postgis;
DROP EXTENSION plpgsql;
DROP SCHEMA public;
--
-- Name: postgres; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry, geography, and raster spatial types and functions';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_group (
    id integer NOT NULL,
    name character varying(80) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_id_seq OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE auth_group_id_seq OWNED BY auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_permissions_id_seq OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE auth_group_permissions_id_seq OWNED BY auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_permission (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_permission_id_seq OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE auth_permission_id_seq OWNED BY auth_permission.id;


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone NOT NULL,
    is_superuser boolean NOT NULL,
    username character varying(30) NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    email character varying(75) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO postgres;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO postgres;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_groups_id_seq OWNER TO postgres;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE auth_user_groups_id_seq OWNED BY auth_user_groups.id;


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_id_seq OWNER TO postgres;

--
-- Name: auth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE auth_user_id_seq OWNED BY auth_user.id;


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_user_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO postgres;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_user_user_permissions_id_seq OWNER TO postgres;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE auth_user_user_permissions_id_seq OWNED BY auth_user_user_permissions.id;


--
-- Name: blog_blogcategory; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE blog_blogcategory (
    slug character varying(2000),
    id integer NOT NULL,
    title character varying(500) NOT NULL,
    site_id integer NOT NULL
);


ALTER TABLE public.blog_blogcategory OWNER TO postgres;

--
-- Name: blog_blogcategory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE blog_blogcategory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.blog_blogcategory_id_seq OWNER TO postgres;

--
-- Name: blog_blogcategory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE blog_blogcategory_id_seq OWNED BY blog_blogcategory.id;


--
-- Name: blog_blogpost; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE blog_blogpost (
    status integer NOT NULL,
    description text NOT NULL,
    title character varying(500) NOT NULL,
    short_url character varying(200),
    id integer NOT NULL,
    content text NOT NULL,
    expiry_date timestamp with time zone,
    publish_date timestamp with time zone,
    user_id integer NOT NULL,
    slug character varying(2000),
    comments_count integer NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    rating_average double precision NOT NULL,
    rating_count integer NOT NULL,
    allow_comments boolean NOT NULL,
    featured_image character varying(255),
    gen_description boolean NOT NULL,
    _meta_title character varying(500),
    in_sitemap boolean NOT NULL,
    rating_sum integer NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone
);


ALTER TABLE public.blog_blogpost OWNER TO postgres;

--
-- Name: blog_blogpost_categories; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE blog_blogpost_categories (
    id integer NOT NULL,
    blogpost_id integer NOT NULL,
    blogcategory_id integer NOT NULL
);


ALTER TABLE public.blog_blogpost_categories OWNER TO postgres;

--
-- Name: blog_blogpost_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE blog_blogpost_categories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.blog_blogpost_categories_id_seq OWNER TO postgres;

--
-- Name: blog_blogpost_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE blog_blogpost_categories_id_seq OWNED BY blog_blogpost_categories.id;


--
-- Name: blog_blogpost_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE blog_blogpost_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.blog_blogpost_id_seq OWNER TO postgres;

--
-- Name: blog_blogpost_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE blog_blogpost_id_seq OWNED BY blog_blogpost.id;


--
-- Name: blog_blogpost_related_posts; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE blog_blogpost_related_posts (
    id integer NOT NULL,
    from_blogpost_id integer NOT NULL,
    to_blogpost_id integer NOT NULL
);


ALTER TABLE public.blog_blogpost_related_posts OWNER TO postgres;

--
-- Name: blog_blogpost_related_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE blog_blogpost_related_posts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.blog_blogpost_related_posts_id_seq OWNER TO postgres;

--
-- Name: blog_blogpost_related_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE blog_blogpost_related_posts_id_seq OWNED BY blog_blogpost_related_posts.id;


--
-- Name: celery_taskmeta; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE celery_taskmeta (
    id integer NOT NULL,
    task_id character varying(255) NOT NULL,
    status character varying(50) NOT NULL,
    result text,
    date_done timestamp with time zone NOT NULL,
    traceback text,
    hidden boolean NOT NULL,
    meta text
);


ALTER TABLE public.celery_taskmeta OWNER TO postgres;

--
-- Name: celery_taskmeta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE celery_taskmeta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.celery_taskmeta_id_seq OWNER TO postgres;

--
-- Name: celery_taskmeta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE celery_taskmeta_id_seq OWNED BY celery_taskmeta.id;


--
-- Name: celery_tasksetmeta; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE celery_tasksetmeta (
    id integer NOT NULL,
    taskset_id character varying(255) NOT NULL,
    result text NOT NULL,
    date_done timestamp with time zone NOT NULL,
    hidden boolean NOT NULL
);


ALTER TABLE public.celery_tasksetmeta OWNER TO postgres;

--
-- Name: celery_tasksetmeta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE celery_tasksetmeta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.celery_tasksetmeta_id_seq OWNER TO postgres;

--
-- Name: celery_tasksetmeta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE celery_tasksetmeta_id_seq OWNED BY celery_tasksetmeta.id;


--
-- Name: conf_setting; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE conf_setting (
    id integer NOT NULL,
    value character varying(2000) NOT NULL,
    name character varying(50) NOT NULL,
    site_id integer NOT NULL
);


ALTER TABLE public.conf_setting OWNER TO postgres;

--
-- Name: conf_setting_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE conf_setting_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.conf_setting_id_seq OWNER TO postgres;

--
-- Name: conf_setting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE conf_setting_id_seq OWNED BY conf_setting.id;


--
-- Name: core_sitepermission; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE core_sitepermission (
    id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.core_sitepermission OWNER TO postgres;

--
-- Name: core_sitepermission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE core_sitepermission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.core_sitepermission_id_seq OWNER TO postgres;

--
-- Name: core_sitepermission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE core_sitepermission_id_seq OWNED BY core_sitepermission.id;


--
-- Name: core_sitepermission_sites; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE core_sitepermission_sites (
    id integer NOT NULL,
    sitepermission_id integer NOT NULL,
    site_id integer NOT NULL
);


ALTER TABLE public.core_sitepermission_sites OWNER TO postgres;

--
-- Name: core_sitepermission_sites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE core_sitepermission_sites_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.core_sitepermission_sites_id_seq OWNER TO postgres;

--
-- Name: core_sitepermission_sites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE core_sitepermission_sites_id_seq OWNED BY core_sitepermission_sites.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    user_id integer NOT NULL,
    content_type_id integer,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_admin_log_id_seq OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_admin_log_id_seq OWNED BY django_admin_log.id;


--
-- Name: django_comment_flags; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_comment_flags (
    id integer NOT NULL,
    user_id integer NOT NULL,
    comment_id integer NOT NULL,
    flag character varying(30) NOT NULL,
    flag_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_comment_flags OWNER TO postgres;

--
-- Name: django_comment_flags_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_comment_flags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_comment_flags_id_seq OWNER TO postgres;

--
-- Name: django_comment_flags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_comment_flags_id_seq OWNED BY django_comment_flags.id;


--
-- Name: django_comments; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_comments (
    id integer NOT NULL,
    content_type_id integer NOT NULL,
    object_pk text NOT NULL,
    site_id integer NOT NULL,
    user_id integer,
    user_name character varying(50) NOT NULL,
    user_email character varying(75) NOT NULL,
    user_url character varying(200) NOT NULL,
    comment text NOT NULL,
    submit_date timestamp with time zone NOT NULL,
    ip_address inet,
    is_public boolean NOT NULL,
    is_removed boolean NOT NULL
);


ALTER TABLE public.django_comments OWNER TO postgres;

--
-- Name: django_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_comments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_comments_id_seq OWNER TO postgres;

--
-- Name: django_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_comments_id_seq OWNED BY django_comments.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_content_type (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_content_type_id_seq OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id;


--
-- Name: django_irods_rodsenvironment; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_irods_rodsenvironment (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    host character varying(255) NOT NULL,
    port integer NOT NULL,
    def_res character varying(255) NOT NULL,
    home_coll character varying(255) NOT NULL,
    cwd text NOT NULL,
    username character varying(255) NOT NULL,
    zone text NOT NULL,
    auth text NOT NULL
);


ALTER TABLE public.django_irods_rodsenvironment OWNER TO postgres;

--
-- Name: django_irods_rodsenvironment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_irods_rodsenvironment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_irods_rodsenvironment_id_seq OWNER TO postgres;

--
-- Name: django_irods_rodsenvironment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_irods_rodsenvironment_id_seq OWNED BY django_irods_rodsenvironment.id;


--
-- Name: django_redirect; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_redirect (
    id integer NOT NULL,
    site_id integer NOT NULL,
    old_path character varying(200) NOT NULL,
    new_path character varying(200) NOT NULL
);


ALTER TABLE public.django_redirect OWNER TO postgres;

--
-- Name: django_redirect_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_redirect_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_redirect_id_seq OWNER TO postgres;

--
-- Name: django_redirect_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_redirect_id_seq OWNED BY django_redirect.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: django_site; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_site (
    id integer NOT NULL,
    domain character varying(100) NOT NULL,
    name character varying(50) NOT NULL
);


ALTER TABLE public.django_site OWNER TO postgres;

--
-- Name: django_site_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_site_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_site_id_seq OWNER TO postgres;

--
-- Name: django_site_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_site_id_seq OWNED BY django_site.id;


--
-- Name: djcelery_crontabschedule; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE djcelery_crontabschedule (
    id integer NOT NULL,
    minute character varying(64) NOT NULL,
    hour character varying(64) NOT NULL,
    day_of_week character varying(64) NOT NULL,
    day_of_month character varying(64) NOT NULL,
    month_of_year character varying(64) NOT NULL
);


ALTER TABLE public.djcelery_crontabschedule OWNER TO postgres;

--
-- Name: djcelery_crontabschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE djcelery_crontabschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.djcelery_crontabschedule_id_seq OWNER TO postgres;

--
-- Name: djcelery_crontabschedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE djcelery_crontabschedule_id_seq OWNED BY djcelery_crontabschedule.id;


--
-- Name: djcelery_intervalschedule; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE djcelery_intervalschedule (
    id integer NOT NULL,
    every integer NOT NULL,
    period character varying(24) NOT NULL
);


ALTER TABLE public.djcelery_intervalschedule OWNER TO postgres;

--
-- Name: djcelery_intervalschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE djcelery_intervalschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.djcelery_intervalschedule_id_seq OWNER TO postgres;

--
-- Name: djcelery_intervalschedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE djcelery_intervalschedule_id_seq OWNED BY djcelery_intervalschedule.id;


--
-- Name: djcelery_periodictask; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE djcelery_periodictask (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    task character varying(200) NOT NULL,
    interval_id integer,
    crontab_id integer,
    args text NOT NULL,
    kwargs text NOT NULL,
    queue character varying(200),
    exchange character varying(200),
    routing_key character varying(200),
    expires timestamp with time zone,
    enabled boolean NOT NULL,
    last_run_at timestamp with time zone,
    total_run_count integer NOT NULL,
    date_changed timestamp with time zone NOT NULL,
    description text NOT NULL,
    CONSTRAINT djcelery_periodictask_total_run_count_check CHECK ((total_run_count >= 0))
);


ALTER TABLE public.djcelery_periodictask OWNER TO postgres;

--
-- Name: djcelery_periodictask_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE djcelery_periodictask_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.djcelery_periodictask_id_seq OWNER TO postgres;

--
-- Name: djcelery_periodictask_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE djcelery_periodictask_id_seq OWNED BY djcelery_periodictask.id;


--
-- Name: djcelery_periodictasks; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE djcelery_periodictasks (
    ident smallint NOT NULL,
    last_update timestamp with time zone NOT NULL
);


ALTER TABLE public.djcelery_periodictasks OWNER TO postgres;

--
-- Name: djcelery_taskstate; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE djcelery_taskstate (
    id integer NOT NULL,
    state character varying(64) NOT NULL,
    task_id character varying(36) NOT NULL,
    name character varying(200),
    tstamp timestamp with time zone NOT NULL,
    args text,
    kwargs text,
    eta timestamp with time zone,
    expires timestamp with time zone,
    result text,
    traceback text,
    runtime double precision,
    retries integer NOT NULL,
    worker_id integer,
    hidden boolean NOT NULL
);


ALTER TABLE public.djcelery_taskstate OWNER TO postgres;

--
-- Name: djcelery_taskstate_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE djcelery_taskstate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.djcelery_taskstate_id_seq OWNER TO postgres;

--
-- Name: djcelery_taskstate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE djcelery_taskstate_id_seq OWNED BY djcelery_taskstate.id;


--
-- Name: djcelery_workerstate; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE djcelery_workerstate (
    id integer NOT NULL,
    hostname character varying(255) NOT NULL,
    last_heartbeat timestamp with time zone
);


ALTER TABLE public.djcelery_workerstate OWNER TO postgres;

--
-- Name: djcelery_workerstate_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE djcelery_workerstate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.djcelery_workerstate_id_seq OWNER TO postgres;

--
-- Name: djcelery_workerstate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE djcelery_workerstate_id_seq OWNED BY djcelery_workerstate.id;


--
-- Name: dublincore_qualifieddublincoreelement; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE dublincore_qualifieddublincoreelement (
    id integer NOT NULL,
    object_id character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    term character varying(4) NOT NULL,
    qualifier character varying(40),
    content text NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.dublincore_qualifieddublincoreelement OWNER TO postgres;

--
-- Name: dublincore_qualifieddublincoreelement_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dublincore_qualifieddublincoreelement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dublincore_qualifieddublincoreelement_id_seq OWNER TO postgres;

--
-- Name: dublincore_qualifieddublincoreelement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dublincore_qualifieddublincoreelement_id_seq OWNED BY dublincore_qualifieddublincoreelement.id;


--
-- Name: dublincore_qualifieddublincoreelementhistory; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE dublincore_qualifieddublincoreelementhistory (
    id integer NOT NULL,
    object_id character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    term character varying(4) NOT NULL,
    qualifier character varying(40),
    content text NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    qdce_id integer,
    qdce_id_stored integer NOT NULL,
    CONSTRAINT dublincore_qualifieddublincoreelementhisto_qdce_id_stored_check CHECK ((qdce_id_stored >= 0))
);


ALTER TABLE public.dublincore_qualifieddublincoreelementhistory OWNER TO postgres;

--
-- Name: dublincore_qualifieddublincoreelementhistory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dublincore_qualifieddublincoreelementhistory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dublincore_qualifieddublincoreelementhistory_id_seq OWNER TO postgres;

--
-- Name: dublincore_qualifieddublincoreelementhistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dublincore_qualifieddublincoreelementhistory_id_seq OWNED BY dublincore_qualifieddublincoreelementhistory.id;


--
-- Name: forms_field; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE forms_field (
    _order integer,
    form_id integer NOT NULL,
    "default" character varying(2000) NOT NULL,
    required boolean NOT NULL,
    label character varying(200) NOT NULL,
    visible boolean NOT NULL,
    help_text character varying(100) NOT NULL,
    choices character varying(1000) NOT NULL,
    id integer NOT NULL,
    placeholder_text character varying(100) NOT NULL,
    field_type integer NOT NULL
);


ALTER TABLE public.forms_field OWNER TO postgres;

--
-- Name: forms_field_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE forms_field_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.forms_field_id_seq OWNER TO postgres;

--
-- Name: forms_field_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE forms_field_id_seq OWNED BY forms_field.id;


--
-- Name: forms_fieldentry; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE forms_fieldentry (
    entry_id integer NOT NULL,
    field_id integer NOT NULL,
    id integer NOT NULL,
    value character varying(2000)
);


ALTER TABLE public.forms_fieldentry OWNER TO postgres;

--
-- Name: forms_fieldentry_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE forms_fieldentry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.forms_fieldentry_id_seq OWNER TO postgres;

--
-- Name: forms_fieldentry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE forms_fieldentry_id_seq OWNED BY forms_fieldentry.id;


--
-- Name: forms_form; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE forms_form (
    email_message text NOT NULL,
    page_ptr_id integer NOT NULL,
    email_copies character varying(200) NOT NULL,
    button_text character varying(50) NOT NULL,
    response text NOT NULL,
    content text NOT NULL,
    send_email boolean NOT NULL,
    email_subject character varying(200) NOT NULL,
    email_from character varying(75) NOT NULL
);


ALTER TABLE public.forms_form OWNER TO postgres;

--
-- Name: forms_formentry; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE forms_formentry (
    entry_time timestamp with time zone NOT NULL,
    id integer NOT NULL,
    form_id integer NOT NULL
);


ALTER TABLE public.forms_formentry OWNER TO postgres;

--
-- Name: forms_formentry_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE forms_formentry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.forms_formentry_id_seq OWNER TO postgres;

--
-- Name: forms_formentry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE forms_formentry_id_seq OWNED BY forms_formentry.id;


--
-- Name: ga_irods_rodsenvironment; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_irods_rodsenvironment (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    host character varying(255) NOT NULL,
    port integer NOT NULL,
    def_res character varying(255) NOT NULL,
    home_coll character varying(255) NOT NULL,
    cwd text NOT NULL,
    username character varying(255) NOT NULL,
    zone text NOT NULL,
    auth text NOT NULL
);


ALTER TABLE public.ga_irods_rodsenvironment OWNER TO postgres;

--
-- Name: ga_irods_rodsenvironment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ga_irods_rodsenvironment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ga_irods_rodsenvironment_id_seq OWNER TO postgres;

--
-- Name: ga_irods_rodsenvironment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ga_irods_rodsenvironment_id_seq OWNED BY ga_irods_rodsenvironment.id;


--
-- Name: ga_resources_catalogpage; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_catalogpage (
    page_ptr_id integer NOT NULL,
    public boolean NOT NULL,
    owner_id integer
);


ALTER TABLE public.ga_resources_catalogpage OWNER TO postgres;

--
-- Name: ga_resources_dataresource; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_dataresource (
    page_ptr_id integer NOT NULL,
    content text NOT NULL,
    resource_file character varying(100),
    resource_url character varying(200),
    resource_config text,
    last_change timestamp with time zone,
    last_refresh timestamp with time zone,
    next_refresh timestamp with time zone,
    refresh_every interval,
    md5sum character varying(64),
    metadata_url character varying(200),
    metadata_xml text,
    native_bounding_box geometry(Polygon,4326),
    bounding_box geometry(Polygon,4326),
    three_d boolean NOT NULL,
    native_srs text,
    public boolean NOT NULL,
    owner_id integer,
    driver character varying(255) NOT NULL,
    big boolean NOT NULL
);


ALTER TABLE public.ga_resources_dataresource OWNER TO postgres;

--
-- Name: ga_resources_orderedresource; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_orderedresource (
    id integer NOT NULL,
    resource_group_id integer NOT NULL,
    data_resource_id integer NOT NULL,
    ordering integer NOT NULL
);


ALTER TABLE public.ga_resources_orderedresource OWNER TO postgres;

--
-- Name: ga_resources_orderedresource_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ga_resources_orderedresource_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ga_resources_orderedresource_id_seq OWNER TO postgres;

--
-- Name: ga_resources_orderedresource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ga_resources_orderedresource_id_seq OWNED BY ga_resources_orderedresource.id;


--
-- Name: ga_resources_relatedresource; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_relatedresource (
    page_ptr_id integer NOT NULL,
    content text NOT NULL,
    resource_file character varying(100) NOT NULL,
    foreign_resource_id integer NOT NULL,
    foreign_key character varying(64),
    local_key character varying(64),
    left_index boolean NOT NULL,
    right_index boolean NOT NULL,
    how character varying(8) NOT NULL,
    driver character varying(255) NOT NULL,
    key_transform integer
);


ALTER TABLE public.ga_resources_relatedresource OWNER TO postgres;

--
-- Name: ga_resources_renderedlayer; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_renderedlayer (
    page_ptr_id integer NOT NULL,
    content text NOT NULL,
    data_resource_id integer NOT NULL,
    default_style_id integer NOT NULL,
    default_class character varying(255) NOT NULL,
    public boolean NOT NULL,
    owner_id integer
);


ALTER TABLE public.ga_resources_renderedlayer OWNER TO postgres;

--
-- Name: ga_resources_renderedlayer_styles; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_renderedlayer_styles (
    id integer NOT NULL,
    renderedlayer_id integer NOT NULL,
    style_id integer NOT NULL
);


ALTER TABLE public.ga_resources_renderedlayer_styles OWNER TO postgres;

--
-- Name: ga_resources_renderedlayer_styles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ga_resources_renderedlayer_styles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ga_resources_renderedlayer_styles_id_seq OWNER TO postgres;

--
-- Name: ga_resources_renderedlayer_styles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ga_resources_renderedlayer_styles_id_seq OWNED BY ga_resources_renderedlayer_styles.id;


--
-- Name: ga_resources_resourcegroup; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_resourcegroup (
    page_ptr_id integer NOT NULL,
    is_timeseries boolean NOT NULL,
    min_time timestamp with time zone,
    max_time timestamp with time zone
);


ALTER TABLE public.ga_resources_resourcegroup OWNER TO postgres;

--
-- Name: ga_resources_style; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_resources_style (
    page_ptr_id integer NOT NULL,
    legend character varying(100),
    legend_width integer,
    legend_height integer,
    stylesheet text NOT NULL,
    public boolean NOT NULL,
    owner_id integer
);


ALTER TABLE public.ga_resources_style OWNER TO postgres;

--
-- Name: galleries_gallery; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE galleries_gallery (
    page_ptr_id integer NOT NULL,
    content text NOT NULL,
    zip_import character varying(100) NOT NULL
);


ALTER TABLE public.galleries_gallery OWNER TO postgres;

--
-- Name: galleries_galleryimage; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE galleries_galleryimage (
    id integer NOT NULL,
    _order integer,
    gallery_id integer NOT NULL,
    file character varying(200) NOT NULL,
    description character varying(1000) NOT NULL
);


ALTER TABLE public.galleries_galleryimage OWNER TO postgres;

--
-- Name: galleries_galleryimage_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE galleries_galleryimage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.galleries_galleryimage_id_seq OWNER TO postgres;

--
-- Name: galleries_galleryimage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE galleries_galleryimage_id_seq OWNED BY galleries_galleryimage.id;


--
-- Name: generic_assignedkeyword; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE generic_assignedkeyword (
    content_type_id integer NOT NULL,
    id integer NOT NULL,
    keyword_id integer NOT NULL,
    object_pk integer,
    _order integer
);


ALTER TABLE public.generic_assignedkeyword OWNER TO postgres;

--
-- Name: generic_assignedkeyword_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE generic_assignedkeyword_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.generic_assignedkeyword_id_seq OWNER TO postgres;

--
-- Name: generic_assignedkeyword_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE generic_assignedkeyword_id_seq OWNED BY generic_assignedkeyword.id;


--
-- Name: generic_keyword; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE generic_keyword (
    slug character varying(2000),
    id integer NOT NULL,
    title character varying(500) NOT NULL,
    site_id integer NOT NULL
);


ALTER TABLE public.generic_keyword OWNER TO postgres;

--
-- Name: generic_keyword_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE generic_keyword_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.generic_keyword_id_seq OWNER TO postgres;

--
-- Name: generic_keyword_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE generic_keyword_id_seq OWNED BY generic_keyword.id;


--
-- Name: generic_rating; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE generic_rating (
    content_type_id integer NOT NULL,
    id integer NOT NULL,
    value integer NOT NULL,
    object_pk integer,
    rating_date timestamp with time zone,
    user_id integer
);


ALTER TABLE public.generic_rating OWNER TO postgres;

--
-- Name: generic_rating_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE generic_rating_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.generic_rating_id_seq OWNER TO postgres;

--
-- Name: generic_rating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE generic_rating_id_seq OWNED BY generic_rating.id;


--
-- Name: generic_threadedcomment; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE generic_threadedcomment (
    by_author boolean NOT NULL,
    comment_ptr_id integer NOT NULL,
    replied_to_id integer,
    rating_count integer NOT NULL,
    rating_average double precision NOT NULL,
    rating_sum integer NOT NULL
);


ALTER TABLE public.generic_threadedcomment OWNER TO postgres;

--
-- Name: hs_core_bags; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_bags (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    bag character varying(100),
    CONSTRAINT hs_core_bags_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_bags OWNER TO postgres;

--
-- Name: hs_core_bags_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_bags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_bags_id_seq OWNER TO postgres;

--
-- Name: hs_core_bags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_bags_id_seq OWNED BY hs_core_bags.id;


--
-- Name: hs_core_contributor; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_contributor (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    description character varying(200),
    name character varying(100) NOT NULL,
    organization character varying(200),
    email character varying(75),
    address character varying(250),
    phone character varying(25),
    homepage character varying(200),
    "researcherID" character varying(200),
    "researchGateID" character varying(200),
    CONSTRAINT hs_core_contributor_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_contributor OWNER TO postgres;

--
-- Name: hs_core_contributor_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_contributor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_contributor_id_seq OWNER TO postgres;

--
-- Name: hs_core_contributor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_contributor_id_seq OWNED BY hs_core_contributor.id;


--
-- Name: hs_core_coremetadata; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_coremetadata (
    id integer NOT NULL
);


ALTER TABLE public.hs_core_coremetadata OWNER TO postgres;

--
-- Name: hs_core_coremetadata_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_coremetadata_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_coremetadata_id_seq OWNER TO postgres;

--
-- Name: hs_core_coremetadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_coremetadata_id_seq OWNED BY hs_core_coremetadata.id;


--
-- Name: hs_core_coverage; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_coverage (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    type character varying(20) NOT NULL,
    _value character varying(1024) NOT NULL,
    CONSTRAINT hs_core_coverage_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_coverage OWNER TO postgres;

--
-- Name: hs_core_coverage_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_coverage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_coverage_id_seq OWNER TO postgres;

--
-- Name: hs_core_coverage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_coverage_id_seq OWNED BY hs_core_coverage.id;


--
-- Name: hs_core_creator; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_creator (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    description character varying(200),
    name character varying(100) NOT NULL,
    organization character varying(200),
    email character varying(75),
    address character varying(250),
    phone character varying(25),
    homepage character varying(200),
    "researcherID" character varying(200),
    "researchGateID" character varying(200),
    "order" integer NOT NULL,
    CONSTRAINT hs_core_creator_object_id_check CHECK ((object_id >= 0)),
    CONSTRAINT hs_core_creator_order_check CHECK (("order" >= 0))
);


ALTER TABLE public.hs_core_creator OWNER TO postgres;

--
-- Name: hs_core_creator_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_creator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_creator_id_seq OWNER TO postgres;

--
-- Name: hs_core_creator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_creator_id_seq OWNED BY hs_core_creator.id;


--
-- Name: hs_core_date; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_date (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    type character varying(20) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    CONSTRAINT hs_core_date_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_date OWNER TO postgres;

--
-- Name: hs_core_date_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_date_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_date_id_seq OWNER TO postgres;

--
-- Name: hs_core_date_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_date_id_seq OWNED BY hs_core_date.id;


--
-- Name: hs_core_description; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_description (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    abstract character varying(500) NOT NULL,
    CONSTRAINT hs_core_description_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_description OWNER TO postgres;

--
-- Name: hs_core_description_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_description_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_description_id_seq OWNER TO postgres;

--
-- Name: hs_core_description_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_description_id_seq OWNED BY hs_core_description.id;


--
-- Name: hs_core_externalprofilelink; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_externalprofilelink (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    url character varying(200) NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    CONSTRAINT hs_core_externalprofilelink_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_externalprofilelink OWNER TO postgres;

--
-- Name: hs_core_externalprofilelink_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_externalprofilelink_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_externalprofilelink_id_seq OWNER TO postgres;

--
-- Name: hs_core_externalprofilelink_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_externalprofilelink_id_seq OWNED BY hs_core_externalprofilelink.id;


--
-- Name: hs_core_format; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_format (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    value character varying(50) NOT NULL,
    CONSTRAINT hs_core_format_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_format OWNER TO postgres;

--
-- Name: hs_core_format_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_format_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_format_id_seq OWNER TO postgres;

--
-- Name: hs_core_format_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_format_id_seq OWNED BY hs_core_format.id;


--
-- Name: hs_core_genericresource; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_genericresource (
    page_ptr_id integer NOT NULL,
    content text NOT NULL,
    user_id integer NOT NULL,
    creator_id integer NOT NULL,
    public boolean NOT NULL,
    frozen boolean NOT NULL,
    do_not_distribute boolean NOT NULL,
    discoverable boolean NOT NULL,
    published_and_frozen boolean NOT NULL,
    last_changed_by_id integer,
    comments_count integer NOT NULL,
    short_id character varying(32) NOT NULL,
    doi character varying(1024),
    object_id integer,
    content_type_id integer,
    CONSTRAINT ck_object_id_pstv_59b90619f3c946d0 CHECK ((object_id >= 0)),
    CONSTRAINT hs_core_genericresource_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_genericresource OWNER TO postgres;

--
-- Name: hs_core_genericresource_edit_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_genericresource_edit_groups (
    id integer NOT NULL,
    genericresource_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.hs_core_genericresource_edit_groups OWNER TO postgres;

--
-- Name: hs_core_genericresource_edit_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_genericresource_edit_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_genericresource_edit_groups_id_seq OWNER TO postgres;

--
-- Name: hs_core_genericresource_edit_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_genericresource_edit_groups_id_seq OWNED BY hs_core_genericresource_edit_groups.id;


--
-- Name: hs_core_genericresource_edit_users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_genericresource_edit_users (
    id integer NOT NULL,
    genericresource_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.hs_core_genericresource_edit_users OWNER TO postgres;

--
-- Name: hs_core_genericresource_edit_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_genericresource_edit_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_genericresource_edit_users_id_seq OWNER TO postgres;

--
-- Name: hs_core_genericresource_edit_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_genericresource_edit_users_id_seq OWNED BY hs_core_genericresource_edit_users.id;


--
-- Name: hs_core_genericresource_owners; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_genericresource_owners (
    id integer NOT NULL,
    genericresource_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.hs_core_genericresource_owners OWNER TO postgres;

--
-- Name: hs_core_genericresource_owners_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_genericresource_owners_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_genericresource_owners_id_seq OWNER TO postgres;

--
-- Name: hs_core_genericresource_owners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_genericresource_owners_id_seq OWNED BY hs_core_genericresource_owners.id;


--
-- Name: hs_core_genericresource_view_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_genericresource_view_groups (
    id integer NOT NULL,
    genericresource_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.hs_core_genericresource_view_groups OWNER TO postgres;

--
-- Name: hs_core_genericresource_view_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_genericresource_view_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_genericresource_view_groups_id_seq OWNER TO postgres;

--
-- Name: hs_core_genericresource_view_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_genericresource_view_groups_id_seq OWNED BY hs_core_genericresource_view_groups.id;


--
-- Name: hs_core_genericresource_view_users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_genericresource_view_users (
    id integer NOT NULL,
    genericresource_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.hs_core_genericresource_view_users OWNER TO postgres;

--
-- Name: hs_core_genericresource_view_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_genericresource_view_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_genericresource_view_users_id_seq OWNER TO postgres;

--
-- Name: hs_core_genericresource_view_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_genericresource_view_users_id_seq OWNED BY hs_core_genericresource_view_users.id;


--
-- Name: hs_core_groupownership; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_groupownership (
    id integer NOT NULL,
    group_id integer NOT NULL,
    owner_id integer NOT NULL
);


ALTER TABLE public.hs_core_groupownership OWNER TO postgres;

--
-- Name: hs_core_groupownership_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_groupownership_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_groupownership_id_seq OWNER TO postgres;

--
-- Name: hs_core_groupownership_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_groupownership_id_seq OWNED BY hs_core_groupownership.id;


--
-- Name: hs_core_identifier; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_identifier (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    name character varying(100) NOT NULL,
    url character varying(200) NOT NULL,
    CONSTRAINT hs_core_identifier_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_identifier OWNER TO postgres;

--
-- Name: hs_core_identifier_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_identifier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_identifier_id_seq OWNER TO postgres;

--
-- Name: hs_core_identifier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_identifier_id_seq OWNED BY hs_core_identifier.id;


--
-- Name: hs_core_language; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_language (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    code character varying(3) NOT NULL,
    CONSTRAINT hs_core_language_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_language OWNER TO postgres;

--
-- Name: hs_core_language_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_language_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_language_id_seq OWNER TO postgres;

--
-- Name: hs_core_language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_language_id_seq OWNED BY hs_core_language.id;


--
-- Name: hs_core_publisher; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_publisher (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    name character varying(200) NOT NULL,
    url character varying(200) NOT NULL,
    CONSTRAINT hs_core_publisher_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_publisher OWNER TO postgres;

--
-- Name: hs_core_publisher_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_publisher_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_publisher_id_seq OWNER TO postgres;

--
-- Name: hs_core_publisher_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_publisher_id_seq OWNED BY hs_core_publisher.id;


--
-- Name: hs_core_relation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_relation (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    type character varying(100) NOT NULL,
    value character varying(500) NOT NULL,
    CONSTRAINT hs_core_relation_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_relation OWNER TO postgres;

--
-- Name: hs_core_relation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_relation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_relation_id_seq OWNER TO postgres;

--
-- Name: hs_core_relation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_relation_id_seq OWNED BY hs_core_relation.id;


--
-- Name: hs_core_resourcefile; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_resourcefile (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    resource_file character varying(100) NOT NULL,
    CONSTRAINT hs_core_resourcefile_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_resourcefile OWNER TO postgres;

--
-- Name: hs_core_resourcefile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_resourcefile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_resourcefile_id_seq OWNER TO postgres;

--
-- Name: hs_core_resourcefile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_resourcefile_id_seq OWNED BY hs_core_resourcefile.id;


--
-- Name: hs_core_rights; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_rights (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    statement text,
    url character varying(200),
    CONSTRAINT hs_core_rights_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_rights OWNER TO postgres;

--
-- Name: hs_core_rights_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_rights_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_rights_id_seq OWNER TO postgres;

--
-- Name: hs_core_rights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_rights_id_seq OWNED BY hs_core_rights.id;


--
-- Name: hs_core_source; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_source (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    derived_from character varying(300) NOT NULL,
    CONSTRAINT hs_core_source_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_source OWNER TO postgres;

--
-- Name: hs_core_source_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_source_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_source_id_seq OWNER TO postgres;

--
-- Name: hs_core_source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_source_id_seq OWNED BY hs_core_source.id;


--
-- Name: hs_core_subject; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_subject (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    value character varying(100) NOT NULL,
    CONSTRAINT hs_core_subject_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_subject OWNER TO postgres;

--
-- Name: hs_core_subject_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_subject_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_subject_id_seq OWNER TO postgres;

--
-- Name: hs_core_subject_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_subject_id_seq OWNED BY hs_core_subject.id;


--
-- Name: hs_core_title; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_title (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    value character varying(300) NOT NULL,
    CONSTRAINT hs_core_title_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_title OWNER TO postgres;

--
-- Name: hs_core_title_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_title_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_title_id_seq OWNER TO postgres;

--
-- Name: hs_core_title_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_title_id_seq OWNED BY hs_core_title.id;


--
-- Name: hs_core_type; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_core_type (
    id integer NOT NULL,
    object_id integer NOT NULL,
    content_type_id integer NOT NULL,
    url character varying(200) NOT NULL,
    CONSTRAINT hs_core_type_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_core_type OWNER TO postgres;

--
-- Name: hs_core_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_core_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_core_type_id_seq OWNER TO postgres;

--
-- Name: hs_core_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_core_type_id_seq OWNED BY hs_core_type.id;


--
-- Name: hs_party_addresscodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_addresscodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_addresscodelist OWNER TO postgres;

--
-- Name: hs_party_choicetype; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_choicetype (
    id integer NOT NULL,
    "choiceType" character varying(40) NOT NULL,
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_choicetype OWNER TO postgres;

--
-- Name: hs_party_choicetype_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_choicetype_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_choicetype_id_seq OWNER TO postgres;

--
-- Name: hs_party_choicetype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_choicetype_id_seq OWNED BY hs_party_choicetype.id;


--
-- Name: hs_party_city; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_city (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    "geonamesUrl" character varying(200) NOT NULL
);


ALTER TABLE public.hs_party_city OWNER TO postgres;

--
-- Name: hs_party_city_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_city_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_city_id_seq OWNER TO postgres;

--
-- Name: hs_party_city_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_city_id_seq OWNED BY hs_party_city.id;


--
-- Name: hs_party_country; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_country (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    "geonamesUrl" character varying(200) NOT NULL
);


ALTER TABLE public.hs_party_country OWNER TO postgres;

--
-- Name: hs_party_country_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_country_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_country_id_seq OWNER TO postgres;

--
-- Name: hs_party_country_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_country_id_seq OWNED BY hs_party_country.id;


--
-- Name: hs_party_emailcodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_emailcodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_emailcodelist OWNER TO postgres;

--
-- Name: hs_party_externalidentifiercodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_externalidentifiercodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_externalidentifiercodelist OWNER TO postgres;

--
-- Name: hs_party_externalorgidentifier; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_externalorgidentifier (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    "identifierName_id" character varying(24) NOT NULL,
    "otherName" character varying(255) NOT NULL,
    "identifierCode" character varying(255) NOT NULL,
    "createdDate" date NOT NULL
);


ALTER TABLE public.hs_party_externalorgidentifier OWNER TO postgres;

--
-- Name: hs_party_externalorgidentifier_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_externalorgidentifier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_externalorgidentifier_id_seq OWNER TO postgres;

--
-- Name: hs_party_externalorgidentifier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_externalorgidentifier_id_seq OWNED BY hs_party_externalorgidentifier.id;


--
-- Name: hs_party_group; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_group (
    party_ptr_id integer NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    title character varying(500) NOT NULL,
    slug character varying(2000),
    _meta_title character varying(500),
    description text NOT NULL,
    gen_description boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone,
    status integer NOT NULL,
    publish_date timestamp with time zone,
    expiry_date timestamp with time zone,
    short_url character varying(200),
    in_sitemap boolean NOT NULL
);


ALTER TABLE public.hs_party_group OWNER TO postgres;

--
-- Name: hs_party_namealiascodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_namealiascodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_namealiascodelist OWNER TO postgres;

--
-- Name: hs_party_organization; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organization (
    party_ptr_id integer NOT NULL,
    specialities_string character varying(500) NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    title character varying(500) NOT NULL,
    slug character varying(2000),
    _meta_title character varying(500),
    description text NOT NULL,
    gen_description boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone,
    status integer NOT NULL,
    publish_date timestamp with time zone,
    expiry_date timestamp with time zone,
    short_url character varying(200),
    in_sitemap boolean NOT NULL,
    "logoUrl" character varying(100) NOT NULL,
    "parentOrganization_id" integer,
    "organizationType_id" character varying(24) NOT NULL
);


ALTER TABLE public.hs_party_organization OWNER TO postgres;

--
-- Name: hs_party_organizationassociation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organizationassociation (
    id integer NOT NULL,
    "createdDate" date NOT NULL,
    "uniqueCode" character varying(64) NOT NULL,
    organization_id integer NOT NULL,
    person_id integer NOT NULL,
    "beginDate" date,
    "endDate" date,
    "jobTitle" character varying(100) NOT NULL,
    "presentOrganization" boolean NOT NULL
);


ALTER TABLE public.hs_party_organizationassociation OWNER TO postgres;

--
-- Name: hs_party_organizationassociation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_organizationassociation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_organizationassociation_id_seq OWNER TO postgres;

--
-- Name: hs_party_organizationassociation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_organizationassociation_id_seq OWNED BY hs_party_organizationassociation.id;


--
-- Name: hs_party_organizationcodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organizationcodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_organizationcodelist OWNER TO postgres;

--
-- Name: hs_party_organizationemail; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organizationemail (
    id integer NOT NULL,
    email character varying(30) NOT NULL,
    email_type_id character varying(24) NOT NULL,
    organization_id integer
);


ALTER TABLE public.hs_party_organizationemail OWNER TO postgres;

--
-- Name: hs_party_organizationemail_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_organizationemail_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_organizationemail_id_seq OWNER TO postgres;

--
-- Name: hs_party_organizationemail_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_organizationemail_id_seq OWNED BY hs_party_organizationemail.id;


--
-- Name: hs_party_organizationlocation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organizationlocation (
    id integer NOT NULL,
    address text NOT NULL,
    address_type_id character varying(24) NOT NULL,
    organization_id integer
);


ALTER TABLE public.hs_party_organizationlocation OWNER TO postgres;

--
-- Name: hs_party_organizationlocation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_organizationlocation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_organizationlocation_id_seq OWNER TO postgres;

--
-- Name: hs_party_organizationlocation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_organizationlocation_id_seq OWNED BY hs_party_organizationlocation.id;


--
-- Name: hs_party_organizationname; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organizationname (
    id integer NOT NULL,
    "otherName" character varying(255) NOT NULL,
    annotation_id character varying(24) NOT NULL,
    organization_id integer
);


ALTER TABLE public.hs_party_organizationname OWNER TO postgres;

--
-- Name: hs_party_organizationname_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_organizationname_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_organizationname_id_seq OWNER TO postgres;

--
-- Name: hs_party_organizationname_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_organizationname_id_seq OWNED BY hs_party_organizationname.id;


--
-- Name: hs_party_organizationphone; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_organizationphone (
    id integer NOT NULL,
    phone_number character varying(30) NOT NULL,
    phone_type_id character varying(24) NOT NULL,
    organization_id integer
);


ALTER TABLE public.hs_party_organizationphone OWNER TO postgres;

--
-- Name: hs_party_organizationphone_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_organizationphone_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_organizationphone_id_seq OWNER TO postgres;

--
-- Name: hs_party_organizationphone_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_organizationphone_id_seq OWNED BY hs_party_organizationphone.id;


--
-- Name: hs_party_othername; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_othername (
    id integer NOT NULL,
    "otherName" character varying(255) NOT NULL,
    annotation_id character varying(24) NOT NULL,
    persons_id integer NOT NULL
);


ALTER TABLE public.hs_party_othername OWNER TO postgres;

--
-- Name: hs_party_othername_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_othername_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_othername_id_seq OWNER TO postgres;

--
-- Name: hs_party_othername_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_othername_id_seq OWNED BY hs_party_othername.id;


--
-- Name: hs_party_party; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_party (
    id integer NOT NULL,
    "uniqueCode" character varying(64) NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    notes text NOT NULL,
    "createdDate" date NOT NULL,
    "lastUpdate" date NOT NULL
);


ALTER TABLE public.hs_party_party OWNER TO postgres;

--
-- Name: hs_party_party_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_party_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_party_id_seq OWNER TO postgres;

--
-- Name: hs_party_party_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_party_id_seq OWNED BY hs_party_party.id;


--
-- Name: hs_party_person; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_person (
    party_ptr_id integer NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    title character varying(500) NOT NULL,
    slug character varying(2000),
    _meta_title character varying(500),
    description text NOT NULL,
    gen_description boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone,
    status integer NOT NULL,
    publish_date timestamp with time zone,
    expiry_date timestamp with time zone,
    short_url character varying(200),
    in_sitemap boolean NOT NULL,
    "givenName" character varying(125) NOT NULL,
    "familyName" character varying(125) NOT NULL,
    "jobTitle" character varying(100) NOT NULL,
    "primaryOrganizationRecord_id" integer
);


ALTER TABLE public.hs_party_person OWNER TO postgres;

--
-- Name: hs_party_personemail; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_personemail (
    id integer NOT NULL,
    email character varying(30) NOT NULL,
    email_type_id character varying(24) NOT NULL,
    person_id integer
);


ALTER TABLE public.hs_party_personemail OWNER TO postgres;

--
-- Name: hs_party_personemail_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_personemail_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_personemail_id_seq OWNER TO postgres;

--
-- Name: hs_party_personemail_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_personemail_id_seq OWNED BY hs_party_personemail.id;


--
-- Name: hs_party_personexternalidentifier; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_personexternalidentifier (
    id integer NOT NULL,
    person_id integer NOT NULL,
    "identifierName_id" character varying(24) NOT NULL,
    "otherName" character varying(255) NOT NULL,
    "identifierCode" character varying(255) NOT NULL,
    "createdDate" date NOT NULL
);


ALTER TABLE public.hs_party_personexternalidentifier OWNER TO postgres;

--
-- Name: hs_party_personexternalidentifier_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_personexternalidentifier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_personexternalidentifier_id_seq OWNER TO postgres;

--
-- Name: hs_party_personexternalidentifier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_personexternalidentifier_id_seq OWNED BY hs_party_personexternalidentifier.id;


--
-- Name: hs_party_personlocation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_personlocation (
    id integer NOT NULL,
    address text NOT NULL,
    address_type_id character varying(24) NOT NULL,
    person_id integer
);


ALTER TABLE public.hs_party_personlocation OWNER TO postgres;

--
-- Name: hs_party_personlocation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_personlocation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_personlocation_id_seq OWNER TO postgres;

--
-- Name: hs_party_personlocation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_personlocation_id_seq OWNED BY hs_party_personlocation.id;


--
-- Name: hs_party_personphone; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_personphone (
    id integer NOT NULL,
    phone_number character varying(30) NOT NULL,
    phone_type_id character varying(24) NOT NULL,
    person_id integer
);


ALTER TABLE public.hs_party_personphone OWNER TO postgres;

--
-- Name: hs_party_personphone_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_personphone_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_personphone_id_seq OWNER TO postgres;

--
-- Name: hs_party_personphone_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_personphone_id_seq OWNED BY hs_party_personphone.id;


--
-- Name: hs_party_phonecodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_phonecodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_phonecodelist OWNER TO postgres;

--
-- Name: hs_party_region; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_region (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    "geonamesUrl" character varying(200) NOT NULL
);


ALTER TABLE public.hs_party_region OWNER TO postgres;

--
-- Name: hs_party_region_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_party_region_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_party_region_id_seq OWNER TO postgres;

--
-- Name: hs_party_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_party_region_id_seq OWNED BY hs_party_region.id;


--
-- Name: hs_party_usercodelist; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_party_usercodelist (
    code character varying(24) NOT NULL,
    name character varying(255) NOT NULL,
    "order" integer NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.hs_party_usercodelist OWNER TO postgres;

--
-- Name: hs_scholar_profile_city; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_city (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    "geonamesUrl" character varying(200) NOT NULL
);


ALTER TABLE public.hs_scholar_profile_city OWNER TO postgres;

--
-- Name: hs_scholar_profile_city_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_city_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_city_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_city_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_city_id_seq OWNED BY hs_scholar_profile_city.id;


--
-- Name: hs_scholar_profile_country; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_country (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    "geonamesUrl" character varying(200) NOT NULL
);


ALTER TABLE public.hs_scholar_profile_country OWNER TO postgres;

--
-- Name: hs_scholar_profile_country_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_country_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_country_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_country_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_country_id_seq OWNED BY hs_scholar_profile_country.id;


--
-- Name: hs_scholar_profile_externalidentifiers; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_externalidentifiers (
    id integer NOT NULL,
    "identifierName" character varying(255) NOT NULL,
    "otherName" character varying(255) NOT NULL,
    "identifierCode" character varying(24) NOT NULL,
    "createdDate" date NOT NULL
);


ALTER TABLE public.hs_scholar_profile_externalidentifiers OWNER TO postgres;

--
-- Name: hs_scholar_profile_externalidentifiers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_externalidentifiers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_externalidentifiers_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_externalidentifiers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_externalidentifiers_id_seq OWNED BY hs_scholar_profile_externalidentifiers.id;


--
-- Name: hs_scholar_profile_externalorgidentifiers; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_externalorgidentifiers (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    "identifierName" character varying(10) NOT NULL,
    "otherName" character varying(255) NOT NULL,
    "identifierCode" character varying(255) NOT NULL,
    "createdDate" date NOT NULL
);


ALTER TABLE public.hs_scholar_profile_externalorgidentifiers OWNER TO postgres;

--
-- Name: hs_scholar_profile_externalorgidentifiers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_externalorgidentifiers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_externalorgidentifiers_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_externalorgidentifiers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_externalorgidentifiers_id_seq OWNED BY hs_scholar_profile_externalorgidentifiers.id;


--
-- Name: hs_scholar_profile_organization; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_organization (
    id integer NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    title character varying(500) NOT NULL,
    slug character varying(2000),
    _meta_title character varying(500),
    description text NOT NULL,
    gen_description boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone,
    status integer NOT NULL,
    publish_date timestamp with time zone,
    expiry_date timestamp with time zone,
    short_url character varying(200),
    in_sitemap boolean NOT NULL,
    "uniqueCode" character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    notes text NOT NULL,
    "createdDate" date NOT NULL,
    "lastUpdate" date NOT NULL,
    "logoUrl" character varying(100) NOT NULL,
    "parentOrganization_id" integer,
    "organizationType" character varying(14) NOT NULL
);


ALTER TABLE public.hs_scholar_profile_organization OWNER TO postgres;

--
-- Name: hs_scholar_profile_organization_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_organization_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_organization_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_organization_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_organization_id_seq OWNED BY hs_scholar_profile_organization.id;


--
-- Name: hs_scholar_profile_organizationemail; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_organizationemail (
    id integer NOT NULL,
    phone_number character varying(30) NOT NULL,
    phone_type character varying(30) NOT NULL,
    organization_id integer NOT NULL
);


ALTER TABLE public.hs_scholar_profile_organizationemail OWNER TO postgres;

--
-- Name: hs_scholar_profile_organizationemail_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_organizationemail_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_organizationemail_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_organizationemail_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_organizationemail_id_seq OWNED BY hs_scholar_profile_organizationemail.id;


--
-- Name: hs_scholar_profile_organizationlocation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_organizationlocation (
    id integer NOT NULL,
    address text NOT NULL,
    address_type character varying(24) NOT NULL,
    organization_id integer NOT NULL
);


ALTER TABLE public.hs_scholar_profile_organizationlocation OWNER TO postgres;

--
-- Name: hs_scholar_profile_organizationlocation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_organizationlocation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_organizationlocation_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_organizationlocation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_organizationlocation_id_seq OWNED BY hs_scholar_profile_organizationlocation.id;


--
-- Name: hs_scholar_profile_organizationphone; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_organizationphone (
    id integer NOT NULL,
    phone_number character varying(30) NOT NULL,
    phone_type character varying(30) NOT NULL,
    organization_id integer NOT NULL
);


ALTER TABLE public.hs_scholar_profile_organizationphone OWNER TO postgres;

--
-- Name: hs_scholar_profile_organizationphone_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_organizationphone_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_organizationphone_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_organizationphone_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_organizationphone_id_seq OWNED BY hs_scholar_profile_organizationphone.id;


--
-- Name: hs_scholar_profile_orgassociations; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_orgassociations (
    id integer NOT NULL,
    "createdDate" date NOT NULL,
    organization_id integer NOT NULL,
    person_id integer NOT NULL,
    "beginDate" date NOT NULL,
    "endDate" date,
    "jobTitle" character varying(100) NOT NULL,
    "presentOrganization" boolean NOT NULL
);


ALTER TABLE public.hs_scholar_profile_orgassociations OWNER TO postgres;

--
-- Name: hs_scholar_profile_orgassociations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_orgassociations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_orgassociations_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_orgassociations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_orgassociations_id_seq OWNED BY hs_scholar_profile_orgassociations.id;


--
-- Name: hs_scholar_profile_othernames; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_othernames (
    id integer NOT NULL,
    persons_id integer NOT NULL,
    "otherName" character varying(255) NOT NULL,
    annotation character varying(10) NOT NULL
);


ALTER TABLE public.hs_scholar_profile_othernames OWNER TO postgres;

--
-- Name: hs_scholar_profile_othernames_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_othernames_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_othernames_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_othernames_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_othernames_id_seq OWNED BY hs_scholar_profile_othernames.id;


--
-- Name: hs_scholar_profile_person; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_person (
    id integer NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    title character varying(500) NOT NULL,
    slug character varying(2000),
    _meta_title character varying(500),
    description text NOT NULL,
    gen_description boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone,
    status integer NOT NULL,
    publish_date timestamp with time zone,
    expiry_date timestamp with time zone,
    short_url character varying(200),
    in_sitemap boolean NOT NULL,
    "uniqueCode" character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    notes text NOT NULL,
    "createdDate" date NOT NULL,
    "lastUpdate" date NOT NULL,
    "givenName" character varying(125) NOT NULL,
    "familyName" character varying(125) NOT NULL,
    "jobTitle" character varying(100) NOT NULL
);


ALTER TABLE public.hs_scholar_profile_person OWNER TO postgres;

--
-- Name: hs_scholar_profile_person_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_person_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_person_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_person_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_person_id_seq OWNED BY hs_scholar_profile_person.id;


--
-- Name: hs_scholar_profile_personemail; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_personemail (
    id integer NOT NULL,
    phone_number character varying(30) NOT NULL,
    phone_type character varying(30) NOT NULL,
    person_id integer
);


ALTER TABLE public.hs_scholar_profile_personemail OWNER TO postgres;

--
-- Name: hs_scholar_profile_personemail_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_personemail_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_personemail_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_personemail_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_personemail_id_seq OWNED BY hs_scholar_profile_personemail.id;


--
-- Name: hs_scholar_profile_personlocation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_personlocation (
    id integer NOT NULL,
    address text NOT NULL,
    address_type character varying(24) NOT NULL,
    person_id integer
);


ALTER TABLE public.hs_scholar_profile_personlocation OWNER TO postgres;

--
-- Name: hs_scholar_profile_personlocation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_personlocation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_personlocation_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_personlocation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_personlocation_id_seq OWNED BY hs_scholar_profile_personlocation.id;


--
-- Name: hs_scholar_profile_personphone; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_personphone (
    id integer NOT NULL,
    phone_number character varying(30) NOT NULL,
    phone_type character varying(30) NOT NULL,
    person_id integer
);


ALTER TABLE public.hs_scholar_profile_personphone OWNER TO postgres;

--
-- Name: hs_scholar_profile_personphone_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_personphone_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_personphone_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_personphone_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_personphone_id_seq OWNED BY hs_scholar_profile_personphone.id;


--
-- Name: hs_scholar_profile_region; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_region (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    "geonamesUrl" character varying(200) NOT NULL
);


ALTER TABLE public.hs_scholar_profile_region OWNER TO postgres;

--
-- Name: hs_scholar_profile_region_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_region_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_region_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_region_id_seq OWNED BY hs_scholar_profile_region.id;


--
-- Name: hs_scholar_profile_scholar; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_scholar (
    person_ptr_id integer NOT NULL,
    user_id integer NOT NULL,
    demographics_id integer
);


ALTER TABLE public.hs_scholar_profile_scholar OWNER TO postgres;

--
-- Name: hs_scholar_profile_scholarexternalidentifiers; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_scholarexternalidentifiers (
    externalidentifiers_ptr_id integer NOT NULL,
    scholar_id integer NOT NULL
);


ALTER TABLE public.hs_scholar_profile_scholarexternalidentifiers OWNER TO postgres;

--
-- Name: hs_scholar_profile_scholargroup; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_scholargroup (
    group_ptr_id integer NOT NULL,
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    title character varying(500) NOT NULL,
    slug character varying(2000),
    _meta_title character varying(500),
    description text NOT NULL,
    gen_description boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone,
    status integer NOT NULL,
    publish_date timestamp with time zone,
    expiry_date timestamp with time zone,
    short_url character varying(200),
    in_sitemap boolean NOT NULL,
    "groupDescription" text NOT NULL,
    purpose character varying(100) NOT NULL,
    "createdDate" date NOT NULL,
    "createdBy_id" integer NOT NULL
);


ALTER TABLE public.hs_scholar_profile_scholargroup OWNER TO postgres;

--
-- Name: hs_scholar_profile_userdemographics; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_userdemographics (
    id integer NOT NULL,
    public boolean NOT NULL,
    "userType" character varying(255) NOT NULL,
    city_id integer,
    region_id integer,
    country_id integer
);


ALTER TABLE public.hs_scholar_profile_userdemographics OWNER TO postgres;

--
-- Name: hs_scholar_profile_userdemographics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_userdemographics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_userdemographics_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_userdemographics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_userdemographics_id_seq OWNED BY hs_scholar_profile_userdemographics.id;


--
-- Name: hs_scholar_profile_userkeywords; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_scholar_profile_userkeywords (
    id integer NOT NULL,
    person_id integer NOT NULL,
    keyword character varying(100) NOT NULL,
    "createdDate" date NOT NULL
);


ALTER TABLE public.hs_scholar_profile_userkeywords OWNER TO postgres;

--
-- Name: hs_scholar_profile_userkeywords_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_scholar_profile_userkeywords_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_scholar_profile_userkeywords_id_seq OWNER TO postgres;

--
-- Name: hs_scholar_profile_userkeywords_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_scholar_profile_userkeywords_id_seq OWNED BY hs_scholar_profile_userkeywords.id;


--
-- Name: pages_link; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pages_link (
    page_ptr_id integer NOT NULL
);


ALTER TABLE public.pages_link OWNER TO postgres;

--
-- Name: pages_page; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pages_page (
    status integer NOT NULL,
    _order integer,
    parent_id integer,
    description text NOT NULL,
    title character varying(500) NOT NULL,
    short_url character varying(200),
    login_required boolean NOT NULL,
    id integer NOT NULL,
    expiry_date timestamp with time zone,
    publish_date timestamp with time zone,
    titles character varying(1000),
    content_model character varying(50),
    slug character varying(2000),
    keywords_string character varying(500) NOT NULL,
    site_id integer NOT NULL,
    gen_description boolean NOT NULL,
    in_menus character varying(100),
    _meta_title character varying(500),
    in_sitemap boolean NOT NULL,
    created timestamp with time zone,
    updated timestamp with time zone
);


ALTER TABLE public.pages_page OWNER TO postgres;

--
-- Name: pages_page_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE pages_page_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pages_page_id_seq OWNER TO postgres;

--
-- Name: pages_page_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE pages_page_id_seq OWNED BY pages_page.id;


--
-- Name: pages_richtextpage; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pages_richtextpage (
    content text NOT NULL,
    page_ptr_id integer NOT NULL
);


ALTER TABLE public.pages_richtextpage OWNER TO postgres;

--
-- Name: south_migrationhistory; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE south_migrationhistory (
    id integer NOT NULL,
    app_name character varying(255) NOT NULL,
    migration character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.south_migrationhistory OWNER TO postgres;

--
-- Name: south_migrationhistory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE south_migrationhistory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.south_migrationhistory_id_seq OWNER TO postgres;

--
-- Name: south_migrationhistory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE south_migrationhistory_id_seq OWNED BY south_migrationhistory.id;


--
-- Name: tastypie_apiaccess; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tastypie_apiaccess (
    id integer NOT NULL,
    identifier character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    request_method character varying(10) NOT NULL,
    accessed integer NOT NULL,
    CONSTRAINT tastypie_apiaccess_accessed_check CHECK ((accessed >= 0))
);


ALTER TABLE public.tastypie_apiaccess OWNER TO postgres;

--
-- Name: tastypie_apiaccess_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tastypie_apiaccess_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tastypie_apiaccess_id_seq OWNER TO postgres;

--
-- Name: tastypie_apiaccess_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tastypie_apiaccess_id_seq OWNED BY tastypie_apiaccess.id;


--
-- Name: tastypie_apikey; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tastypie_apikey (
    id integer NOT NULL,
    user_id integer NOT NULL,
    key character varying(256) NOT NULL,
    created timestamp with time zone NOT NULL
);


ALTER TABLE public.tastypie_apikey OWNER TO postgres;

--
-- Name: tastypie_apikey_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tastypie_apikey_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tastypie_apikey_id_seq OWNER TO postgres;

--
-- Name: tastypie_apikey_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tastypie_apikey_id_seq OWNED BY tastypie_apikey.id;


--
-- Name: theme_homepage; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE theme_homepage (
    page_ptr_id integer NOT NULL,
    heading character varying(100) NOT NULL,
    slide_in_one_icon character varying(50) NOT NULL,
    slide_in_one character varying(200) NOT NULL,
    slide_in_two_icon character varying(50) NOT NULL,
    slide_in_two character varying(200) NOT NULL,
    slide_in_three_icon character varying(50) NOT NULL,
    slide_in_three character varying(200) NOT NULL,
    header_background character varying(255) NOT NULL,
    header_image character varying(255),
    welcome_heading character varying(100) NOT NULL,
    content text NOT NULL,
    recent_blog_heading character varying(100) NOT NULL,
    number_recent_posts integer NOT NULL,
    CONSTRAINT theme_homepage_number_recent_posts_check CHECK ((number_recent_posts >= 0))
);


ALTER TABLE public.theme_homepage OWNER TO postgres;

--
-- Name: theme_iconbox; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE theme_iconbox (
    id integer NOT NULL,
    _order integer,
    homepage_id integer NOT NULL,
    icon character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    link_text character varying(100) NOT NULL,
    link character varying(2000) NOT NULL
);


ALTER TABLE public.theme_iconbox OWNER TO postgres;

--
-- Name: theme_iconbox_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE theme_iconbox_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.theme_iconbox_id_seq OWNER TO postgres;

--
-- Name: theme_iconbox_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE theme_iconbox_id_seq OWNED BY theme_iconbox.id;


--
-- Name: theme_siteconfiguration; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE theme_siteconfiguration (
    id integer NOT NULL,
    site_id integer NOT NULL,
    col1_heading character varying(200) NOT NULL,
    col1_content text NOT NULL,
    col2_heading character varying(200) NOT NULL,
    col2_content text NOT NULL,
    col3_heading character varying(200) NOT NULL,
    col3_content text NOT NULL,
    twitter_link character varying(2000) NOT NULL,
    facebook_link character varying(2000) NOT NULL,
    pinterest_link character varying(2000) NOT NULL,
    youtube_link character varying(2000) NOT NULL,
    github_link character varying(2000) NOT NULL,
    linkedin_link character varying(2000) NOT NULL,
    vk_link character varying(2000) NOT NULL,
    gplus_link character varying(2000) NOT NULL,
    has_social_network_links boolean NOT NULL,
    copyright text NOT NULL
);


ALTER TABLE public.theme_siteconfiguration OWNER TO postgres;

--
-- Name: theme_siteconfiguration_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE theme_siteconfiguration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.theme_siteconfiguration_id_seq OWNER TO postgres;

--
-- Name: theme_siteconfiguration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE theme_siteconfiguration_id_seq OWNED BY theme_siteconfiguration.id;


--
-- Name: theme_userprofile; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE theme_userprofile (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying(1024),
    profession character varying(1024),
    subject_areas character varying(1024),
    organization character varying(1024),
    organization_type character varying(1024),
    phone_1 character varying(1024),
    phone_1_type character varying(1024),
    phone_2 character varying(1024),
    phone_2_type character varying(1024),
    public boolean NOT NULL,
    picture character varying(100),
    cv character varying(100),
    details text
);


ALTER TABLE public.theme_userprofile OWNER TO postgres;

--
-- Name: theme_userprofile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE theme_userprofile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.theme_userprofile_id_seq OWNER TO postgres;

--
-- Name: theme_userprofile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE theme_userprofile_id_seq OWNED BY theme_userprofile.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group ALTER COLUMN id SET DEFAULT nextval('auth_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('auth_group_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user ALTER COLUMN id SET DEFAULT nextval('auth_user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_groups ALTER COLUMN id SET DEFAULT nextval('auth_user_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('auth_user_user_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogcategory ALTER COLUMN id SET DEFAULT nextval('blog_blogcategory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost ALTER COLUMN id SET DEFAULT nextval('blog_blogpost_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost_categories ALTER COLUMN id SET DEFAULT nextval('blog_blogpost_categories_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost_related_posts ALTER COLUMN id SET DEFAULT nextval('blog_blogpost_related_posts_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY celery_taskmeta ALTER COLUMN id SET DEFAULT nextval('celery_taskmeta_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY celery_tasksetmeta ALTER COLUMN id SET DEFAULT nextval('celery_tasksetmeta_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY conf_setting ALTER COLUMN id SET DEFAULT nextval('conf_setting_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY core_sitepermission ALTER COLUMN id SET DEFAULT nextval('core_sitepermission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY core_sitepermission_sites ALTER COLUMN id SET DEFAULT nextval('core_sitepermission_sites_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comment_flags ALTER COLUMN id SET DEFAULT nextval('django_comment_flags_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comments ALTER COLUMN id SET DEFAULT nextval('django_comments_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_irods_rodsenvironment ALTER COLUMN id SET DEFAULT nextval('django_irods_rodsenvironment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_redirect ALTER COLUMN id SET DEFAULT nextval('django_redirect_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_site ALTER COLUMN id SET DEFAULT nextval('django_site_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_crontabschedule ALTER COLUMN id SET DEFAULT nextval('djcelery_crontabschedule_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_intervalschedule ALTER COLUMN id SET DEFAULT nextval('djcelery_intervalschedule_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_periodictask ALTER COLUMN id SET DEFAULT nextval('djcelery_periodictask_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_taskstate ALTER COLUMN id SET DEFAULT nextval('djcelery_taskstate_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_workerstate ALTER COLUMN id SET DEFAULT nextval('djcelery_workerstate_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelement ALTER COLUMN id SET DEFAULT nextval('dublincore_qualifieddublincoreelement_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelementhistory ALTER COLUMN id SET DEFAULT nextval('dublincore_qualifieddublincoreelementhistory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_field ALTER COLUMN id SET DEFAULT nextval('forms_field_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_fieldentry ALTER COLUMN id SET DEFAULT nextval('forms_fieldentry_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_formentry ALTER COLUMN id SET DEFAULT nextval('forms_formentry_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_irods_rodsenvironment ALTER COLUMN id SET DEFAULT nextval('ga_irods_rodsenvironment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_orderedresource ALTER COLUMN id SET DEFAULT nextval('ga_resources_orderedresource_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer_styles ALTER COLUMN id SET DEFAULT nextval('ga_resources_renderedlayer_styles_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY galleries_galleryimage ALTER COLUMN id SET DEFAULT nextval('galleries_galleryimage_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_assignedkeyword ALTER COLUMN id SET DEFAULT nextval('generic_assignedkeyword_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_keyword ALTER COLUMN id SET DEFAULT nextval('generic_keyword_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_rating ALTER COLUMN id SET DEFAULT nextval('generic_rating_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_bags ALTER COLUMN id SET DEFAULT nextval('hs_core_bags_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_contributor ALTER COLUMN id SET DEFAULT nextval('hs_core_contributor_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_coremetadata ALTER COLUMN id SET DEFAULT nextval('hs_core_coremetadata_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_coverage ALTER COLUMN id SET DEFAULT nextval('hs_core_coverage_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_creator ALTER COLUMN id SET DEFAULT nextval('hs_core_creator_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_date ALTER COLUMN id SET DEFAULT nextval('hs_core_date_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_description ALTER COLUMN id SET DEFAULT nextval('hs_core_description_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_externalprofilelink ALTER COLUMN id SET DEFAULT nextval('hs_core_externalprofilelink_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_format ALTER COLUMN id SET DEFAULT nextval('hs_core_format_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_groups ALTER COLUMN id SET DEFAULT nextval('hs_core_genericresource_edit_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_users ALTER COLUMN id SET DEFAULT nextval('hs_core_genericresource_edit_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_owners ALTER COLUMN id SET DEFAULT nextval('hs_core_genericresource_owners_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_view_groups ALTER COLUMN id SET DEFAULT nextval('hs_core_genericresource_view_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_view_users ALTER COLUMN id SET DEFAULT nextval('hs_core_genericresource_view_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_groupownership ALTER COLUMN id SET DEFAULT nextval('hs_core_groupownership_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_identifier ALTER COLUMN id SET DEFAULT nextval('hs_core_identifier_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_language ALTER COLUMN id SET DEFAULT nextval('hs_core_language_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_publisher ALTER COLUMN id SET DEFAULT nextval('hs_core_publisher_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_relation ALTER COLUMN id SET DEFAULT nextval('hs_core_relation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_resourcefile ALTER COLUMN id SET DEFAULT nextval('hs_core_resourcefile_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_rights ALTER COLUMN id SET DEFAULT nextval('hs_core_rights_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_source ALTER COLUMN id SET DEFAULT nextval('hs_core_source_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_subject ALTER COLUMN id SET DEFAULT nextval('hs_core_subject_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_title ALTER COLUMN id SET DEFAULT nextval('hs_core_title_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_type ALTER COLUMN id SET DEFAULT nextval('hs_core_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_choicetype ALTER COLUMN id SET DEFAULT nextval('hs_party_choicetype_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_city ALTER COLUMN id SET DEFAULT nextval('hs_party_city_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_country ALTER COLUMN id SET DEFAULT nextval('hs_party_country_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_externalorgidentifier ALTER COLUMN id SET DEFAULT nextval('hs_party_externalorgidentifier_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationassociation ALTER COLUMN id SET DEFAULT nextval('hs_party_organizationassociation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationemail ALTER COLUMN id SET DEFAULT nextval('hs_party_organizationemail_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationlocation ALTER COLUMN id SET DEFAULT nextval('hs_party_organizationlocation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationname ALTER COLUMN id SET DEFAULT nextval('hs_party_organizationname_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationphone ALTER COLUMN id SET DEFAULT nextval('hs_party_organizationphone_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_othername ALTER COLUMN id SET DEFAULT nextval('hs_party_othername_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_party ALTER COLUMN id SET DEFAULT nextval('hs_party_party_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personemail ALTER COLUMN id SET DEFAULT nextval('hs_party_personemail_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personexternalidentifier ALTER COLUMN id SET DEFAULT nextval('hs_party_personexternalidentifier_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personlocation ALTER COLUMN id SET DEFAULT nextval('hs_party_personlocation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personphone ALTER COLUMN id SET DEFAULT nextval('hs_party_personphone_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_region ALTER COLUMN id SET DEFAULT nextval('hs_party_region_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_city ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_city_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_country ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_country_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_externalidentifiers ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_externalidentifiers_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_externalorgidentifiers ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_externalorgidentifiers_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organization ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_organization_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organizationemail ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_organizationemail_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organizationlocation ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_organizationlocation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organizationphone ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_organizationphone_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_orgassociations ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_orgassociations_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_othernames ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_othernames_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_person ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_person_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_personemail ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_personemail_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_personlocation ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_personlocation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_personphone ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_personphone_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_region ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_region_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_userdemographics ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_userdemographics_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_userkeywords ALTER COLUMN id SET DEFAULT nextval('hs_scholar_profile_userkeywords_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_page ALTER COLUMN id SET DEFAULT nextval('pages_page_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY south_migrationhistory ALTER COLUMN id SET DEFAULT nextval('south_migrationhistory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tastypie_apiaccess ALTER COLUMN id SET DEFAULT nextval('tastypie_apiaccess_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tastypie_apikey ALTER COLUMN id SET DEFAULT nextval('tastypie_apikey_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_iconbox ALTER COLUMN id SET DEFAULT nextval('theme_iconbox_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_siteconfiguration ALTER COLUMN id SET DEFAULT nextval('theme_siteconfiguration_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_userprofile ALTER COLUMN id SET DEFAULT nextval('theme_userprofile_id_seq'::regclass);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_group (id, name) FROM stdin;
1	Hydroshare Author
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_group_id_seq', 1, true);


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_group_permissions (id, group_id, permission_id) FROM stdin;
38	1	22
39	1	23
40	1	24
41	1	25
42	1	26
43	1	27
44	1	34
45	1	35
46	1	36
47	1	37
48	1	38
49	1	39
50	1	40
51	1	50
52	1	51
53	1	52
54	1	56
55	1	57
56	1	58
57	1	65
58	1	66
59	1	67
60	1	68
61	1	69
62	1	70
63	1	71
64	1	72
65	1	73
66	1	74
67	1	75
68	1	76
69	1	95
70	1	96
71	1	97
\.


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', 71, true);


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add permission	1	add_permission
2	Can change permission	1	change_permission
3	Can delete permission	1	delete_permission
4	Can add group	2	add_group
5	Can change group	2	change_group
6	Can delete group	2	delete_group
7	Can add user	3	add_user
8	Can change user	3	change_user
9	Can delete user	3	delete_user
10	Can add content type	4	add_contenttype
11	Can change content type	4	change_contenttype
12	Can delete content type	4	delete_contenttype
13	Can add redirect	5	add_redirect
14	Can change redirect	5	change_redirect
15	Can delete redirect	5	delete_redirect
16	Can add session	6	add_session
17	Can change session	6	change_session
18	Can delete session	6	delete_session
19	Can add site	7	add_site
20	Can change site	7	change_site
21	Can delete site	7	delete_site
22	Can add qualified dublin core element	8	add_qualifieddublincoreelement
23	Can change qualified dublin core element	8	change_qualifieddublincoreelement
24	Can delete qualified dublin core element	8	delete_qualifieddublincoreelement
25	Can add qualified dublin core element history	9	add_qualifieddublincoreelementhistory
26	Can change qualified dublin core element history	9	change_qualifieddublincoreelementhistory
27	Can delete qualified dublin core element history	9	delete_qualifieddublincoreelementhistory
28	Can add migration history	10	add_migrationhistory
29	Can change migration history	10	change_migrationhistory
30	Can delete migration history	10	delete_migrationhistory
31	Can add log entry	11	add_logentry
32	Can change log entry	11	change_logentry
33	Can delete log entry	11	delete_logentry
34	Can add comment	12	add_comment
35	Can change comment	12	change_comment
36	Can delete comment	12	delete_comment
37	Can moderate comments	12	can_moderate
38	Can add comment flag	13	add_commentflag
39	Can change comment flag	13	change_commentflag
40	Can delete comment flag	13	delete_commentflag
41	Can add rods environment	14	add_rodsenvironment
42	Can change rods environment	14	change_rodsenvironment
43	Can delete rods environment	14	delete_rodsenvironment
44	Can add Setting	15	add_setting
45	Can change Setting	15	change_setting
46	Can delete Setting	15	delete_setting
47	Can add Site permission	16	add_sitepermission
48	Can change Site permission	16	change_sitepermission
49	Can delete Site permission	16	delete_sitepermission
50	Can add Page	17	add_page
51	Can change Page	17	change_page
52	Can delete Page	17	delete_page
53	Can add Rich text page	18	add_richtextpage
54	Can change Rich text page	18	change_richtextpage
55	Can delete Rich text page	18	delete_richtextpage
56	Can add Link	19	add_link
57	Can change Link	19	change_link
58	Can delete Link	19	delete_link
59	Can add Blog post	20	add_blogpost
60	Can change Blog post	20	change_blogpost
61	Can delete Blog post	20	delete_blogpost
62	Can add Blog Category	21	add_blogcategory
63	Can change Blog Category	21	change_blogcategory
64	Can delete Blog Category	21	delete_blogcategory
65	Can add Comment	22	add_threadedcomment
66	Can change Comment	22	change_threadedcomment
67	Can delete Comment	22	delete_threadedcomment
68	Can add Keyword	23	add_keyword
69	Can change Keyword	23	change_keyword
70	Can delete Keyword	23	delete_keyword
71	Can add assigned keyword	24	add_assignedkeyword
72	Can change assigned keyword	24	change_assignedkeyword
73	Can delete assigned keyword	24	delete_assignedkeyword
74	Can add Rating	25	add_rating
75	Can change Rating	25	change_rating
76	Can delete Rating	25	delete_rating
77	Can add Form	26	add_form
78	Can change Form	26	change_form
79	Can delete Form	26	delete_form
80	Can add Field	27	add_field
81	Can change Field	27	change_field
82	Can delete Field	27	delete_field
83	Can add Form entry	28	add_formentry
84	Can change Form entry	28	change_formentry
85	Can delete Form entry	28	delete_formentry
86	Can add Form field entry	29	add_fieldentry
87	Can change Form field entry	29	change_fieldentry
88	Can delete Form field entry	29	delete_fieldentry
89	Can add Gallery	30	add_gallery
90	Can change Gallery	30	change_gallery
91	Can delete Gallery	30	delete_gallery
92	Can add Image	31	add_galleryimage
93	Can change Image	31	change_galleryimage
94	Can delete Image	31	delete_galleryimage
95	Can add Generic Hydroshare Resource	32	add_genericresource
96	Can change Generic Hydroshare Resource	32	change_genericresource
97	Can delete Generic Hydroshare Resource	32	delete_genericresource
98	Can add task state	33	add_taskmeta
99	Can change task state	33	change_taskmeta
100	Can delete task state	33	delete_taskmeta
101	Can add saved group result	34	add_tasksetmeta
102	Can change saved group result	34	change_tasksetmeta
103	Can delete saved group result	34	delete_tasksetmeta
104	Can add interval	35	add_intervalschedule
105	Can change interval	35	change_intervalschedule
106	Can delete interval	35	delete_intervalschedule
107	Can add crontab	36	add_crontabschedule
108	Can change crontab	36	change_crontabschedule
109	Can delete crontab	36	delete_crontabschedule
110	Can add periodic tasks	37	add_periodictasks
111	Can change periodic tasks	37	change_periodictasks
112	Can delete periodic tasks	37	delete_periodictasks
113	Can add periodic task	38	add_periodictask
114	Can change periodic task	38	change_periodictask
115	Can delete periodic task	38	delete_periodictask
116	Can add worker	39	add_workerstate
117	Can change worker	39	change_workerstate
118	Can delete worker	39	delete_workerstate
119	Can add task	40	add_taskstate
120	Can change task	40	change_taskstate
121	Can delete task	40	delete_taskstate
122	Can add catalog page	41	add_catalogpage
123	Can change catalog page	41	change_catalogpage
124	Can delete catalog page	41	delete_catalogpage
125	Can add data resource	42	add_dataresource
126	Can change data resource	42	change_dataresource
127	Can delete data resource	42	delete_dataresource
128	Can add ordered resource	43	add_orderedresource
129	Can change ordered resource	43	change_orderedresource
130	Can delete ordered resource	43	delete_orderedresource
131	Can add resource group	44	add_resourcegroup
132	Can change resource group	44	change_resourcegroup
133	Can delete resource group	44	delete_resourcegroup
134	Can add related resource	45	add_relatedresource
135	Can change related resource	45	change_relatedresource
136	Can delete related resource	45	delete_relatedresource
137	Can add style	46	add_style
138	Can change style	46	change_style
139	Can delete style	46	delete_style
140	Can add rendered layer	47	add_renderedlayer
141	Can change rendered layer	47	change_renderedlayer
142	Can delete rendered layer	47	delete_renderedlayer
143	Can add api access	48	add_apiaccess
144	Can change api access	48	change_apiaccess
145	Can delete api access	48	delete_apiaccess
146	Can add api key	49	add_apikey
147	Can change api key	49	change_apikey
148	Can delete api key	49	delete_apikey
149	Can add Site Configuration	50	add_siteconfiguration
150	Can change Site Configuration	50	change_siteconfiguration
151	Can delete Site Configuration	50	delete_siteconfiguration
152	Can add Home page	51	add_homepage
153	Can change Home page	51	change_homepage
154	Can delete Home page	51	delete_homepage
155	Can add icon box	52	add_iconbox
156	Can change icon box	52	change_iconbox
157	Can delete icon box	52	delete_iconbox
158	Can add group ownership	53	add_groupownership
159	Can change group ownership	53	change_groupownership
160	Can delete group ownership	53	delete_groupownership
161	Can add resource file	54	add_resourcefile
162	Can change resource file	54	change_resourcefile
163	Can delete resource file	54	delete_resourcefile
164	Can add bags	55	add_bags
165	Can change bags	55	change_bags
166	Can delete bags	55	delete_bags
167	Can add city	56	add_city
168	Can change city	56	change_city
169	Can delete city	56	delete_city
170	Can add region	57	add_region
171	Can change region	57	change_region
172	Can delete region	57	delete_region
173	Can add country	58	add_country
174	Can change country	58	change_country
175	Can delete country	58	delete_country
176	Can add organization	59	add_organization
177	Can change organization	59	change_organization
178	Can delete organization	59	delete_organization
179	Can add person	60	add_person
180	Can change person	60	change_person
181	Can delete person	60	delete_person
182	Can add person email	61	add_personemail
183	Can change person email	61	change_personemail
184	Can delete person email	61	delete_personemail
185	Can add person location	62	add_personlocation
186	Can change person location	62	change_personlocation
187	Can delete person location	62	delete_personlocation
188	Can add person phone	63	add_personphone
189	Can change person phone	63	change_personphone
190	Can delete person phone	63	delete_personphone
191	Can add user keywords	64	add_userkeywords
192	Can change user keywords	64	change_userkeywords
193	Can delete user keywords	64	delete_userkeywords
194	Can add user demographics	65	add_userdemographics
195	Can change user demographics	65	change_userdemographics
196	Can delete user demographics	65	delete_userdemographics
197	Can add other names	66	add_othernames
198	Can change other names	66	change_othernames
199	Can delete other names	66	delete_othernames
200	Can add organization email	67	add_organizationemail
201	Can change organization email	67	change_organizationemail
202	Can delete organization email	67	delete_organizationemail
203	Can add organization location	68	add_organizationlocation
204	Can change organization location	68	change_organizationlocation
205	Can delete organization location	68	delete_organizationlocation
206	Can add organization phone	69	add_organizationphone
207	Can change organization phone	69	change_organizationphone
208	Can delete organization phone	69	delete_organizationphone
209	Can add external org identifiers	70	add_externalorgidentifiers
210	Can change external org identifiers	70	change_externalorgidentifiers
211	Can delete external org identifiers	70	delete_externalorgidentifiers
212	Can add org associations	71	add_orgassociations
213	Can change org associations	71	change_orgassociations
214	Can delete org associations	71	delete_orgassociations
215	Can add external identifiers	72	add_externalidentifiers
216	Can change external identifiers	72	change_externalidentifiers
217	Can delete external identifiers	72	delete_externalidentifiers
218	Can add scholar	73	add_scholar
219	Can change scholar	73	change_scholar
220	Can delete scholar	73	delete_scholar
221	Can add scholar external identifiers	74	add_scholarexternalidentifiers
222	Can change scholar external identifiers	74	change_scholarexternalidentifiers
223	Can delete scholar external identifiers	74	delete_scholarexternalidentifiers
224	Can add scholar group	75	add_scholargroup
225	Can change scholar group	75	change_scholargroup
226	Can delete scholar group	75	delete_scholargroup
227	Can add user profile	76	add_userprofile
228	Can change user profile	76	change_userprofile
229	Can delete user profile	76	delete_userprofile
230	Can add external profile link	77	add_externalprofilelink
231	Can change external profile link	77	change_externalprofilelink
232	Can delete external profile link	77	delete_externalprofilelink
233	Can add contributor	78	add_contributor
234	Can change contributor	78	change_contributor
235	Can delete contributor	78	delete_contributor
236	Can add creator	79	add_creator
237	Can change creator	79	change_creator
238	Can delete creator	79	delete_creator
239	Can add description	80	add_description
240	Can change description	80	change_description
241	Can delete description	80	delete_description
242	Can add title	81	add_title
243	Can change title	81	change_title
244	Can delete title	81	delete_title
245	Can add type	82	add_type
246	Can change type	82	change_type
247	Can delete type	82	delete_type
248	Can add date	83	add_date
249	Can change date	83	change_date
250	Can delete date	83	delete_date
251	Can add relation	84	add_relation
252	Can change relation	84	change_relation
253	Can delete relation	84	delete_relation
254	Can add identifier	85	add_identifier
255	Can change identifier	85	change_identifier
256	Can delete identifier	85	delete_identifier
257	Can add publisher	86	add_publisher
258	Can change publisher	86	change_publisher
259	Can delete publisher	86	delete_publisher
260	Can add language	87	add_language
261	Can change language	87	change_language
262	Can delete language	87	delete_language
263	Can add coverage	88	add_coverage
264	Can change coverage	88	change_coverage
265	Can delete coverage	88	delete_coverage
266	Can add format	89	add_format
267	Can change format	89	change_format
268	Can delete format	89	delete_format
269	Can add subject	90	add_subject
270	Can change subject	90	change_subject
271	Can delete subject	90	delete_subject
272	Can add source	91	add_source
273	Can change source	91	change_source
274	Can delete source	91	delete_source
275	Can add rights	92	add_rights
276	Can change rights	92	change_rights
277	Can delete rights	92	delete_rights
278	Can add core meta data	93	add_coremetadata
279	Can change core meta data	93	change_coremetadata
280	Can delete core meta data	93	delete_coremetadata
281	Can add iRODS Environment	94	add_rodsenvironment
282	Can change iRODS Environment	94	change_rodsenvironment
283	Can delete iRODS Environment	94	delete_rodsenvironment
\.


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_permission_id_seq', 283, true);


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$12000$qfCKgKUpG7Ll$qZlFYDvd94gill0ulJ/q1u+q2x9inygztWMrfXg0Q4o=	2014-08-13 18:33:01.182439+00	t	admin			example@example.com	t	t	2014-08-13 18:33:01.182439+00
2	pbkdf2_sha256$12000$jqsyb4vzAyvj$sXei14hBBR8oEJN5dp5jTkr4YBHLdCWQII2yqV3Ejx8=	2014-08-13 18:34:06.437778+00	t	root			info@hydroshare.org	t	t	2014-08-13 18:33:59.363301+00
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user_groups (id, user_id, group_id) FROM stdin;
1	5	1
2	8	1
3	9	1
4	6	1
5	10	1
8	12	1
10	2	1
14	3	1
16	30	1
17	29	1
18	17	1
20	32	1
21	33	1
23	34	1
25	35	1
27	37	1
28	38	1
29	39	1
31	40	1
32	41	1
\.


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_user_groups_id_seq', 32, true);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_user_id_seq', 41, true);


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
1	4	34
2	4	35
3	4	36
4	4	37
5	4	38
6	4	39
7	4	40
8	4	50
9	4	51
10	4	52
11	4	53
12	4	54
13	4	55
14	4	56
15	4	57
16	4	58
17	4	65
18	4	66
19	4	67
20	4	68
21	4	69
22	4	70
23	4	71
24	4	72
25	4	73
26	4	74
27	4	75
28	4	76
29	4	95
30	4	96
31	4	97
\.


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_user_user_permissions_id_seq', 31, true);


--
-- Data for Name: blog_blogcategory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY blog_blogcategory (slug, id, title, site_id) FROM stdin;
\.


--
-- Name: blog_blogcategory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('blog_blogcategory_id_seq', 1, false);


--
-- Data for Name: blog_blogpost; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY blog_blogpost (status, description, title, short_url, id, content, expiry_date, publish_date, user_id, slug, comments_count, keywords_string, site_id, rating_average, rating_count, allow_comments, featured_image, gen_description, _meta_title, in_sitemap, rating_sum, created, updated) FROM stdin;
\.


--
-- Data for Name: blog_blogpost_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY blog_blogpost_categories (id, blogpost_id, blogcategory_id) FROM stdin;
\.


--
-- Name: blog_blogpost_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('blog_blogpost_categories_id_seq', 1, false);


--
-- Name: blog_blogpost_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('blog_blogpost_id_seq', 1, false);


--
-- Data for Name: blog_blogpost_related_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY blog_blogpost_related_posts (id, from_blogpost_id, to_blogpost_id) FROM stdin;
\.


--
-- Name: blog_blogpost_related_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('blog_blogpost_related_posts_id_seq', 1, false);


--
-- Data for Name: celery_taskmeta; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY celery_taskmeta (id, task_id, status, result, date_done, traceback, hidden, meta) FROM stdin;
\.


--
-- Name: celery_taskmeta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('celery_taskmeta_id_seq', 1, false);


--
-- Data for Name: celery_tasksetmeta; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY celery_tasksetmeta (id, taskset_id, result, date_done, hidden) FROM stdin;
\.


--
-- Name: celery_tasksetmeta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('celery_tasksetmeta_id_seq', 1, false);


--
-- Data for Name: conf_setting; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY conf_setting (id, value, name, site_id) FROM stdin;
\.


--
-- Name: conf_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('conf_setting_id_seq', 1, false);


--
-- Data for Name: core_sitepermission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY core_sitepermission (id, user_id) FROM stdin;
1	4
2	5
3	8
4	9
5	6
6	10
7	12
8	2
13	3
16	30
17	29
18	17
19	31
20	32
21	33
22	34
23	35
24	37
25	38
26	39
27	40
28	41
\.


--
-- Name: core_sitepermission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('core_sitepermission_id_seq', 28, true);


--
-- Data for Name: core_sitepermission_sites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY core_sitepermission_sites (id, sitepermission_id, site_id) FROM stdin;
1	1	1
2	2	1
3	3	1
4	4	1
5	5	1
6	6	1
7	7	1
8	8	1
13	13	1
16	16	1
17	17	1
18	18	1
19	19	1
20	20	1
21	21	1
22	22	1
23	23	1
24	24	1
25	25	1
26	26	1
27	27	1
28	28	1
\.


--
-- Name: core_sitepermission_sites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('core_sitepermission_sites_id_seq', 28, true);


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_admin_log (id, action_time, user_id, content_type_id, object_id, object_repr, action_flag, change_message) FROM stdin;
1	2014-02-05 17:06:43.050672+00	2	32	1	Generic Hydroshare Resource	1	
2	2014-02-05 17:07:06.190195+00	2	7	1	dev.hydroshare.org	2	Changed domain.
3	2014-02-05 17:07:55.572997+00	2	17	1	Generic Hydroshare Resource	2	Changed keywords and id.
4	2014-02-05 17:09:42.171202+00	2	8	1	Title = Generic Hydroshare Resource	1	
5	2014-02-05 17:13:22.985164+00	2	3	4	danames	2	Changed is_staff and user_permissions.
6	2014-02-05 17:14:34.350421+00	2	2	1	Hydroshare Author	1	
7	2014-02-05 17:14:48.772056+00	2	3	5	Castronova	2	Changed is_staff and groups.
8	2014-02-05 17:15:00.979685+00	2	3	8	carolxsong	2	Changed is_staff and groups.
9	2014-02-05 17:15:18.876467+00	2	3	9	horsburgh	2	Changed is_staff and groups.
10	2014-02-05 17:15:30.751591+00	2	3	6	martinn	2	Changed is_staff and groups.
11	2014-02-05 17:15:40.120893+00	2	3	7	rayi	2	Changed is_staff and is_superuser.
12	2014-02-05 17:16:48.375803+00	2	32	1	Generic Hydroshare Resource	3	
13	2014-02-05 17:26:45.460456+00	2	32	2	Resource	1	
14	2014-02-10 16:28:43.350632+00	2	17	2	Resource	2	Changed keywords and id.
15	2014-02-10 16:29:05.504999+00	2	32	2	Resource	2	Changed keywords.
16	2014-02-10 16:34:49.016056+00	2	32	2	Resource	2	Changed keywords. Added qualified dublin core element "Title = Resource". Added qualified dublin core element "Creator = Jefferson Heard".
17	2014-02-10 16:36:19.778084+00	2	32	2	Resource	2	Changed content and id.
18	2014-02-10 17:08:40.975345+00	2	32	2	Resource	2	Changed do_not_distribute and id.
19	2014-02-12 13:44:52.168916+00	2	3	10	jamy	2	Changed is_staff and groups.
20	2014-02-12 15:38:41.665526+00	10	32	4	Test file	1	
21	2014-02-12 15:42:06.499006+00	10	32	4	Test file	2	Changed content, resource_file and keywords.
22	2014-02-12 15:42:26.79925+00	10	32	4	Test file	2	Changed content and keywords. Added qualified dublin core element "Creator = Tian Gan".
23	2014-02-26 17:44:48.801579+00	14	32	2	Resource	2	Changed content, description and keywords. Added qualified dublin core element "Abstract:is = This is the abstract".
24	2014-02-27 16:32:07.133525+00	10	32	4	Test file	2	Changed content and keywords. Added qualified dublin core element "Abstract = This is an abstract test".
25	2014-02-28 16:54:53.489612+00	14	3	11	shaunjl	2	Changed is_staff and is_superuser.
26	2014-03-04 20:45:47.457777+00	10	32	4	Test file	2	Changed content, resource_file and keywords.
27	2014-03-04 20:46:00.298002+00	10	32	4	Test file	2	Changed content and keywords.
28	2014-03-04 20:48:58.21964+00	10	32	4	Test file	2	Changed content and keywords. Added qualified dublin core element "Publisher = HydroShare, http://hydroshare.org".
29	2014-03-04 20:49:48.325717+00	10	32	4	Test file	2	Changed content and keywords.
30	2014-03-04 23:57:27.053497+00	10	32	4	Test file	2	Changed public and id.
31	2014-03-05 16:13:51.838365+00	14	18	5	Homepage	2	Changed title, slug and keywords.
32	2014-03-05 16:14:25.403024+00	14	17	5	Homepage	3	
33	2014-03-05 16:16:07.86021+00	14	51	6	Home	1	
34	2014-03-05 16:46:17.356063+00	14	32	2	Resource	2	Changed content, description and keywords.
35	2014-03-05 16:46:56.560631+00	14	32	7	Resource2	1	
36	2014-03-05 16:47:52.286942+00	14	17	2	Resource	3	
37	2014-03-05 16:48:00.887595+00	14	17	4	Test file	3	
38	2014-03-12 14:05:28.31722+00	14	32	7	Resource2	2	Changed content, resource_file, description and keywords.
39	2014-03-12 14:16:21.955748+00	14	32	9	Non-public Resource	1	
40	2014-03-12 16:30:35.202066+00	14	3	12	dtarb	2	Changed is_staff and groups.
41	2014-03-12 16:30:47.981549+00	14	3	3	jeff	2	Changed is_staff, is_superuser and groups.
42	2014-03-19 16:14:13.803024+00	14	3	12	dtarb	2	Changed is_superuser.
43	2014-03-20 12:10:30.008359+00	12	42	10	PI Meeting Poster	1	
44	2014-03-24 22:20:58.986531+00	12	32	11	Software carpentry readme.txt	1	
45	2014-03-26 00:54:21.447696+00	10	32	12	Large file test	1	
46	2014-03-26 12:45:51.853385+00	12	32	11	Software carpentry readme.txt	2	Changed discoverable and id.
47	2014-03-26 12:50:40.177039+00	12	42	10	PI Meeting Poster	3	
48	2014-03-26 13:07:52.539311+00	12	32	13	Eel River TauDEM analysis	1	
49	2014-03-26 13:21:35.195991+00	12	32	14	Logan DEM Demo	1	
50	2014-03-26 13:23:23.879331+00	12	32	14	Logan DEM Demo	2	Changed in_menus and keywords.
51	2014-03-26 15:00:36.22984+00	14	32	11	Software carpentry readme.txt	2	Changed in_menus and keywords.
52	2014-03-26 15:00:57.41674+00	14	51	6	Home	2	Changed header_background, header_image, slug and keywords.
53	2014-03-26 15:51:47.24234+00	14	18	15	Resources	1	
54	2014-03-26 15:52:11.301897+00	14	18	15	Resources	3	
55	2014-03-31 17:32:58.568402+00	10	32	12	Large file test	3	
56	2014-04-07 17:02:44.400057+00	14	51	6	Home	2	Changed heading and id.
57	2014-04-07 17:03:11.552042+00	14	51	6	Home	2	Changed welcome_heading and id.
58	2014-04-07 17:03:34.817473+00	14	51	6	Home	2	Changed content and id.
59	2014-04-07 17:03:48.575382+00	14	51	6	Home	2	Changed heading and id.
60	2014-04-07 17:06:53.447638+00	14	51	6	Home	2	Changed slide_in_one_icon and id.
61	2014-04-10 22:35:03.186259+00	12	32	16	CubDemo DEM	1	
62	2014-04-10 22:35:41.495102+00	12	32	16	CubDemo DEM	2	Changed in_menus and keywords.
63	2014-04-16 15:21:43.624714+00	2	41	17	Resources	1	
64	2014-04-16 15:24:10.861037+00	2	32	18	Resources / Generic Resource Test	1	
65	2014-04-29 19:00:55.540942+00	14	51	6	Home	2	Changed header_background, header_image, content and keywords.
66	2014-04-29 19:01:32.821668+00	14	18	19	My Resources	1	
67	2014-04-29 19:02:27.56805+00	14	18	20	Explore	1	
68	2014-04-29 19:02:40.295681+00	14	18	21	Collaborate	1	
69	2014-04-29 19:02:56.724072+00	14	18	22	Support	1	
70	2014-04-29 19:03:05.14542+00	14	41	17	Resources	2	Changed in_menus and keywords.
71	2014-04-29 19:03:29.993466+00	14	51	6	Home	2	Changed slide_in_one_icon and id.
72	2014-05-05 15:37:01.89392+00	14	50	1	SiteConfiguration object	2	Changed copyright and id.
73	2014-05-05 15:38:19.101879+00	14	50	1	SiteConfiguration object	2	Changed col3_heading, col3_content and id.
74	2014-05-05 15:39:05.908898+00	14	50	1	SiteConfiguration object	2	Changed col3_content and id.
75	2014-05-05 16:00:24.73329+00	14	50	1	SiteConfiguration object	2	Changed col1_content, col3_content, twitter_link, youtube_link, github_link, gplus_link and has_social_network_links.
76	2014-05-05 19:40:28.565716+00	14	18	23	Verify account	1	
77	2014-05-05 19:47:25.089668+00	14	18	23	Verify account	2	Changed content, in_menus and keywords.
78	2014-05-05 19:51:29.979744+00	14	26	24	Resend Verification Email	1	
79	2014-05-06 23:53:55.591118+00	12	50	1	SiteConfiguration object	2	Changed col3_content, twitter_link, facebook_link, youtube_link, github_link, linkedin_link, gplus_link and copyright.
80	2014-05-07 00:00:32.045384+00	12	50	1	SiteConfiguration object	2	Changed col3_content and youtube_link.
81	2014-05-07 00:01:37.498027+00	12	50	1	SiteConfiguration object	2	Changed col3_content and youtube_link.
82	2014-05-07 15:16:21.604904+00	14	18	25	Create Resource	1	
83	2014-05-07 16:23:46.654261+00	14	50	1	SiteConfiguration object	2	Changed col3_content and id.
84	2014-05-07 16:25:02.205153+00	14	51	6	Home	2	Changed header_background, header_image, content, in_menus and keywords.
85	2014-05-07 17:27:32.934936+00	14	18	26	Terms of Use	1	
86	2014-05-07 17:28:04.067626+00	14	18	27	Statement of Privacy	1	
87	2014-05-07 17:30:43.952194+00	14	18	27	Statement of Privacy	2	Changed in_menus, slug and keywords.
88	2014-06-02 18:03:55.854724+00	14	18	22	Support	2	Changed slug and keywords.
89	2014-06-02 18:07:38.191945+00	14	18	28	Resource landing	1	
90	2014-06-02 18:08:59.937737+00	14	18	29	Share resource	1	
91	2014-06-02 18:09:05.849536+00	14	18	28	Resource landing	2	Changed in_menus and keywords.
92	2014-06-02 19:30:18.824469+00	14	51	6	Home	2	Changed header_background, header_image, content, in_menus and keywords.
93	2014-06-02 19:34:52.495092+00	14	51	6	Home	2	Changed header_background, header_image, content, in_menus and keywords.
94	2014-06-03 17:06:12.283253+00	2	3	2	th	2	Changed first_name, last_name and groups. Added Site permission "SitePermission object". Changed title, keywords, uniqueCode, givenName and familyName for scholar "  : th".
95	2014-06-03 17:08:32.305593+00	2	32	18	Resources / Generic Resource Test	2	Changed keywords. Added qualified dublin core element "Abstract = Sed ut perspiciatis unde omnis iste natus error si...". Added qualified dublin core element "References = Heard, J. R., "Lorem Ipsum." Lorem Ipsum Generator...". Added qualified dublin core element "References = Heard, J. R., "Lorem Ipsum 2." Lorem Ipsum Generat...".
96	2014-06-03 17:09:00.477417+00	2	32	18	Resources / Generic Resource Test	2	Changed keywords. Added qualified dublin core element "BibliographicCitation = Heard, J. R., "Generic Resource Test" Hydroshare 2...".
97	2014-06-03 17:15:16.092289+00	2	32	18	Resources / Generic Resource Test	2	Changed keywords.
98	2014-06-04 15:19:23.908032+00	2	2	1	Hydroshare Author	2	Changed permissions.
99	2014-06-04 15:19:55.004868+00	2	3	2	th	2	Changed is_superuser. Changed keywords for scholar "Jefferson Heard : th".
100	2014-06-06 13:39:07.432664+00	2	32	18	Resources / Generic Resource Test	2	Changed public and id.
101	2014-06-09 19:08:47.622842+00	14	18	26	Terms of Use	2	Changed content, in_menus and keywords.
102	2014-06-09 19:09:37.35497+00	14	18	26	Terms of Use	2	Changed content, in_menus and keywords.
103	2014-06-09 19:11:17.924057+00	14	18	26	Terms of Use	2	Changed content, in_menus and keywords.
104	2014-06-09 19:15:13.503718+00	14	18	26	Terms of Use	2	Changed content, in_menus, description and keywords.
105	2014-06-09 19:16:27.228451+00	14	18	27	Statement of Privacy	2	Changed content, in_menus and keywords.
106	2014-06-09 19:16:48.48823+00	14	18	26	Terms of Use	2	Changed content, in_menus, description and keywords.
107	2014-06-09 19:27:00.185566+00	14	3	18	jeff@terrahub.io	3	
108	2014-06-09 19:55:19.515735+00	14	3	19	jeff@terrahub.io	3	
109	2014-06-09 20:18:53.777071+00	14	50	1	SiteConfiguration object	2	Changed col3_content and id.
110	2014-06-09 20:24:17.504225+00	2	32	18	Resources / Generic Resource Test	2	Changed public and id.
111	2014-06-11 02:25:05.48499+00	14	3	20	jeff@terrahub.io	3	
112	2014-06-11 02:37:03.143051+00	14	3	23	jeff@terrahub.io	3	
113	2014-06-11 02:50:08.155172+00	14	3	24	jeffersonheard	2	Changed groups.
114	2014-06-11 12:34:11.666565+00	14	18	20	Explore	2	Changed in_menus and keywords.
115	2014-06-11 12:34:19.712734+00	14	18	21	Collaborate	2	Changed in_menus and keywords.
116	2014-06-11 12:36:09.38368+00	14	50	1	SiteConfiguration object	2	Changed col1_content and id.
117	2014-06-11 13:37:30.852247+00	14	3	24	jeffersonheard	3	
118	2014-06-11 14:27:36.497312+00	14	3	25	jeff@terrahub.io	3	
119	2014-06-11 14:32:22.161236+00	14	3	26	jeffheard	3	
120	2014-06-11 14:41:09.340278+00	2	32	18	Resources / Generic Resource Test	2	Changed edit_groups and keywords.
121	2014-06-11 14:42:17.740733+00	14	3	3	jeff	2	Changed is_superuser.
122	2014-06-11 16:14:29.885409+00	14	3	16	platosken	3	
123	2014-06-11 16:17:20.254574+00	14	3	27	jeffheard	3	
124	2014-06-11 17:27:25.872058+00	14	3	29	jon_goodall	2	Changed is_staff and groups.
125	2014-06-11 17:27:49.752348+00	14	3	17	srj9	2	Changed is_staff and groups.
126	2014-06-11 17:35:46.478059+00	14	3	28	jeffheard	3	
127	2014-07-18 18:04:01.099719+00	14	51	6	Home	2	Changed header_background, header_image, content, in_menus and keywords.
128	2014-07-18 18:04:31.81219+00	14	18	19	Resources	2	Changed title and keywords.
129	2014-07-19 00:17:37.249445+00	12	32	46	Tiff File for unknown location	2	Changed public and id.
130	2014-07-19 22:47:24.446688+00	38	32	48	Test resource-1 by PK	2	Changed content, public, in_menus and keywords.
131	2014-07-20 12:59:24.457045+00	12	32	53	Test resource shared with davidG	2	Changed public and id.
132	2014-07-20 13:02:19.745864+00	12	32	54	test resource shared with david G view	2	Changed public and id.
133	2014-07-20 13:17:31.594398+00	37	32	56	Test resource shared with dtarb	2	Changed public and id.
134	2014-07-20 13:33:29.548+00	37	32	55	Test resource public davidg	2	Changed content, in_menus and keywords.
135	2014-07-20 13:33:46.468366+00	37	32	55	1. Test resource public davidg	2	Changed title, in_menus and keywords.
136	2014-07-20 13:34:34.071343+00	37	32	56	3. Test resource shared with dtarb	2	Changed title, content, in_menus and keywords.
137	2014-07-20 13:35:20.220507+00	12	32	52	2. Test resource public dtarb	2	Changed title, content, in_menus and keywords.
138	2014-07-20 13:36:08.014818+00	12	32	53	4. Test resource shared with davidG	2	Changed title, content, in_menus and keywords.
139	2014-07-20 13:37:35.822776+00	12	32	54	5. test resource shared with david G view	2	Changed title, content, in_menus and keywords.
140	2014-08-01 14:55:13.264325+00	7	51	6	Home	2	Changed content and id.
141	2014-08-03 20:16:25.03412+00	7	51	6	Home	2	Changed content and id.
\.


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 141, true);


--
-- Data for Name: django_comment_flags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_comment_flags (id, user_id, comment_id, flag, flag_date) FROM stdin;
\.


--
-- Name: django_comment_flags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_comment_flags_id_seq', 1, false);


--
-- Data for Name: django_comments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_comments (id, content_type_id, object_pk, site_id, user_id, user_name, user_email, user_url, comment, submit_date, ip_address, is_public, is_removed) FROM stdin;
3	32	18	1	2	Jefferson Heard	jeff@renci.org		This is my comment on this resource.	2014-06-06 14:28:36.030007+00	152.54.8.126	t	f
6	32	39	1	30	Jeff	jeff@gmail.com	http://www.stackoverflow.com/	This data set has been very useful in my own research. 	2014-06-11 18:58:11.084543+00	128.187.97.19	t	f
7	32	42	1	\N	Amber Jones	amber.jones@usu.edu		These data characterize diurnal fluctuations in temperature in the Little Bear River at its terminus just upstream of Cutler Reservoir. At its lower end, the hydrology of the Little Bear River has been highly modified, with streamflows dominated by releases from Hyrum Reservoir and with several agricultural diversions and return flows.  These temperature observations reflect a high degree of human modification within what was typically a spring snowmelt dominated system.	2014-06-14 22:55:06.565085+00	129.123.51.50	t	f
8	32	42	1	\N	Tony Melcher	tony.melcher@usu.edu		I used these data in a fish habitat assessment for the Little Bear River.  They demonstrate the diurnal variability in water temperature, and I was able to use them to assess potential acute and chronic effects of elevated stream temperatures on salmonid fish species.	2014-06-14 22:58:19.278131+00	129.123.51.50	t	f
\.


--
-- Name: django_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_comments_id_seq', 8, true);


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_content_type (id, name, app_label, model) FROM stdin;
1	permission	auth	permission
2	group	auth	group
3	user	auth	user
4	content type	contenttypes	contenttype
5	redirect	redirects	redirect
6	session	sessions	session
7	site	sites	site
8	qualified dublin core element	dublincore	qualifieddublincoreelement
9	qualified dublin core element history	dublincore	qualifieddublincoreelementhistory
10	migration history	south	migrationhistory
11	log entry	admin	logentry
12	comment	comments	comment
13	comment flag	comments	commentflag
14	rods environment	ga_irods	rodsenvironment
15	Setting	conf	setting
16	Site permission	core	sitepermission
17	Page	pages	page
18	Rich text page	pages	richtextpage
19	Link	pages	link
20	Blog post	blog	blogpost
21	Blog Category	blog	blogcategory
22	Comment	generic	threadedcomment
23	Keyword	generic	keyword
24	assigned keyword	generic	assignedkeyword
25	Rating	generic	rating
26	Form	forms	form
27	Field	forms	field
28	Form entry	forms	formentry
29	Form field entry	forms	fieldentry
30	Gallery	galleries	gallery
31	Image	galleries	galleryimage
32	Generic Hydroshare Resource	hs_core	genericresource
33	task state	djcelery	taskmeta
34	saved group result	djcelery	tasksetmeta
35	interval	djcelery	intervalschedule
36	crontab	djcelery	crontabschedule
37	periodic tasks	djcelery	periodictasks
38	periodic task	djcelery	periodictask
39	worker	djcelery	workerstate
40	task	djcelery	taskstate
41	catalog page	ga_resources	catalogpage
42	data resource	ga_resources	dataresource
43	ordered resource	ga_resources	orderedresource
44	resource group	ga_resources	resourcegroup
45	related resource	ga_resources	relatedresource
46	style	ga_resources	style
47	rendered layer	ga_resources	renderedlayer
48	api access	tastypie	apiaccess
49	api key	tastypie	apikey
50	Site Configuration	theme	siteconfiguration
51	Home page	theme	homepage
52	icon box	theme	iconbox
53	group ownership	hs_core	groupownership
54	resource file	hs_core	resourcefile
55	bags	hs_core	bags
56	city	hs_scholar_profile	city
57	region	hs_scholar_profile	region
58	country	hs_scholar_profile	country
59	organization	hs_scholar_profile	organization
60	person	hs_scholar_profile	person
61	person email	hs_scholar_profile	personemail
62	person location	hs_scholar_profile	personlocation
63	person phone	hs_scholar_profile	personphone
64	user keywords	hs_scholar_profile	userkeywords
65	user demographics	hs_scholar_profile	userdemographics
66	other names	hs_scholar_profile	othernames
67	organization email	hs_scholar_profile	organizationemail
68	organization location	hs_scholar_profile	organizationlocation
69	organization phone	hs_scholar_profile	organizationphone
70	external org identifiers	hs_scholar_profile	externalorgidentifiers
71	org associations	hs_scholar_profile	orgassociations
72	external identifiers	hs_scholar_profile	externalidentifiers
73	scholar	hs_scholar_profile	scholar
74	scholar external identifiers	hs_scholar_profile	scholarexternalidentifiers
75	scholar group	hs_scholar_profile	scholargroup
76	user profile	theme	userprofile
77	external profile link	hs_core	externalprofilelink
78	contributor	hs_core	contributor
79	creator	hs_core	creator
80	description	hs_core	description
81	title	hs_core	title
82	type	hs_core	type
83	date	hs_core	date
84	relation	hs_core	relation
85	identifier	hs_core	identifier
86	publisher	hs_core	publisher
87	language	hs_core	language
88	coverage	hs_core	coverage
89	format	hs_core	format
90	subject	hs_core	subject
91	source	hs_core	source
92	rights	hs_core	rights
93	core meta data	hs_core	coremetadata
94	iRODS Environment	django_irods	rodsenvironment
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_content_type_id_seq', 94, true);


--
-- Data for Name: django_irods_rodsenvironment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_irods_rodsenvironment (id, owner_id, host, port, def_res, home_coll, cwd, username, zone, auth) FROM stdin;
\.


--
-- Name: django_irods_rodsenvironment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_irods_rodsenvironment_id_seq', 1, false);


--
-- Data for Name: django_redirect; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_redirect (id, site_id, old_path, new_path) FROM stdin;
\.


--
-- Name: django_redirect_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_redirect_id_seq', 1, false);


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
qvp40du8s6up8enkldjvrpr3orq39edx	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-02-18 16:00:40.73287+00
epmibejlx47ixj46ib6sq6j0mceww1kf	N2UzODBmMzg2YzY1OGU3MDk1NDA5MDFmNmQ5NGVlZmU4MmY2YmM1Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjN9	2014-02-18 16:01:12.471904+00
sbor97qk8v3dmkb2sfb2i2pryyznf5ny	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-02-19 17:04:46.054582+00
z1fpdfxp0am3bmh0ely1eb2nu06rpdsc	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-19 00:07:35.274992+00
7af8svsmr3n5k4g2rrku27cpl98g5ida	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-02-19 17:05:08.088313+00
of5ldast56w3pv5ksm4i3jyu2uqe6rtf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-19 00:17:03.5548+00
obk1np0ot3luoymlg4vptnmww4an5qqc	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-02-19 17:07:54.364313+00
3kns587k46ukpj3aaurkgqukbawzl3ah	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-03-19 16:13:22.801814+00
l0uakhq3rgxd868pezq45c2enpwf7b24	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-02-19 17:08:52.164474+00
a3aueia2ekfn1y8z64l2cf8m6yld06f4	NTZhOTA4MzllNjI4MzA0NTM2YzJjMjY0NTJjZTg5NjhjMGI3NTQ5Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjh9	2014-02-19 17:13:08.488865+00
nvgtmv3v0x9qqbxyn2qhanv0weh8p38y	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-02-19 17:13:15.085918+00
aks13e3uykvm2is9tji52xhgjp6xp4rw	MDU5YmRkODMxNTc4NjY0NTNhNGNhNDE1MDg5ZTY5ZmQ5NDY4Y2U4NTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjZ9	2014-02-19 17:15:45.139967+00
m55f2auux3n9vl66pxku02ts83rgikl6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-19 18:29:10.32542+00
vch35mhgnoqb7rk7y42rb923qxznqjce	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-02-19 17:18:21.451318+00
ssdhtqjqd926z2oi10eralkvyeobrppp	MDU5YmRkODMxNTc4NjY0NTNhNGNhNDE1MDg5ZTY5ZmQ5NDY4Y2U4NTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjZ9	2014-02-19 18:11:55.794742+00
m2fnh6eb4rb78ahud8s5zg09flo78mux	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-19 21:41:15.390314+00
50kneg73ewk2n40bdt20xfih4n1e69xn	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-02-19 19:01:00.368629+00
mutq2i59nxqqd0xtc8c9edqvavp48ef1	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-02-19 21:59:58.374588+00
a6ykfsf7z7dms7h41h0j6wa0bh25r3x2	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-19 22:11:15.452803+00
sviwfcoi77aaa7zxcissbbo5x1f6iz0c	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-02-21 20:21:19.466033+00
6cwigooyu6c8j8707zs8krof4tri1o0m	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-02-21 22:16:00.214061+00
u1n8coelgrzigi0u0fhuvy5ebnbgefy2	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-03-20 00:01:28.814673+00
tqk5jz4o48117ofq93cohw1sxvxscov7	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-03-21 18:24:00.461754+00
sw1vn8bcx7re9r7wiekmh3mz9jdxcop9	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-02-26 03:49:39.088372+00
x0fp8lgvnxvi19pxdkelssuwfvr40vem	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-02-26 13:44:05.923149+00
lszm479i7vbwhr92oz3gt5a2r990ft7i	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-02-26 15:44:52.269416+00
c27c8mxnti8syirzb6mdv8i0gvfphw73	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-02-28 21:34:22.990164+00
kw803b33dsgqhhe438iucjmlr4g79684	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-04 00:42:00.452943+00
fe5ce28e779889ij6m27syn3qmcyzf0m	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-03-04 18:23:34.178532+00
8qjbiwhpg06o4nowxqjw0jdh41bajw16	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-04 18:24:33.511482+00
u3lxga3vhk4evajcnh4rlilntxx4fk82	OGI2OTBlMjNmZjcxMTFiN2E0ZDM5NWZjYjBiY2FlMTRlZjc1NzgzYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzfQ==	2014-03-04 22:40:45.566579+00
mdkaupw7ct810jga0123jxs8lfs6zpoo	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-05 17:57:26.325122+00
uxa31xaafq44lrrmo6ufuka15are2cfd	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-03-05 18:08:38.197017+00
miad9uotohm976kt2wtv9ecv94b2eguv	MDU5YmRkODMxNTc4NjY0NTNhNGNhNDE1MDg5ZTY5ZmQ5NDY4Y2U4NTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjZ9	2014-03-10 22:48:24.2825+00
jk5smmsg23oez8wgfbemjwqqe7qx68vm	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-03-12 17:08:48.270261+00
j7wilu9vz8vwou6e2t9vz0jb9xh2x5t3	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-03-12 17:09:39.9253+00
7dlbmm9ajgl9gvhr617nz8rlez46e1bt	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-03-13 16:31:30.008855+00
5ugjvbbptmdayel1kn3q0tj74wyryk4q	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-17 14:21:57.754523+00
6qhficiaju0pah6xeqymd6umpbawpj3s	Mzc5MmVlZTVjNTliN2U5MDJkZDJjY2Q3ZmNkZDUzOTNkZTk3NWU3OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE2fQ==	2014-03-22 09:03:30.851983+00
o90mqv8pmz7u8ou6mzzb1rvjkdgm52bh	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-09 13:23:29.964167+00
3e10cq9xv6qfv3qc2sd4bwu5vlf46sre	OGZhNDBmZjY5MTk0NWViNWY1YTBjZDVmOGZhMmUxNWFhNDkzZTJiZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM4fQ==	2014-08-05 18:19:39.734733+00
wc4rrgonauqbni3kcxpx4ruigsg6cp3b	MDE3MGQ0NzgyNGI1Yzg4ZTc1ZWEyNmJmNGFhMDIzZTE3NGQxMWQ4Njp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE3fQ==	2014-04-09 20:54:07.459754+00
3o61ns3jas7cekypfk8rj65kbxqpfde4	OGI2OTBlMjNmZjcxMTFiN2E0ZDM5NWZjYjBiY2FlMTRlZjc1NzgzYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzfQ==	2014-08-07 20:57:39.399294+00
zyrqx8qadvwg3mwc4qcjgcwo7lg01hj3	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-04-10 21:38:42.838615+00
jhh573upkf9gs2ym8wzoit7zowuuai7n	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-06-25 17:06:10.759049+00
nrzsvs6tk1fjcv5ljtvhk8v5glt9xzdh	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-04-14 17:32:10.337189+00
27o0zb6gv6oki16zejuuxrsjlgc5en6h	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-04-23 14:56:30.122852+00
m98l8vwpg3nawryzyqusg80as3y3et5q	ZGIyMDNjNzUxZWYwNDVmZjZhNmE4YzU3ZjQ5M2Y2NTRmYjEwM2Y1YTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMwfQ==	2014-06-25 17:14:28.808856+00
tke9wphj31tfq0yi73u8e9u8wv4bq9ca	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-06 17:47:41.293076+00
33ai2992a72zm2safp80dfmm52n10as1	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-05-08 21:16:00.203714+00
01f746zv1rj5lgi3muhead75otvksek6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-17 20:16:29.118806+00
2jo19jfo2fygvlaongpa4k5sqw2gc1bs	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-21 01:08:02.729221+00
epghtxgeloarw5xjidc6ylv30b4eub2l	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-13 21:42:58.171993+00
l4206dj5cxfzivs6kb1lsfen7lekhvp5	OGI2OTBlMjNmZjcxMTFiN2E0ZDM5NWZjYjBiY2FlMTRlZjc1NzgzYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzfQ==	2014-08-27 16:19:00.057556+00
o45s46wx404qt3kamxg12qdnx0ijnmd4	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-07-01 21:34:04.035374+00
oiebkhssmsww5ina92c2rfqocalqzqi9	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:49:21.930091+00
i4mknrh5dx94d0om7exq6f98w0g5u9b3	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-07-04 04:47:35.4145+00
ubjfi81gceid3gspk6kppqlq5is8o4og	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:51:03.909031+00
0fph7jg31rn31kflu3skwcll09888rnx	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-09 19:21:23.21981+00
665rhgbx0kxqgfq3w96e06w7rkmi08yu	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-07-25 23:10:06.833496+00
9e9ljhx2brwn0vsvq1h6scqzmn33pg8j	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-03-24 15:02:29.932232+00
qr1xremtfh4zy0jqw2g312hpy5m8gvyf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-09 00:54:28.496144+00
1wn3c6zqf28crfskpyzl66lacryuwbwy	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-28 15:33:28.807751+00
wda85tfose9l8s5tdpwotfp581kghqae	ZjM2NmMzODA5ODEzMjhkODA5OGMzN2IyNDM3MDM5NmUxZjRhZDU4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM5fQ==	2014-08-05 15:26:53.728235+00
jmfqwoja0oo3zi8au56x5h9qat2jpzpt	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-25 17:26:56.617585+00
x094y96g2egpwi2na63btrsk8bv1eptl	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-06-26 13:12:50.688963+00
bbhtkjii4lkug90b6ot3oj68xgvc3cwf	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-20 23:59:51.801152+00
2duetxro5bsffi2j4j6y1k2dh7pk61c9	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-24 22:28:59.554253+00
pc2fkm15t2cbgq76qml4fig6utjuaevk	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-04-30 15:21:13.10097+00
a9xbk4ngsvagf50bumcklfy6v27f7xqc	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-21 01:09:12.031427+00
9i2z4t0o99keusrp2mj3gzqjk4ydlcdx	OGI2OTBlMjNmZjcxMTFiN2E0ZDM5NWZjYjBiY2FlMTRlZjc1NzgzYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzfQ==	2014-05-06 19:26:46.609864+00
z1supwob9h3jt2qqv09m3sxr4qt1wng4	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-05-08 21:16:18.035112+00
1cwufl7gkqsfqwg3cxehofjbuurt8mqu	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-05-21 15:18:04.40864+00
9gc5f4si5snwluskmczice2hyxn8474x	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-13 18:16:41.11812+00
w1zluujdr18i9sucy1ktyrnkv9ndk73p	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-26 20:16:54.550504+00
cpgsium7h6bm85zt9cahvlwh6k1ggj7i	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-02 00:23:11.701584+00
519nfcjd1g7xbd3d05hgteo2qz1t6ezo	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-15 14:55:17.093705+00
wd7lttwjty5u4i88gle25585g6mnndov	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-14 13:07:52.644815+00
x3pwsiahbkfne1k2c0rxlcprry8l6hbg	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:50:38.77378+00
vyll8ot4tni1885ixkeazh1f56vcqq87	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-07-07 15:34:11.80706+00
1kcb6kdxl9up0aa3setvjf5iv7vbc6w1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:52:14.162754+00
u6j82tvlldn9d9vszhoeyuvkekem8y1d	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-07-21 18:50:44.458761+00
3uhkeiuz50k3wy7sclfb1w0kd0hgivxd	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-06-23 20:23:03.680743+00
xk48zibahupf5jv3sn2p4qtswgmb3c0g	YjBhZDJkZmY2YzBjODVhM2YxYzVlMTBkMmY2NWYyYjUxNmVjZGVjMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQxfQ==	2014-09-10 16:14:13.340188+00
f1gdqwxghp7rchymsp98ocnn1iqa1igp	ZmY4MTEyMzExOWExMmM0MjYyYzFkYTQzYTRhMDI5OWNiODE4YTUzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM3fQ==	2014-08-03 13:39:56.740488+00
cntm0xduasknl0yw3l6c4rfy7ahmxdgp	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-09 12:44:24.965349+00
lsmxqlw05x9f9uloxe62twqootbbn8rw	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-06-02 20:20:58.245613+00
udn8z48wi5rpnway5wmnsho1pw5t2jns	OGZhNDBmZjY5MTk0NWViNWY1YTBjZDVmOGZhMmUxNWFhNDkzZTJiZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM4fQ==	2014-08-05 17:34:58.087593+00
khvj9fhc6uucpp6zmlt3yf4vca1xz9ir	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-08-06 16:19:27.83665+00
8dg9qh25dnfudwgpsprrufuuewvt02ws	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-11 22:21:20.35476+00
2f1yj21nsiwo7w1j83ie2wfecesbtd7m	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-20 22:19:04.79546+00
8gik9yj8tppp6v8hcb015akdrjgexsq9	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-25 17:34:35.455896+00
k05tdo6g410rc00bkon25dcidwdl9yho	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-04-24 22:34:21.217653+00
8mag65afpwwxkinqomjqqrzko4nafehp	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-02 02:38:45.558486+00
uipftk60wtt632qrzhhp88dyx1k0h272	ZmY4MTEyMzExOWExMmM0MjYyYzFkYTQzYTRhMDI5OWNiODE4YTUzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM3fQ==	2014-08-09 03:51:35.62365+00
4j4zxsszx8z1ic31hfno55hgsc8f6wxx	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-07 05:08:15.420443+00
4hjoa3de1omyibdli2lqm7jr5kyri1yl	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-06-27 14:49:31.625344+00
oa3gts0wqy4vs29716dpd0q135aastzf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-02 16:17:50.098506+00
9mjm2wm120hb33e4q6y6xqoa51lfmyj6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:50:41.497681+00
y4j0s6m9rfs5o7rh47hnizb9pkl0wrtw	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-05-23 21:07:56.123597+00
p0hopm8wcm9hwccdc2r33zfwip5hc0yg	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:53:24.756195+00
0arra1e0xwlwls2jo4ny8tb2wfet06cm	ZmJmMjAzM2U5M2NmNDRkYWQ1NGFkZWZkNmFmNjY1NTZjMGQ2NzQ4ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMyfQ==	2014-07-21 19:11:26.856374+00
1vqjhfcpdp8yi63ux94zgwt1ik2navg2	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-09-10 18:32:05.391189+00
rfk5stg10c9tpc6jn4893tzpu7f4czbw	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-28 16:01:27.535162+00
5owkla54ypvsptk71jvdicplxe203is6	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-08-01 22:37:26.484369+00
xynhx0ksj4km1wpwkx7fmc3x7qqiz5q8	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-04 13:04:49.435771+00
b2m4ja8ztwbvrkiqtjplioq1vonimte1	N2RjZTc1ZTdkNzRhZDVlZDc0MzVhNDU3NDU4MTAxNDFiNzYyMmEzNDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI4fQ==	2014-06-25 16:48:49.285633+00
o73jrnucpyje1krqua0qbcvr03vctb6m	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-09 20:11:36.419072+00
g5lxhfruqtkb8rxnjosu8lry34fu7cro	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-03-26 15:36:58.594348+00
em69vk6mvibj0oyb0ise66ta2vwcjevq	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-04-09 21:25:29.165707+00
914gw3cza0x8s3ltdkp3wee6eunxvmbj	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-25 02:24:34.43365+00
1s2coo5ii9ooz97r5kj4qvv6g954iroy	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-13 20:04:32.578327+00
axbs8td5eepp1t1e2yazgy0s0yvzkt33	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-20 17:24:24.355476+00
v8bv3z9iiiwjg2scwosmspy0kvrxv85n	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-03-26 16:28:26.608748+00
wkbvua94fg0d1sukodq72dsjq4qjlwas	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-21 17:15:26.919868+00
2eb1mlwwshivx404021k0dmxudbi63c2	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-05-06 17:47:14.483388+00
6k503vt9ajvxg1lfky2pajdr3loxntdw	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-08 21:15:41.055955+00
9ac05w0h23grhyv39951kdbd1fi0d7qh	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-12 19:00:15.016649+00
p51o31jmp1hnq6dl0t27qzcpsoxv6v1d	N2UzODBmMzg2YzY1OGU3MDk1NDA5MDFmNmQ5NGVlZmU4MmY2YmM1Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjN9	2014-03-26 16:31:04.366811+00
7840x2ook981f247ss8vtzv3e7t6z9g6	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-06-27 19:05:00.635198+00
iqa5lrxq1oeibpskedf9iy0ldhbp58qx	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-21 04:11:14.735604+00
7fi4khzisttrqpi06438h3xdyjw13cix	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-26 16:33:05.487359+00
gwpkv4ro27qx2mbekjjky5ydhcp7sj3z	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-13 21:15:51.603611+00
ap1vq6215xi7md0ydxnu2jjszyzjuiyn	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-03-27 01:26:20.200585+00
ztqjqj79ebmmiveni7r1xc2qoyepwf2x	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-31 17:18:55.775987+00
9mbhfezi4k606cj6270ywboovkkzspvk	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-01 13:50:53.896293+00
0yns8mxt5jg6q1y5nqy1faoq4ubaim0n	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-02 04:09:35.726824+00
f5ypbfhda7va1ndryg0omtadafuh4ren	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-23 19:07:30.433163+00
u3v0crcvmiehn322dd9dwph7n0g5jkv6	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-04-02 16:13:22.274201+00
h5qc5terfvmr627pl0d0ynt7169qcb3n	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:47:13.733766+00
6b13sdrfr84867u7q99qd51ez8rjswkr	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-05-21 18:19:00.352417+00
epcsrkf9y0rrhdkjet371gmdyd07t7ai	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-03 11:50:12.743579+00
4swl0ekjisxpj8lok7z7rrhfh519iwy1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:50:53.71061+00
w7haixpumvmc8qd9cayi667iqniuep2t	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-03 11:56:21.159705+00
ft1urfvrtn0hke0s5h5gf2p7xgwmfic0	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-02 16:17:50.310778+00
n7ku873s40dw005pmt073yszu17iaasb	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-06 14:30:46.369229+00
4ydacy0khrzg5lh6uqqj8ancrk06doeo	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:53:27.734894+00
nvs3f3bc5qkg1wdlu4qkatoe7ubqt7wz	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-07 22:17:31.327026+00
6by4ivfnomd3jyhlekrmfv57c74l703s	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-08 15:37:03.378192+00
95mnqqrnkcbk71lheelel7drd5bt56i0	OGI2OTBlMjNmZjcxMTFiN2E0ZDM5NWZjYjBiY2FlMTRlZjc1NzgzYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzfQ==	2014-07-21 23:12:45.941812+00
m93hrfmi2ta4bj0l9lvpj915xd71o5i1	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-07-30 18:12:43.896158+00
wnwaqq3fh0uzcxzbd5wfxrkearuf517t	ZmY4MTEyMzExOWExMmM0MjYyYzFkYTQzYTRhMDI5OWNiODE4YTUzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM3fQ==	2014-08-01 18:45:59.237298+00
\.


--
-- Data for Name: django_site; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_site (id, domain, name) FROM stdin;
1	127.0.0.1:8000	Default
\.


--
-- Name: django_site_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_site_id_seq', 1, true);


--
-- Data for Name: djcelery_crontabschedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY djcelery_crontabschedule (id, minute, hour, day_of_week, day_of_month, month_of_year) FROM stdin;
\.


--
-- Name: djcelery_crontabschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('djcelery_crontabschedule_id_seq', 1, false);


--
-- Data for Name: djcelery_intervalschedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY djcelery_intervalschedule (id, every, period) FROM stdin;
\.


--
-- Name: djcelery_intervalschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('djcelery_intervalschedule_id_seq', 1, false);


--
-- Data for Name: djcelery_periodictask; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY djcelery_periodictask (id, name, task, interval_id, crontab_id, args, kwargs, queue, exchange, routing_key, expires, enabled, last_run_at, total_run_count, date_changed, description) FROM stdin;
\.


--
-- Name: djcelery_periodictask_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('djcelery_periodictask_id_seq', 1, false);


--
-- Data for Name: djcelery_periodictasks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY djcelery_periodictasks (ident, last_update) FROM stdin;
\.


--
-- Data for Name: djcelery_taskstate; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY djcelery_taskstate (id, state, task_id, name, tstamp, args, kwargs, eta, expires, result, traceback, runtime, retries, worker_id, hidden) FROM stdin;
\.


--
-- Name: djcelery_taskstate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('djcelery_taskstate_id_seq', 1, false);


--
-- Data for Name: djcelery_workerstate; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY djcelery_workerstate (id, hostname, last_heartbeat) FROM stdin;
\.


--
-- Name: djcelery_workerstate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('djcelery_workerstate_id_seq', 1, false);


--
-- Data for Name: dublincore_qualifieddublincoreelement; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY dublincore_qualifieddublincoreelement (id, object_id, content_type_id, term, qualifier, content, updated_at, created_at) FROM stdin;
78	39	32	T	\N	Provo River Water Flow 2009-12-12 to 2010-12-15	2014-06-11 18:53:30.051818+00	2014-06-11 18:53:30.051841+00
79	39	32	AB	\N	Provo river water flow measurements taken before and during river restoration efforts. 	2014-06-11 18:53:30.055133+00	2014-06-11 18:53:30.055164+00
80	39	32	DTS	\N	2014-06-11T18:53:30.007644+00:00	2014-06-11 18:53:30.058429+00	2014-06-11 18:53:30.058451+00
4	9	32	AB		This is a simple generic resource that is not entirely public.  DaveT, JeffH, and Jefferson should be able to view it.	2014-03-12 14:16:21.953376+00	2014-03-12 14:16:21.953398+00
5	18	32	AB		Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?	2014-06-03 17:08:32.255605+00	2014-06-03 17:08:32.255638+00
6	18	32	REF		Heard, J. R., "Lorem Ipsum." Lorem Ipsum Generator, 2012.	2014-06-03 17:08:32.2976+00	2014-06-03 17:08:32.297632+00
7	18	32	REF		Heard, J. R., "Lorem Ipsum 2." Lorem Ipsum Generator, 2014.	2014-06-03 17:08:32.299723+00	2014-06-03 17:08:32.299746+00
8	18	32	BIB		Heard, J. R., "Generic Resource Test" Hydroshare 2014.	2014-06-03 17:09:00.471461+00	2014-06-03 17:09:00.471485+00
9	18	32	REF	\N	Heard, J.R. "Lorem Ipsum 3. The Return of the Ipsum.", Lorem Ipsum Generator 2014.	2014-06-04 13:34:12.318575+00	2014-06-04 13:34:12.318598+00
10	18	32	COT	\N	Hydroshare Generic Resource Release 1 Specification.	2014-06-04 13:34:59.513919+00	2014-06-04 13:34:59.513947+00
11	18	32	REF	\N	Heard J.R., "Lorem Ipsum 4", Lorem Ipsum Generator 2014	2014-06-04 16:54:29.956993+00	2014-06-04 16:54:29.957015+00
81	39	32	CN	\N	shaun livingston	2014-06-11 18:53:30.061678+00	2014-06-11 18:53:30.061699+00
82	39	32	CR	\N	shaun livingston	2014-06-11 18:53:30.064667+00	2014-06-11 18:53:30.064688+00
83	39	32	FMT	file format	csv	2014-06-11 18:54:52.913259+00	2014-06-11 18:54:52.913284+00
84	40	32	T	\N	EPA-SWMM model 	2014-06-12 13:20:19.774856+00	2014-06-12 13:20:19.774879+00
85	40	32	AB	\N	calibrated EPA-SWMM model for Rocky Branch watershed, Columbia, SC	2014-06-12 13:20:19.778268+00	2014-06-12 13:20:19.77829+00
86	40	32	DTS	\N	2014-06-12T13:20:19.714025+00:00	2014-06-12 13:20:19.781439+00	2014-06-12 13:20:19.781461+00
87	40	32	CN	\N	Mohamed Morsy	2014-06-12 13:20:19.784257+00	2014-06-12 13:20:19.784278+00
88	40	32	CR	\N	Mohamed Morsy	2014-06-12 13:20:19.787158+00	2014-06-12 13:20:19.787179+00
89	41	32	T	\N	HydroTrend - Run 1	2014-06-13 19:08:44.098858+00	2014-06-13 19:08:44.09888+00
90	41	32	AB	\N	A CSDMS Web Modeling Tool model run of the HydroTrend component with default model parameters.	2014-06-13 19:08:44.109186+00	2014-06-13 19:08:44.109213+00
91	41	32	DTS	\N	2014-06-13T19:08:43.910451+00:00	2014-06-13 19:08:44.112514+00	2014-06-13 19:08:44.112546+00
92	41	32	CN	\N	Jon Goodall	2014-06-13 19:08:44.115694+00	2014-06-13 19:08:44.115716+00
93	41	32	CR	\N	Jon Goodall	2014-06-13 19:08:44.118813+00	2014-06-13 19:08:44.118835+00
94	42	32	T	\N	Water Temperature in the Little Bear River at Mendon Road	2014-06-14 22:47:26.160452+00	2014-06-14 22:47:26.160476+00
95	42	32	AB	\N	This resource contains water temperature observations in the Little Bear River at Mendon Road near Mendon, Utah, USA. The values represent 30-minut average values and were measured using a Hydrolap Minisonde 4 multi-parameter water quality sonde.  Values are recorded at the end of each 30 minute interval and represent the average water temperature over the preceding 30-minute interval. The data have been subject to multiple quality control tests, removing obviously bad data and known errors.	2014-06-14 22:47:26.16895+00	2014-06-14 22:47:26.168972+00
96	42	32	DTS	\N	2014-06-14T22:47:25.972009+00:00	2014-06-14 22:47:26.17194+00	2014-06-14 22:47:26.171961+00
97	42	32	CN	\N	Jeffery Horsburgh	2014-06-14 22:47:26.174934+00	2014-06-14 22:47:26.174955+00
98	42	32	CR	\N	Jeffery Horsburgh	2014-06-14 22:47:26.177952+00	2014-06-14 22:47:26.177973+00
35	18	32	COT	\N	Hydroshare Metadata Spec	2014-06-11 12:28:52.518096+00	2014-06-11 12:28:52.518118+00
104	45	32	T	\N	Torrent	2014-07-18 17:59:50.356779+00	2014-07-18 17:59:50.35681+00
105	45	32	AB	\N	Torrent	2014-07-18 17:59:50.360149+00	2014-07-18 17:59:50.36017+00
106	45	32	DT	\N	2014-07-18T17:59:50.330900+00:00	2014-07-18 17:59:50.362993+00	2014-07-18 17:59:50.363015+00
107	45	32	CN	\N	Jefferson Heard	2014-07-18 17:59:50.366012+00	2014-07-18 17:59:50.366034+00
108	45	32	CR	\N	Jefferson Heard	2014-07-18 17:59:50.368861+00	2014-07-18 17:59:50.368882+00
109	46	32	T	\N	Tiff File for unknown location	2014-07-18 18:33:02.036862+00	2014-07-18 18:33:02.036901+00
110	46	32	AB	\N	Tiff File for unknown location	2014-07-18 18:33:02.041026+00	2014-07-18 18:33:02.041053+00
111	46	32	DT	\N	2014-07-18T18:33:01.970174+00:00	2014-07-18 18:33:02.044678+00	2014-07-18 18:33:02.044705+00
112	46	32	CN	\N	David Tarboton	2014-07-18 18:33:02.048295+00	2014-07-18 18:33:02.048322+00
113	46	32	CR	\N	David Tarboton	2014-07-18 18:33:02.051568+00	2014-07-18 18:33:02.051591+00
114	46	32	AB	\N	This is a test abstract	2014-07-18 18:38:41.472129+00	2014-07-18 18:38:41.472155+00
115	46	32	CN	\N	Pabitra Dash	2014-07-18 18:39:13.706244+00	2014-07-18 18:39:13.706266+00
116	47	32	T	\N	Peuker Douglas DEM	2014-07-18 18:49:16.829503+00	2014-07-18 18:49:16.829537+00
117	47	32	AB	\N	Peuker Douglas DEM	2014-07-18 18:49:16.833019+00	2014-07-18 18:49:16.833041+00
118	47	32	DT	\N	2014-07-18T18:49:16.779345+00:00	2014-07-18 18:49:16.836011+00	2014-07-18 18:49:16.836045+00
119	47	32	CN	\N	DavidG Tarboton	2014-07-18 18:49:16.839013+00	2014-07-18 18:49:16.839042+00
120	47	32	CR	\N	DavidG Tarboton	2014-07-18 18:49:16.841933+00	2014-07-18 18:49:16.841955+00
121	48	32	T	\N	Test resource-1 by PK	2014-07-18 22:06:18.409788+00	2014-07-18 22:06:18.409817+00
122	48	32	AB	\N	Test	2014-07-18 22:06:18.413346+00	2014-07-18 22:06:18.413368+00
123	48	32	DT	\N	2014-07-18T22:06:18.384189+00:00	2014-07-18 22:06:18.416197+00	2014-07-18 22:06:18.416218+00
68	37	32	T	\N	Text and figures for our iEMSs paper titled 'Metadata for Describing Water Models'	2014-06-11 17:12:11.4213+00	2014-06-11 17:12:11.421328+00
69	37	32	AB	\N	Computer models are widely used in hydrology and water resources management. A large variety of models exist, each tailored to address specific challenges related to hydrologic science and water resources management. When scientists and engineers apply one of these models to address a specific question, they must devote significant effort to set up, calibrate, and evaluate that model instance built for some place and time. In many cases, there is a benefit to sharing these computer models and associated datasets with the broader scientific community. Core to model reuse in any context is metadata describing the model. A standardized metadata framework applicable across models will foster interoperability and encourage reuse and sharing of existing resources. This paper reports on the development of a metadata framework for describing water models. We discuss steps taken to achieve this goal for the HydroShare system and within the context of a use case that describes a team-based hydrologic modeling project.\r\n	2014-06-11 17:12:11.424958+00	2014-06-11 17:12:11.42498+00
70	37	32	DTS	\N	2014-06-11T17:12:11.366111+00:00	2014-06-11 17:12:11.428192+00	2014-06-11 17:12:11.428213+00
71	37	32	CN	\N	Jon Goodall	2014-06-11 17:12:11.431377+00	2014-06-11 17:12:11.431408+00
72	37	32	CR	\N	Jon Goodall	2014-06-11 17:12:11.435087+00	2014-06-11 17:12:11.435108+00
73	38	32	T	\N	Provo River Water Flow 2009-12-12 to 2010-12-15	2014-06-11 17:31:48.905825+00	2014-06-11 17:31:48.905853+00
74	38	32	AB	\N	This data was gathered for the purpose of monitoring gain of water flow due to river restoration efforts. 	2014-06-11 17:31:48.909472+00	2014-06-11 17:31:48.909495+00
75	38	32	DTS	\N	2014-06-11T17:31:48.843427+00:00	2014-06-11 17:31:48.912605+00	2014-06-11 17:31:48.912626+00
76	38	32	CN	\N	shaun livingston	2014-06-11 17:31:48.915786+00	2014-06-11 17:31:48.915807+00
77	38	32	CR	\N	shaun livingston	2014-06-11 17:31:48.919857+00	2014-06-11 17:31:48.919879+00
124	48	32	CN	\N	Pabitra Dash	2014-07-18 22:06:18.419135+00	2014-07-18 22:06:18.419156+00
125	48	32	CR	\N	Pabitra Dash	2014-07-18 22:06:18.421997+00	2014-07-18 22:06:18.422017+00
126	49	32	T	\N	Test	2014-07-18 22:43:29.42539+00	2014-07-18 22:43:29.425432+00
127	49	32	AB	\N	Test	2014-07-18 22:43:29.429101+00	2014-07-18 22:43:29.429125+00
128	49	32	DT	\N	2014-07-18T22:43:29.403846+00:00	2014-07-18 22:43:29.432252+00	2014-07-18 22:43:29.432275+00
129	49	32	CN	\N	Jefferson Heard	2014-07-18 22:43:29.435318+00	2014-07-18 22:43:29.43534+00
130	49	32	CR	\N	Jefferson Heard	2014-07-18 22:43:29.438574+00	2014-07-18 22:43:29.4386+00
131	50	32	T	\N	Test resource-2 by PK	2014-07-18 23:53:51.356609+00	2014-07-18 23:53:51.356648+00
132	50	32	AB	\N	Test-2	2014-07-18 23:53:51.360215+00	2014-07-18 23:53:51.360237+00
133	50	32	DT	\N	2014-07-18T23:53:51.332313+00:00	2014-07-18 23:53:51.363496+00	2014-07-18 23:53:51.363516+00
134	50	32	CN	\N	Pabitra Dash	2014-07-18 23:53:51.366724+00	2014-07-18 23:53:51.366745+00
135	50	32	CR	\N	Pabitra Dash	2014-07-18 23:53:51.36986+00	2014-07-18 23:53:51.36989+00
136	51	32	T	\N	Sample res-1 by Tester-1	2014-07-19 00:00:34.475203+00	2014-07-19 00:00:34.475238+00
137	51	32	AB	\N	Test	2014-07-19 00:00:34.479249+00	2014-07-19 00:00:34.479272+00
138	51	32	DT	\N	2014-07-19T00:00:34.442806+00:00	2014-07-19 00:00:34.482671+00	2014-07-19 00:00:34.482701+00
139	51	32	CN	\N	Test Dash	2014-07-19 00:00:34.485883+00	2014-07-19 00:00:34.485906+00
140	51	32	CR	\N	Test Dash	2014-07-19 00:00:34.48892+00	2014-07-19 00:00:34.48895+00
141	48	32	FMT	\N	csv/text	2014-07-20 04:46:29.967881+00	2014-07-20 04:46:29.967908+00
142	48	32	AB	\N	This is the abstract for this resource	2014-07-20 04:47:05.268291+00	2014-07-20 04:47:05.268316+00
143	48	32	SUB	\N	ueb	2014-07-20 04:47:38.239451+00	2014-07-20 04:47:38.239475+00
144	48	32	LG	\N	English	2014-07-20 04:48:01.796831+00	2014-07-20 04:48:01.796854+00
145	48	32	RT	\N	This is the rights statement for this resource	2014-07-20 04:50:22.70082+00	2014-07-20 04:50:22.700845+00
146	48	32	PD	\N	start=01-01-2000, end=01-12-2005	2014-07-20 04:54:22.725344+00	2014-07-20 04:54:22.725367+00
147	48	32	PBL	\N	Hydroshare	2014-07-20 04:55:37.390239+00	2014-07-20 04:55:37.390264+00
148	52	32	T	\N	Test resource public dtarb	2014-07-20 12:57:43.617806+00	2014-07-20 12:57:43.61783+00
149	52	32	AB	\N	Test resource public dtarb	2014-07-20 12:57:43.621348+00	2014-07-20 12:57:43.62137+00
150	52	32	DT	\N	2014-07-20T12:57:43.593717+00:00	2014-07-20 12:57:43.624304+00	2014-07-20 12:57:43.624325+00
151	52	32	CN	\N	David Tarboton	2014-07-20 12:57:43.627402+00	2014-07-20 12:57:43.627434+00
152	52	32	CR	\N	David Tarboton	2014-07-20 12:57:43.63055+00	2014-07-20 12:57:43.630573+00
153	53	32	T	\N	Test resource shared with davidG	2014-07-20 12:59:07.368825+00	2014-07-20 12:59:07.368855+00
154	53	32	AB	\N	Test resource shared with davidG	2014-07-20 12:59:07.372677+00	2014-07-20 12:59:07.3727+00
155	53	32	DT	\N	2014-07-20T12:59:07.343873+00:00	2014-07-20 12:59:07.375671+00	2014-07-20 12:59:07.375693+00
156	53	32	CN	\N	David Tarboton	2014-07-20 12:59:07.37877+00	2014-07-20 12:59:07.378791+00
157	53	32	CR	\N	David Tarboton	2014-07-20 12:59:07.394457+00	2014-07-20 12:59:07.394483+00
158	54	32	T	\N	test resource shared with david G view	2014-07-20 13:02:01.45314+00	2014-07-20 13:02:01.453186+00
159	54	32	AB	\N	test resource shared with david G view	2014-07-20 13:02:01.456719+00	2014-07-20 13:02:01.456741+00
160	54	32	DT	\N	2014-07-20T13:02:01.416498+00:00	2014-07-20 13:02:01.460726+00	2014-07-20 13:02:01.460748+00
161	54	32	CN	\N	David Tarboton	2014-07-20 13:02:01.464118+00	2014-07-20 13:02:01.464139+00
162	54	32	CR	\N	David Tarboton	2014-07-20 13:02:01.467849+00	2014-07-20 13:02:01.467871+00
163	55	32	T	\N	Test resource public davidg	2014-07-20 13:11:47.009265+00	2014-07-20 13:11:47.0093+00
164	55	32	AB	\N	Test resource public davidg	2014-07-20 13:11:47.014457+00	2014-07-20 13:11:47.01448+00
165	55	32	DT	\N	2014-07-20T13:11:46.920720+00:00	2014-07-20 13:11:47.017582+00	2014-07-20 13:11:47.017605+00
166	55	32	CN	\N	DavidG Tarboton	2014-07-20 13:11:47.02055+00	2014-07-20 13:11:47.020572+00
167	55	32	CR	\N	DavidG Tarboton	2014-07-20 13:11:47.023612+00	2014-07-20 13:11:47.023634+00
168	56	32	T	\N	Test resource shared with dtarb	2014-07-20 13:17:15.958029+00	2014-07-20 13:17:15.958063+00
169	56	32	AB	\N	Test resource shared with dtarb	2014-07-20 13:17:15.961754+00	2014-07-20 13:17:15.961775+00
170	56	32	DT	\N	2014-07-20T13:17:15.878432+00:00	2014-07-20 13:17:15.965511+00	2014-07-20 13:17:15.965533+00
171	56	32	CN	\N	DavidG Tarboton	2014-07-20 13:17:15.968728+00	2014-07-20 13:17:15.968749+00
172	56	32	CR	\N	DavidG Tarboton	2014-07-20 13:17:15.971878+00	2014-07-20 13:17:15.9719+00
173	48	32	AB	\N	This is a test abstract	2014-07-21 15:27:42.123558+00	2014-07-21 15:27:42.123584+00
174	48	32	CR	\N	Jhon Smith	2014-07-21 15:29:18.985962+00	2014-07-21 15:29:18.985985+00
175	48	32	CN	\N	Lisa Anderson	2014-07-21 15:29:55.457255+00	2014-07-21 15:29:55.457279+00
176	55	32	DM	\N	2014-07-26T04:07:48.750412+00:00	2014-07-26 04:07:48.750717+00	2014-07-26 04:07:48.750741+00
177	57	32	T	\N	Example Instance XML	2014-08-01 18:19:18.359321+00	2014-08-01 18:19:18.35935+00
178	57	32	AB	\N	This is a test	2014-08-01 18:19:18.546441+00	2014-08-01 18:19:18.546473+00
179	57	32	DT	\N	2014-08-01T18:19:15.718515+00:00	2014-08-01 18:19:18.774444+00	2014-08-01 18:19:18.774477+00
180	57	32	DC	\N	2014-08-01T18:19:15.718529+00:00	2014-08-01 18:19:18.901458+00	2014-08-01 18:19:18.90149+00
181	57	32	CN	\N	david valentine	2014-08-01 18:19:19.034265+00	2014-08-01 18:19:19.034297+00
182	57	32	CR	\N	david valentine	2014-08-01 18:19:19.138775+00	2014-08-01 18:19:19.138817+00
183	58	32	T	\N	Test - push files in github	2014-08-26 18:51:19.533379+00	2014-08-26 18:51:19.53342+00
184	58	32	AB	\N	blah, blah, cannot spell blah	2014-08-26 18:51:19.536845+00	2014-08-26 18:51:19.536866+00
185	58	32	DT	\N	2014-08-26T18:51:19.412627+00:00	2014-08-26 18:51:19.539873+00	2014-08-26 18:51:19.539895+00
186	58	32	DC	\N	2014-08-26T18:51:19.412641+00:00	2014-08-26 18:51:19.542926+00	2014-08-26 18:51:19.542947+00
187	58	32	CN	\N	Michael Stealey	2014-08-26 18:51:19.546013+00	2014-08-26 18:51:19.546035+00
188	58	32	CR	\N	Michael Stealey	2014-08-26 18:51:19.549116+00	2014-08-26 18:51:19.549138+00
\.


--
-- Name: dublincore_qualifieddublincoreelement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('dublincore_qualifieddublincoreelement_id_seq', 188, true);


--
-- Data for Name: dublincore_qualifieddublincoreelementhistory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY dublincore_qualifieddublincoreelementhistory (id, object_id, content_type_id, term, qualifier, content, updated_at, created_at, qdce_id, qdce_id_stored) FROM stdin;
\.


--
-- Name: dublincore_qualifieddublincoreelementhistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('dublincore_qualifieddublincoreelementhistory_id_seq', 1, false);


--
-- Data for Name: forms_field; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY forms_field (_order, form_id, "default", required, label, visible, help_text, choices, id, placeholder_text, field_type) FROM stdin;
\.


--
-- Name: forms_field_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('forms_field_id_seq', 1, false);


--
-- Data for Name: forms_fieldentry; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY forms_fieldentry (entry_id, field_id, id, value) FROM stdin;
\.


--
-- Name: forms_fieldentry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('forms_fieldentry_id_seq', 1, false);


--
-- Data for Name: forms_form; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY forms_form (email_message, page_ptr_id, email_copies, button_text, response, content, send_email, email_subject, email_from) FROM stdin;
	24		Resend verification	<p>Verification email sent!</p>	<p>Please give us your email address and we will resend the confirmation</p>	f		
\.


--
-- Data for Name: forms_formentry; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY forms_formentry (entry_time, id, form_id) FROM stdin;
\.


--
-- Name: forms_formentry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('forms_formentry_id_seq', 1, false);


--
-- Data for Name: ga_irods_rodsenvironment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_irods_rodsenvironment (id, owner_id, host, port, def_res, home_coll, cwd, username, zone, auth) FROM stdin;
\.


--
-- Name: ga_irods_rodsenvironment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ga_irods_rodsenvironment_id_seq', 1, false);


--
-- Data for Name: ga_resources_catalogpage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_catalogpage (page_ptr_id, public, owner_id) FROM stdin;
17	t	2
\.


--
-- Data for Name: ga_resources_dataresource; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_dataresource (page_ptr_id, content, resource_file, resource_url, resource_config, last_change, last_refresh, next_refresh, refresh_every, md5sum, metadata_url, metadata_xml, native_bounding_box, bounding_box, three_d, native_srs, public, owner_id, driver, big) FROM stdin;
\.


--
-- Data for Name: ga_resources_orderedresource; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_orderedresource (id, resource_group_id, data_resource_id, ordering) FROM stdin;
\.


--
-- Name: ga_resources_orderedresource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ga_resources_orderedresource_id_seq', 1, false);


--
-- Data for Name: ga_resources_relatedresource; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_relatedresource (page_ptr_id, content, resource_file, foreign_resource_id, foreign_key, local_key, left_index, right_index, how, driver, key_transform) FROM stdin;
\.


--
-- Data for Name: ga_resources_renderedlayer; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_renderedlayer (page_ptr_id, content, data_resource_id, default_style_id, default_class, public, owner_id) FROM stdin;
\.


--
-- Data for Name: ga_resources_renderedlayer_styles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_renderedlayer_styles (id, renderedlayer_id, style_id) FROM stdin;
\.


--
-- Name: ga_resources_renderedlayer_styles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ga_resources_renderedlayer_styles_id_seq', 1, false);


--
-- Data for Name: ga_resources_resourcegroup; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_resourcegroup (page_ptr_id, is_timeseries, min_time, max_time) FROM stdin;
\.


--
-- Data for Name: ga_resources_style; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_style (page_ptr_id, legend, legend_width, legend_height, stylesheet, public, owner_id) FROM stdin;
\.


--
-- Data for Name: galleries_gallery; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY galleries_gallery (page_ptr_id, content, zip_import) FROM stdin;
\.


--
-- Data for Name: galleries_galleryimage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY galleries_galleryimage (id, _order, gallery_id, file, description) FROM stdin;
\.


--
-- Name: galleries_galleryimage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('galleries_galleryimage_id_seq', 1, false);


--
-- Data for Name: generic_assignedkeyword; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY generic_assignedkeyword (content_type_id, id, keyword_id, object_pk, _order) FROM stdin;
32	32	4	18	0
32	33	5	18	1
32	34	6	18	2
32	38	13	37	0
32	39	14	38	0
32	40	15	38	1
32	41	15	39	0
32	42	16	40	0
32	43	17	41	0
32	44	18	41	1
32	45	19	41	2
32	46	20	42	0
32	47	21	42	1
32	48	22	42	2
32	49	23	42	3
32	50	24	42	4
32	52	26	57	0
32	53	27	57	1
\.


--
-- Name: generic_assignedkeyword_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('generic_assignedkeyword_id_seq', 53, true);


--
-- Data for Name: generic_keyword; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY generic_keyword (slug, id, title, site_id) FROM stdin;
a	1	a	1
b	2	b	1
c	3	c	1
generic	4	generic	1
resources	5	resources	1
csv	6	csv	1
melanoma	7	melanoma	1
bioinformatics	8	bioinformatics	1
keyword	9	keyword	1
proteins	10	proteins	1
gene-ontology	11	gene ontology	1
visualization	12	visualization	1
model-metadata	13	Model Metadata	1
restoration	14	restoration	1
provo-river	15	provo river	1
epa-swmm-model	16	EPA-SWMM model	1
csdms	17	CSDMS	1
wmt	18	WMT	1
hydrotrend	19	HydroTrend	1
temperature	20	Temperature	1
water	21	Water	1
little-bear-river	22	Little Bear River	1
utah	23	Utah	1
water-quality	24	Water Quality	1
keywords	25	Keywords	1
xml	26	xml	1
waterml	27	waterml	1
\.


--
-- Name: generic_keyword_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('generic_keyword_id_seq', 27, true);


--
-- Data for Name: generic_rating; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY generic_rating (content_type_id, id, value, object_pk, rating_date, user_id) FROM stdin;
22	2	1	3	2014-06-06 14:49:29.400266+00	2
\.


--
-- Name: generic_rating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('generic_rating_id_seq', 5, true);


--
-- Data for Name: generic_threadedcomment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY generic_threadedcomment (by_author, comment_ptr_id, replied_to_id, rating_count, rating_average, rating_sum) FROM stdin;
t	3	\N	1	1	1
t	6	\N	0	0	0
f	7	\N	0	0	0
f	8	\N	0	0	0
\.


--
-- Data for Name: hs_core_bags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_bags (id, object_id, content_type_id, "timestamp", bag) FROM stdin;
1	18	32	2014-04-16 15:24:10.830979+00	bags/8a631acc5ea64187bdb331da667f7660.zip
2	18	32	2014-06-04 13:44:16.687587+00	bags/8a631acc5ea64187bdb331da667f7660_1.zip
3	18	32	2014-06-04 13:49:28.227223+00	bags/8a631acc5ea64187bdb331da667f7660_2.zip
4	18	32	2014-06-04 16:54:29.963921+00	bags/8a631acc5ea64187bdb331da667f7660_3.zip
12	18	32	2014-06-11 12:28:52.524444+00	bags/8a631acc5ea64187bdb331da667f7660_4.zip
22	37	32	2014-06-11 17:12:11.369766+00	bags/18159123aca543e2bdd434536f38c889.zip
23	37	32	2014-06-11 17:30:48.130381+00	bags/18159123aca543e2bdd434536f38c889_1.zip
24	38	32	2014-06-11 17:31:48.8472+00	bags/0ae210619bbb408dbcc46a32759e3fce.zip
25	39	32	2014-06-11 18:53:30.012053+00	bags/eceb8ce9711e4ed3a64878bef2640811.zip
26	39	32	2014-06-11 18:54:52.918373+00	bags/eceb8ce9711e4ed3a64878bef2640811_1.zip
27	40	32	2014-06-12 13:20:19.717702+00	bags/ae21c4f108fd4600a7653e51c76b3797.zip
28	41	32	2014-06-13 19:08:43.919745+00	bags/126c860945a94585bf3c6d6f8aacb26d.zip
29	42	32	2014-06-14 22:47:25.975798+00	bags/9981905ea8d646ddbdaf3a296e91b685.zip
31	45	32	2014-07-18 17:59:50.336708+00	bags/cf69af116a944cfeab8984ed7d697204.zip
32	46	32	2014-07-18 18:33:01.975064+00	bags/aabfbcfd58c944ea940d6ed3ecb9508c.zip
33	46	32	2014-07-18 18:38:41.502608+00	bags/aabfbcfd58c944ea940d6ed3ecb9508c_1.zip
34	46	32	2014-07-18 18:39:13.716033+00	bags/aabfbcfd58c944ea940d6ed3ecb9508c_2.zip
35	47	32	2014-07-18 18:49:16.782872+00	bags/c9d484f819da4049b1a6221e5233e8e2.zip
36	48	32	2014-07-18 22:06:18.388064+00	bags/800d9886d6d94073bbc1bb0c0d75627b.zip
37	49	32	2014-07-18 22:43:29.40739+00	bags/1468fce192b6458eaeb9c3e9b667dbb3.zip
38	49	32	2014-07-18 22:43:40.512075+00	bags/1468fce192b6458eaeb9c3e9b667dbb3_1.zip
39	50	32	2014-07-18 23:53:51.336229+00	bags/5d5987f2cd0f48ab8a96da8e7c4c7f7e.zip
40	51	32	2014-07-19 00:00:34.449123+00	bags/871f0c809d3f4ed0badda1eec92fb4fb.zip
41	48	32	2014-07-20 04:46:29.973947+00	bags/800d9886d6d94073bbc1bb0c0d75627b_1.zip
42	48	32	2014-07-20 04:47:05.274709+00	bags/800d9886d6d94073bbc1bb0c0d75627b_2.zip
43	48	32	2014-07-20 04:47:38.244226+00	bags/800d9886d6d94073bbc1bb0c0d75627b_3.zip
44	48	32	2014-07-20 04:48:01.818859+00	bags/800d9886d6d94073bbc1bb0c0d75627b_4.zip
45	48	32	2014-07-20 04:50:22.706968+00	bags/800d9886d6d94073bbc1bb0c0d75627b_5.zip
46	48	32	2014-07-20 04:54:22.73122+00	bags/800d9886d6d94073bbc1bb0c0d75627b_6.zip
47	48	32	2014-07-20 04:55:37.396223+00	bags/800d9886d6d94073bbc1bb0c0d75627b_7.zip
48	52	32	2014-07-20 12:57:43.597399+00	bags/76410211163b45fc9703af14f2b5eb16.zip
49	53	32	2014-07-20 12:59:07.347394+00	bags/98b1c36bcc1e492d8a0eab889cce4f73.zip
50	54	32	2014-07-20 13:02:01.421387+00	bags/f7be27b59697451891388e6ec96a9492.zip
51	55	32	2014-07-20 13:11:46.924359+00	bags/95238a2b33eb472f83048998ec8dfbbc.zip
52	56	32	2014-07-20 13:17:15.882149+00	bags/06a6986e363f414a8be5c739fcfaa12a.zip
53	48	32	2014-07-21 15:27:42.128084+00	bags/800d9886d6d94073bbc1bb0c0d75627b_8.zip
54	48	32	2014-07-21 15:29:18.993095+00	bags/800d9886d6d94073bbc1bb0c0d75627b_9.zip
55	48	32	2014-07-21 15:29:55.461353+00	bags/800d9886d6d94073bbc1bb0c0d75627b_10.zip
56	55	32	2014-07-26 04:07:48.754278+00	bags/95238a2b33eb472f83048998ec8dfbbc_1.zip
57	57	32	2014-08-01 18:19:15.925066+00	bags/845593639ca84cd19dfa8e72d2acc708.zip
58	58	32	2014-08-26 18:51:19.446543+00	bags/6467794b65ea47d389a6c4e99da07175.zip
\.


--
-- Name: hs_core_bags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_bags_id_seq', 58, true);


--
-- Data for Name: hs_core_contributor; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_contributor (id, object_id, content_type_id, description, name, organization, email, address, phone, homepage, "researcherID", "researchGateID") FROM stdin;
\.


--
-- Name: hs_core_contributor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_contributor_id_seq', 1, false);


--
-- Data for Name: hs_core_coremetadata; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_coremetadata (id) FROM stdin;
1
\.


--
-- Name: hs_core_coremetadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_coremetadata_id_seq', 1, true);


--
-- Data for Name: hs_core_coverage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_coverage (id, object_id, content_type_id, type, _value) FROM stdin;
\.


--
-- Name: hs_core_coverage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_coverage_id_seq', 1, false);


--
-- Data for Name: hs_core_creator; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_creator (id, object_id, content_type_id, description, name, organization, email, address, phone, homepage, "researcherID", "researchGateID", "order") FROM stdin;
1	1	93	\N	Michael Stealey	\N	stealey@renci.org	\N	\N	\N	\N	\N	1
\.


--
-- Name: hs_core_creator_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_creator_id_seq', 1, true);


--
-- Data for Name: hs_core_date; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_date (id, object_id, content_type_id, type, start_date, end_date) FROM stdin;
1	1	93	created	2014-08-26 18:51:19.434524+00	\N
2	1	93	modified	2014-08-26 18:51:19.446543+00	\N
\.


--
-- Name: hs_core_date_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_date_id_seq', 2, true);


--
-- Data for Name: hs_core_description; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_description (id, object_id, content_type_id, abstract) FROM stdin;
1	1	93	blah, blah, cannot spell blah
\.


--
-- Name: hs_core_description_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_description_id_seq', 1, true);


--
-- Data for Name: hs_core_externalprofilelink; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_externalprofilelink (id, type, url, object_id, content_type_id) FROM stdin;
\.


--
-- Name: hs_core_externalprofilelink_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_externalprofilelink_id_seq', 1, false);


--
-- Data for Name: hs_core_format; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_format (id, object_id, content_type_id, value) FROM stdin;
\.


--
-- Name: hs_core_format_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_format_id_seq', 1, false);


--
-- Data for Name: hs_core_genericresource; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource (page_ptr_id, content, user_id, creator_id, public, frozen, do_not_distribute, discoverable, published_and_frozen, last_changed_by_id, comments_count, short_id, doi, object_id, content_type_id) FROM stdin;
52	<p>2. Test resource public dtarb</p>	12	12	t	f	f	t	f	12	0	76410211163b45fc9703af14f2b5eb16		\N	\N
47	Peuker Douglas DEM	37	37	t	f	f	t	f	37	0	c9d484f819da4049b1a6221e5233e8e2	\N	\N	\N
39	Provo river water flow measurements taken before and during river restoration efforts. 	30	30	t	f	f	t	f	30	1	eceb8ce9711e4ed3a64878bef2640811	\N	\N	\N
40	calibrated EPA-SWMM model for Rocky Branch watershed, Columbia, SC	33	33	t	f	f	t	f	33	0	ae21c4f108fd4600a7653e51c76b3797	\N	\N	\N
53	<p>4. Test resource shared with davidG</p>	12	12	f	f	f	t	f	12	0	98b1c36bcc1e492d8a0eab889cce4f73		\N	\N
42	This resource contains water temperature observations in the Little Bear River at Mendon Road near Mendon, Utah, USA. The values represent 30-minut average values and were measured using a Hydrolap Minisonde 4 multi-parameter water quality sonde.  Values are recorded at the end of each 30 minute interval and represent the average water temperature over the preceding 30-minute interval. The data have been subject to multiple quality control tests, removing obviously bad data and known errors.	9	9	t	f	f	t	f	9	2	9981905ea8d646ddbdaf3a296e91b685	\N	\N	\N
37	Computer models are widely used in hydrology and water resources management. A large variety of models exist, each tailored to address specific challenges related to hydrologic science and water resources management. When scientists and engineers apply one of these models to address a specific question, they must devote significant effort to set up, calibrate, and evaluate that model instance built for some place and time. In many cases, there is a benefit to sharing these computer models and associated datasets with the broader scientific community. Core to model reuse in any context is metadata describing the model. A standardized metadata framework applicable across models will foster interoperability and encourage reuse and sharing of existing resources. This paper reports on the development of a metadata framework for describing water models. We discuss steps taken to achieve this goal for the HydroShare system and within the context of a use case that describes a team-based hydrologic modeling project.\r\n	29	29	t	f	f	t	f	29	0	18159123aca543e2bdd434536f38c889	\N	\N	\N
38	This data was gathered for the purpose of monitoring gain of water flow due to river restoration efforts. 	30	30	t	f	f	t	f	30	0	0ae210619bbb408dbcc46a32759e3fce	\N	\N	\N
45	Torrent	14	14	t	f	f	t	f	14	0	cf69af116a944cfeab8984ed7d697204	\N	\N	\N
18	<p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?</p>	2	2	t	f	f	t	f	2	1	8a631acc5ea64187bdb331da667f7660		\N	\N
41	A CSDMS Web Modeling Tool model run of the HydroTrend component with default model parameters.	29	29	t	f	f	t	f	29	0	126c860945a94585bf3c6d6f8aacb26d	\N	\N	\N
49	Test	14	14	t	f	f	t	f	14	0	1468fce192b6458eaeb9c3e9b667dbb3	\N	\N	\N
54	<p>5. test resource shared with david G view</p>	12	12	f	f	f	t	f	12	0	f7be27b59697451891388e6ec96a9492		\N	\N
50	Test-2	38	38	t	f	f	t	f	38	0	5d5987f2cd0f48ab8a96da8e7c4c7f7e	\N	\N	\N
51	Test	39	39	t	f	f	t	f	39	0	871f0c809d3f4ed0badda1eec92fb4fb	\N	\N	\N
46	Tiff File for unknown location	12	12	f	f	f	t	f	12	0	aabfbcfd58c944ea940d6ed3ecb9508c	\N	\N	\N
58	blah, blah, cannot spell blah	40	40	t	f	f	t	f	40	0	6467794b65ea47d389a6c4e99da07175	\N	1	93
48	<p>Test</p>	38	38	f	f	f	t	f	38	0	800d9886d6d94073bbc1bb0c0d75627b		\N	\N
44	Torrent	14	14	t	f	f	t	f	14	0	a132d22841a1469995b51d5c66c50c79	\N	\N	\N
56	<p>3. Test resource shared with dtarb</p>	37	37	f	f	f	t	f	37	0	06a6986e363f414a8be5c739fcfaa12a		\N	\N
55	<p>1. Test resource public davidg</p>	37	37	f	f	f	t	f	37	0	95238a2b33eb472f83048998ec8dfbbc		\N	\N
57	This is a test	13	13	f	f	f	t	f	13	0	845593639ca84cd19dfa8e72d2acc708	\N	\N	\N
\.


--
-- Data for Name: hs_core_genericresource_edit_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_edit_groups (id, genericresource_id, group_id) FROM stdin;
5	39	1
\.


--
-- Name: hs_core_genericresource_edit_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_edit_groups_id_seq', 5, true);


--
-- Data for Name: hs_core_genericresource_edit_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_edit_users (id, genericresource_id, user_id) FROM stdin;
13	18	17
14	18	2
16	37	29
17	38	30
20	39	14
21	39	30
22	40	33
23	41	29
24	42	9
26	45	14
27	46	12
28	47	37
30	49	14
31	50	38
33	51	38
35	48	39
42	55	37
43	56	37
44	52	12
45	53	12
46	54	12
47	57	13
48	58	40
\.


--
-- Name: hs_core_genericresource_edit_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_edit_users_id_seq', 48, true);


--
-- Data for Name: hs_core_genericresource_owners; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_owners (id, genericresource_id, user_id) FROM stdin;
13	18	2
14	18	3
16	37	29
17	38	30
19	39	11
20	39	14
21	39	30
22	40	33
23	41	29
24	42	9
26	45	14
27	46	12
28	47	37
31	50	38
35	48	38
44	55	37
45	56	37
46	52	12
47	53	12
48	53	37
49	54	12
50	51	38
53	49	14
54	55	9
55	57	13
56	58	40
\.


--
-- Name: hs_core_genericresource_owners_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_owners_id_seq', 56, true);


--
-- Data for Name: hs_core_genericresource_view_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_view_groups (id, genericresource_id, group_id) FROM stdin;
6	18	1
\.


--
-- Name: hs_core_genericresource_view_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_view_groups_id_seq', 6, true);


--
-- Data for Name: hs_core_genericresource_view_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_view_users (id, genericresource_id, user_id) FROM stdin;
11	18	2
13	37	29
14	38	30
15	39	30
16	40	33
17	41	29
18	42	9
20	45	14
21	46	12
22	47	37
24	49	14
25	50	38
26	51	39
27	48	38
36	55	37
37	56	12
38	52	12
39	53	12
40	54	37
41	57	13
42	58	40
\.


--
-- Name: hs_core_genericresource_view_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_view_users_id_seq', 42, true);


--
-- Data for Name: hs_core_groupownership; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_groupownership (id, group_id, owner_id) FROM stdin;
\.


--
-- Name: hs_core_groupownership_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_groupownership_id_seq', 1, false);


--
-- Data for Name: hs_core_identifier; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_identifier (id, object_id, content_type_id, name, url) FROM stdin;
1	1	93	hydroShareIdentifier	http://hydroshare.org/resource/6467794b65ea47d389a6c4e99da07175
\.


--
-- Name: hs_core_identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_identifier_id_seq', 1, true);


--
-- Data for Name: hs_core_language; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_language (id, object_id, content_type_id, code) FROM stdin;
\.


--
-- Name: hs_core_language_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_language_id_seq', 1, false);


--
-- Data for Name: hs_core_publisher; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_publisher (id, object_id, content_type_id, name, url) FROM stdin;
\.


--
-- Name: hs_core_publisher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_publisher_id_seq', 1, false);


--
-- Data for Name: hs_core_relation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_relation (id, object_id, content_type_id, type, value) FROM stdin;
\.


--
-- Name: hs_core_relation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_relation_id_seq', 1, false);


--
-- Data for Name: hs_core_resourcefile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_resourcefile (id, object_id, content_type_id, resource_file) FROM stdin;
1	18	32	8a631acc5ea64187bdb331da667f7660/TeacherTurnover_CleanData_102413.csv
2	18	32	8a631acc5ea64187bdb331da667f7660/TeacherTurnover_CleanData_102414_1.csv
3	18	32	8a631acc5ea64187bdb331da667f7660/TeacherTurnover_CleanData_102414.csv
4	18	32	8a631acc5ea64187bdb331da667f7660/3909000656_2e8d99d667_b.jpg
88	45	32	cf69af116a944cfeab8984ed7d697204/IMG_20140607_203907.jpg_1.xmp
89	49	32	1468fce192b6458eaeb9c3e9b667dbb3/IMG_20140607_203907.jpg.xmp
90	49	32	1468fce192b6458eaeb9c3e9b667dbb3/IMG_20140516_202353~2.jpg.xmp
91	50	32	5d5987f2cd0f48ab8a96da8e7c4c7f7e/test-data.tif
92	51	32	871f0c809d3f4ed0badda1eec92fb4fb/param.dat
93	52	32	76410211163b45fc9703af14f2b5eb16/HIC2014-1566.pdf
94	53	32	98b1c36bcc1e492d8a0eab889cce4f73/HIC2014-1566.pdf
95	54	32	f7be27b59697451891388e6ec96a9492/HIC2014-1566.pdf
16	37	32	18159123aca543e2bdd434536f38c889/fig03.pdf
17	37	32	18159123aca543e2bdd434536f38c889/fig02.pdf
18	37	32	18159123aca543e2bdd434536f38c889/fig01.pdf
19	37	32	18159123aca543e2bdd434536f38c889/fig04.pdf
20	37	32	18159123aca543e2bdd434536f38c889/iemss.pdf
21	38	32	0ae210619bbb408dbcc46a32759e3fce/hydrologicdata.csv
22	39	32	eceb8ce9711e4ed3a64878bef2640811/hydrologicdata.csv
23	40	32	ae21c4f108fd4600a7653e51c76b3797/swmmsw.jpg
24	41	32	126c860945a94585bf3c6d6f8aacb26d/40e61b50-80a7-4dee-82bc-e18b8aec0e75.tar
25	42	32	9981905ea8d646ddbdaf3a296e91b685/LBR_Mendon_WaterTemperature_QC1.csv
27	45	32	cf69af116a944cfeab8984ed7d697204/docker-hydroshare.zip.torrent
28	46	32	aabfbcfd58c944ea940d6ed3ecb9508c/b_srtm25m.tif
29	47	32	c9d484f819da4049b1a6221e5233e8e2/b_srtm25mss.tif
30	47	32	<?xml version="1.0" encoding="UTF-8"?>\r\n
31	48	32	800d9886d6d94073bbc1bb0c0d75627b/empty-test.dat
32	45	32	<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n
33	45	32	<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">\n
34	45	32	 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n
35	45	32	  <rdf:Description rdf:about=""\n
36	45	32	    xmlns:xmp="http://ns.adobe.com/xap/1.0/"\n
37	45	32	    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"\n
38	45	32	    xmlns:darktable="http://darktable.sf.net/"\n
39	45	32	    xmlns:lr="http://ns.adobe.com/lightroom/1.0/"\n
40	45	32	    xmlns:dc="http://purl.org/dc/elements/1.1/"\n
41	45	32	   xmp:Rating="1"\n
42	45	32	   xmpMM:DerivedFrom="IMG_20140607_203907.jpg"\n
43	45	32	   darktable:xmp_version="1"\n
44	45	32	   darktable:raw_params="0"\n
45	45	32	   darktable:auto_presets_applied="1">\n
46	45	32	   <darktable:colorlabels>\n
47	45	32	    <rdf:Seq/>\n
48	45	32	   </darktable:colorlabels>\n
49	45	32	   <darktable:history_modversion>\n
50	45	32	    <rdf:Seq/>\n
51	45	32	   </darktable:history_modversion>\n
52	45	32	   <darktable:history_enabled>\n
53	45	32	    <rdf:Seq/>\n
54	45	32	   </darktable:history_enabled>\n
55	45	32	   <darktable:history_operation>\n
56	45	32	    <rdf:Seq/>\n
57	45	32	   </darktable:history_operation>\n
58	45	32	   <darktable:history_params>\n
59	45	32	    <rdf:Seq/>\n
60	45	32	   </darktable:history_params>\n
61	45	32	   <darktable:blendop_params>\n
62	45	32	    <rdf:Seq/>\n
63	45	32	   </darktable:blendop_params>\n
64	45	32	   <darktable:blendop_version>\n
65	45	32	    <rdf:Seq/>\n
66	45	32	   </darktable:blendop_version>\n
67	45	32	   <darktable:multi_priority>\n
68	45	32	    <rdf:Seq/>\n
69	45	32	   </darktable:multi_priority>\n
70	45	32	   <darktable:multi_name>\n
71	45	32	    <rdf:Seq/>\n
72	45	32	   </darktable:multi_name>\n
73	45	32	   <lr:hierarchicalSubject>\n
74	45	32	    <rdf:Seq/>\n
75	45	32	   </lr:hierarchicalSubject>\n
76	45	32	   <dc:description>\n
77	45	32	    <rdf:Alt>\n
78	45	32	     <rdf:li xml:lang="x-default">&#xA;</rdf:li>\n
79	45	32	    </rdf:Alt>\n
80	45	32	   </dc:description>\n
81	45	32	   <dc:subject>\n
82	45	32	    <rdf:Seq/>\n
83	45	32	   </dc:subject>\n
84	45	32	  </rdf:Description>\n
85	45	32	 </rdf:RDF>\n
86	45	32	</x:xmpmeta>\n
87	45	32	cf69af116a944cfeab8984ed7d697204/IMG_20140607_203907.jpg.xmp
97	56	32	06a6986e363f414a8be5c739fcfaa12a/CedarCreekdgt.zip
98	57	32	845593639ca84cd19dfa8e72d2acc708/instance1.xml
99	58	32	6467794b65ea47d389a6c4e99da07175/How To Push-Pull Changes in GitHub.pdf
\.


--
-- Name: hs_core_resourcefile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_resourcefile_id_seq', 99, true);


--
-- Data for Name: hs_core_rights; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_rights (id, object_id, content_type_id, statement, url) FROM stdin;
\.


--
-- Name: hs_core_rights_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_rights_id_seq', 1, false);


--
-- Data for Name: hs_core_source; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_source (id, object_id, content_type_id, derived_from) FROM stdin;
\.


--
-- Name: hs_core_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_source_id_seq', 1, false);


--
-- Data for Name: hs_core_subject; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_subject (id, object_id, content_type_id, value) FROM stdin;
\.


--
-- Name: hs_core_subject_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_subject_id_seq', 1, false);


--
-- Data for Name: hs_core_title; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_title (id, object_id, content_type_id, value) FROM stdin;
1	1	93	Test - push files in github
\.


--
-- Name: hs_core_title_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_title_id_seq', 1, true);


--
-- Data for Name: hs_core_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_type (id, object_id, content_type_id, url) FROM stdin;
\.


--
-- Name: hs_core_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_type_id_seq', 1, false);


--
-- Data for Name: hs_party_addresscodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_addresscodelist (code, name, "order", url) FROM stdin;
other	Other address	1	
home	Home Address	1	
work	Work Address	1	
mailing	Mailing Address	1	
primary	Primary Mailing Address	99	
\.


--
-- Data for Name: hs_party_choicetype; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_choicetype (id, "choiceType", code, name, "order", url) FROM stdin;
\.


--
-- Name: hs_party_choicetype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_choicetype_id_seq', 1, false);


--
-- Data for Name: hs_party_city; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_city (id, name, "geonamesUrl") FROM stdin;
\.


--
-- Name: hs_party_city_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_city_id_seq', 1, false);


--
-- Data for Name: hs_party_country; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_country (id, name, "geonamesUrl") FROM stdin;
\.


--
-- Name: hs_party_country_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_country_id_seq', 1, false);


--
-- Data for Name: hs_party_emailcodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_emailcodelist (code, name, "order", url) FROM stdin;
other	Other Email	1	
personal	Personal Email	1	
work	Work Email	1	
support	Support Email	1	
primary	Primary Email	99	
mailing list	Mailing List address	3	
\.


--
-- Data for Name: hs_party_externalidentifiercodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_externalidentifiercodelist (code, name, "order", url) FROM stdin;
orcid	ORCID User Identifier	1	http://www.example.com
twitter	Twitter Identity	1	
facebook	Facebook Identity	1	
google	Google Identity	1	
other	Other Identity	1	
\.


--
-- Data for Name: hs_party_externalorgidentifier; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_externalorgidentifier (id, organization_id, "identifierName_id", "otherName", "identifierCode", "createdDate") FROM stdin;
\.


--
-- Name: hs_party_externalorgidentifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_externalorgidentifier_id_seq', 1, false);


--
-- Data for Name: hs_party_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_group (party_ptr_id, keywords_string, site_id, title, slug, _meta_title, description, gen_description, created, updated, status, publish_date, expiry_date, short_url, in_sitemap) FROM stdin;
\.


--
-- Data for Name: hs_party_namealiascodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_namealiascodelist (code, name, "order", url) FROM stdin;
other	Other Alternate Name	9	
change	Name Change	8	
citation	Publishing Alias, or Name utilized on a publication	2	
fullname	Full Name, or Alternate Full Name	3	
acronym	Acronym, or nickname	4	
\.


--
-- Data for Name: hs_party_organization; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organization (party_ptr_id, specialities_string, keywords_string, site_id, title, slug, _meta_title, description, gen_description, created, updated, status, publish_date, expiry_date, short_url, in_sitemap, "logoUrl", "parentOrganization_id", "organizationType_id") FROM stdin;
1			1			\N	Default Organization	t	2014-07-30 22:02:09.184+00	2014-07-30 22:02:09.184+00	2	2014-07-30 22:02:09.109+00	\N	\N	t		\N	other
\.


--
-- Data for Name: hs_party_organizationassociation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organizationassociation (id, "createdDate", "uniqueCode", organization_id, person_id, "beginDate", "endDate", "jobTitle", "presentOrganization") FROM stdin;
1	2014-07-30	c74dc1ce-d0b6-472e-8c63-4b5ce2ce9869	1	2	2014-07-28	\N	Researcher	t
\.


--
-- Name: hs_party_organizationassociation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_organizationassociation_id_seq', 1, true);


--
-- Data for Name: hs_party_organizationcodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organizationcodelist (code, name, "order", url) FROM stdin;
other	Other or Unknown Organization	1	
commercial	Commercial/Professional Organization	2	
university	University Organization	3	
college	College	4	
gov	Government Organization	5	
nonprofit	Non-profit Organization	6	
k12	School  Kindergarten to 12th Grade	7	
cc	Community College	7	
unspecified	Unspecified Organization	9	
\.


--
-- Data for Name: hs_party_organizationemail; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organizationemail (id, email, email_type_id, organization_id) FROM stdin;
1	dev@hydroshare.org	other	1
\.


--
-- Name: hs_party_organizationemail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_organizationemail_id_seq', 1, true);


--
-- Data for Name: hs_party_organizationlocation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organizationlocation (id, address, address_type_id, organization_id) FROM stdin;
1	123 street address, logan, UT	primary	1
\.


--
-- Name: hs_party_organizationlocation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_organizationlocation_id_seq', 1, true);


--
-- Data for Name: hs_party_organizationname; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organizationname (id, "otherName", annotation_id, organization_id) FROM stdin;
1	Hydroshare	other	1
\.


--
-- Name: hs_party_organizationname_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_organizationname_id_seq', 1, true);


--
-- Data for Name: hs_party_organizationphone; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_organizationphone (id, phone_number, phone_type_id, organization_id) FROM stdin;
1	000-000-000	other	1
\.


--
-- Name: hs_party_organizationphone_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_organizationphone_id_seq', 1, true);


--
-- Data for Name: hs_party_othername; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_othername (id, "otherName", annotation_id, persons_id) FROM stdin;
1	Sandy Shoot	other	2
2	Me	other	2
\.


--
-- Name: hs_party_othername_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_othername_id_seq', 2, true);


--
-- Data for Name: hs_party_party; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_party (id, "uniqueCode", name, url, notes, "createdDate", "lastUpdate") FROM stdin;
1	61255288-9b62-4e87-8bf7-fed434af5824	Default Organization	http://www.hydroshare.org/	This is a generic organization	2014-07-30	2014-08-29
2	9840268f-d790-4362-954c-fb30d20ebc7a	Sandy Flume			2014-07-30	2014-08-29
\.


--
-- Name: hs_party_party_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_party_id_seq', 2, true);


--
-- Data for Name: hs_party_person; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_person (party_ptr_id, keywords_string, site_id, title, slug, _meta_title, description, gen_description, created, updated, status, publish_date, expiry_date, short_url, in_sitemap, "givenName", "familyName", "jobTitle", "primaryOrganizationRecord_id") FROM stdin;
2		1			\N	Sandy Flume	t	2014-07-30 22:06:02.712+00	2014-07-30 22:06:45.77+00	2	2014-07-30 22:06:02.633+00	\N	\N	t	Sandy	Flume		1
\.


--
-- Data for Name: hs_party_personemail; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_personemail (id, email, email_type_id, person_id) FROM stdin;
1	me@example.com	other	2
\.


--
-- Name: hs_party_personemail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_personemail_id_seq', 1, true);


--
-- Data for Name: hs_party_personexternalidentifier; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_personexternalidentifier (id, person_id, "identifierName_id", "otherName", "identifierCode", "createdDate") FROM stdin;
1	2	twitter		http://example.org/	2014-07-30
\.


--
-- Name: hs_party_personexternalidentifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_personexternalidentifier_id_seq', 1, true);


--
-- Data for Name: hs_party_personlocation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_personlocation (id, address, address_type_id, person_id) FROM stdin;
1	123 Street Address\r\nLogan, UT	primary	2
\.


--
-- Name: hs_party_personlocation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_personlocation_id_seq', 1, true);


--
-- Data for Name: hs_party_personphone; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_personphone (id, phone_number, phone_type_id, person_id) FROM stdin;
1	000-000-0000	other	2
\.


--
-- Name: hs_party_personphone_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_personphone_id_seq', 1, true);


--
-- Data for Name: hs_party_phonecodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_phonecodelist (code, name, "order", url) FROM stdin;
other	Other Phone	1	
work	Work Phone	1	
cell	Cell Phone	1	
home	Home Phone	1	
main	Main company phone	1	
fax	Fax	1	
primary	Primary Phone Number	99	
\.


--
-- Data for Name: hs_party_region; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_region (id, name, "geonamesUrl") FROM stdin;
\.


--
-- Name: hs_party_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_party_region_id_seq', 1, false);


--
-- Data for Name: hs_party_usercodelist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_party_usercodelist (code, name, "order", url) FROM stdin;
faculty	University Faculty	1	
research	University Professional or Research Staff	1	
postdoc	Post-Doctoral Fellow	1	
grad	University Graduate Student	1	
undergrad	University Undergraduate Student	1	
commercial	Commercial/Professional	1	
nonprofit	Non-profit Organizations	1	
k12	School Student Kindergarten to 12th Grade	1	
ccfaculty	Community College Faculty	1	
ccstudent	Community College Student	1	
other	Other type of user	1	
Unspecified	Unspecified type of user	1	
\.


--
-- Data for Name: hs_scholar_profile_city; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_city (id, name, "geonamesUrl") FROM stdin;
\.


--
-- Name: hs_scholar_profile_city_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_city_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_country; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_country (id, name, "geonamesUrl") FROM stdin;
\.


--
-- Name: hs_scholar_profile_country_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_country_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_externalidentifiers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_externalidentifiers (id, "identifierName", "otherName", "identifierCode", "createdDate") FROM stdin;
\.


--
-- Name: hs_scholar_profile_externalidentifiers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_externalidentifiers_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_externalorgidentifiers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_externalorgidentifiers (id, organization_id, "identifierName", "otherName", "identifierCode", "createdDate") FROM stdin;
\.


--
-- Name: hs_scholar_profile_externalorgidentifiers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_externalorgidentifiers_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_organization; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_organization (id, keywords_string, site_id, title, slug, _meta_title, description, gen_description, created, updated, status, publish_date, expiry_date, short_url, in_sitemap, "uniqueCode", name, url, notes, "createdDate", "lastUpdate", "logoUrl", "parentOrganization_id", "organizationType") FROM stdin;
\.


--
-- Name: hs_scholar_profile_organization_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_organization_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_organizationemail; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_organizationemail (id, phone_number, phone_type, organization_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_organizationemail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_organizationemail_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_organizationlocation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_organizationlocation (id, address, address_type, organization_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_organizationlocation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_organizationlocation_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_organizationphone; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_organizationphone (id, phone_number, phone_type, organization_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_organizationphone_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_organizationphone_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_orgassociations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_orgassociations (id, "createdDate", organization_id, person_id, "beginDate", "endDate", "jobTitle", "presentOrganization") FROM stdin;
\.


--
-- Name: hs_scholar_profile_orgassociations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_orgassociations_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_othernames; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_othernames (id, persons_id, "otherName", annotation) FROM stdin;
\.


--
-- Name: hs_scholar_profile_othernames_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_othernames_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_person; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_person (id, keywords_string, site_id, title, slug, _meta_title, description, gen_description, created, updated, status, publish_date, expiry_date, short_url, in_sitemap, "uniqueCode", name, url, notes, "createdDate", "lastUpdate", "givenName", "familyName", "jobTitle") FROM stdin;
2		1		-1	\N	  : admin	t	2014-04-16 15:26:49.298279+00	2014-04-16 15:26:49.298279+00	2	2014-04-16 15:26:49.294029+00	\N	\N	t		 			2014-04-16	2014-04-16			
3		1		-2	\N	  : horsburgh	t	2014-04-16 15:26:49.305331+00	2014-04-16 15:26:49.305331+00	2	2014-04-16 15:26:49.302204+00	\N	\N	t		 			2014-04-16	2014-04-16			
4		1		-3	\N	  : danames	t	2014-04-16 15:26:49.312435+00	2014-04-16 15:26:49.312435+00	2	2014-04-16 15:26:49.308254+00	\N	\N	t		 			2014-04-16	2014-04-16			
5		1		-4	\N	  : martinn	t	2014-04-16 15:26:49.320227+00	2014-04-16 15:26:49.320227+00	2	2014-04-16 15:26:49.315149+00	\N	\N	t		 			2014-04-16	2014-04-16			
6		1		-5	\N	  : jeff	t	2014-04-16 15:26:49.335021+00	2014-04-16 15:26:49.335021+00	2	2014-04-16 15:26:49.323021+00	\N	\N	t		 			2014-04-16	2014-04-16			
7		1		-6	\N	  : dtarb	t	2014-04-16 15:26:49.348777+00	2014-04-16 15:26:49.348777+00	2	2014-04-16 15:26:49.339803+00	\N	\N	t		 			2014-04-16	2014-04-16			
8		1		-7	\N	  : Castronova	t	2014-04-16 15:26:49.35938+00	2014-04-16 15:26:49.35938+00	2	2014-04-16 15:26:49.351622+00	\N	\N	t		 			2014-04-16	2014-04-16			
10		1		-8	\N	  : carolxsong	t	2014-04-16 15:26:58.348618+00	2014-04-16 15:26:58.348618+00	2	2014-04-16 15:26:58.338536+00	\N	\N	t		 			2014-04-16	2014-04-16			
11		1		-9	\N	  : rayi	t	2014-04-16 15:26:58.362453+00	2014-04-16 15:26:58.362453+00	2	2014-04-16 15:26:58.353125+00	\N	\N	t		 			2014-04-16	2014-04-16			
12		1		-10	\N	  : root	t	2014-04-16 15:26:58.376434+00	2014-04-16 15:26:58.376434+00	2	2014-04-16 15:26:58.366224+00	\N	\N	t		 			2014-04-16	2014-04-16			
13		1		-11	\N	  : ashsemien	t	2014-04-16 15:26:58.391112+00	2014-04-16 15:26:58.391112+00	2	2014-04-16 15:26:58.380101+00	\N	\N	t		 			2014-04-16	2014-04-16			
14		1		-12	\N	  : srj9	t	2014-04-16 15:26:58.406787+00	2014-04-16 15:26:58.406787+00	2	2014-04-16 15:26:58.394649+00	\N	\N	t		 			2014-04-16	2014-04-16			
15		1		-13	\N	  : valentinedwv	t	2014-04-16 15:26:58.423304+00	2014-04-16 15:26:58.423304+00	2	2014-04-16 15:26:58.410441+00	\N	\N	t		 			2014-04-16	2014-04-16			
16		1		-14	\N	  : platosken	t	2014-04-16 15:26:58.446854+00	2014-04-16 15:26:58.446854+00	2	2014-04-16 15:26:58.427005+00	\N	\N	t		 			2014-04-16	2014-04-16			
17		1		-15	\N	  : shaunjl	t	2014-04-16 15:26:58.46931+00	2014-04-16 15:26:58.46931+00	2	2014-04-16 15:26:58.452709+00	\N	\N	t		 			2014-04-16	2014-04-16			
18		1		-16	\N	  : jamy	t	2014-04-16 15:26:58.489126+00	2014-04-16 15:26:58.489126+00	2	2014-04-16 15:26:58.473509+00	\N	\N	t		 			2014-04-16	2014-04-16			
1		1	Jefferson Heard	jefferson-heard		Jefferson Heard : th	t	2014-04-16 15:21:13.085333+00	2014-06-04 15:19:54.997605+00	2	2014-04-16 15:21:13+00	\N		t	JH	Jefferson Heard			2014-04-16	2014-06-04	Jefferson	Heard	
\.


--
-- Name: hs_scholar_profile_person_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_person_id_seq', 18, true);


--
-- Data for Name: hs_scholar_profile_personemail; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_personemail (id, phone_number, phone_type, person_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_personemail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_personemail_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_personlocation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_personlocation (id, address, address_type, person_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_personlocation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_personlocation_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_personphone; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_personphone (id, phone_number, phone_type, person_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_personphone_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_personphone_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_region; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_region (id, name, "geonamesUrl") FROM stdin;
\.


--
-- Name: hs_scholar_profile_region_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_region_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_scholar; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_scholar (person_ptr_id, user_id, demographics_id) FROM stdin;
2	1	\N
3	9	\N
4	4	\N
5	6	\N
6	3	\N
7	12	\N
8	5	\N
10	8	\N
11	7	\N
12	14	\N
13	15	\N
14	17	\N
15	13	\N
16	16	\N
17	11	\N
18	10	\N
1	2	\N
\.


--
-- Data for Name: hs_scholar_profile_scholarexternalidentifiers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_scholarexternalidentifiers (externalidentifiers_ptr_id, scholar_id) FROM stdin;
\.


--
-- Data for Name: hs_scholar_profile_scholargroup; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_scholargroup (group_ptr_id, keywords_string, site_id, title, slug, _meta_title, description, gen_description, created, updated, status, publish_date, expiry_date, short_url, in_sitemap, "groupDescription", purpose, "createdDate", "createdBy_id") FROM stdin;
\.


--
-- Data for Name: hs_scholar_profile_userdemographics; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_userdemographics (id, public, "userType", city_id, region_id, country_id) FROM stdin;
\.


--
-- Name: hs_scholar_profile_userdemographics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_userdemographics_id_seq', 1, false);


--
-- Data for Name: hs_scholar_profile_userkeywords; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_scholar_profile_userkeywords (id, person_id, keyword, "createdDate") FROM stdin;
\.


--
-- Name: hs_scholar_profile_userkeywords_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_scholar_profile_userkeywords_id_seq', 1, false);


--
-- Data for Name: pages_link; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY pages_link (page_ptr_id) FROM stdin;
\.


--
-- Data for Name: pages_page; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY pages_page (status, _order, parent_id, description, title, short_url, login_required, id, expiry_date, publish_date, titles, content_model, slug, keywords_string, site_id, gen_description, in_menus, _meta_title, in_sitemap, created, updated) FROM stdin;
2	1	\N	Resources	Resources	\N	f	17	\N	2014-04-16 15:21:43+00	Resources	catalogpage	resources		1	t			t	2014-04-16 15:21:43.58223+00	2014-04-29 19:03:05.139134+00
2	2	\N	hjkl	Resources	\N	f	19	\N	2014-04-29 19:01:32+00	Resources	richtextpage	my-resources		1	t	1,2,3		t	2014-04-29 19:01:32.780162+00	2014-07-18 18:04:31.804582+00
2	10	\N	HydroShare Statement of Privacy \nLast modified July 7, 2013	Statement of Privacy	\N	f	27	\N	2014-05-07 17:28:04+00	Statement of Privacy	richtextpage	privacy		1	t			t	2014-05-07 17:28:04.061384+00	2014-06-09 19:16:27.220663+00
2	9	\N	HydroShare Terms of Use\nLast modified July 7, 2013	Terms of Use	\N	f	26	\N	2014-05-07 17:27:32+00	Terms of Use	richtextpage	terms-of-use		1	t			t	2014-05-07 17:27:32.928522+00	2014-06-09 19:16:48.480425+00
2	6	\N	Thank you for signing up for HydroShare! We have sent you an email from hydroshare.org to verify your account.  Please click on the link within the email and verify your account with us and you can get started sharing data and models with HydroShare.	Verify account	\N	f	23	\N	2014-05-05 19:40:28+00	Verify account	richtextpage	verify-account		1	t			t	2014-05-05 19:40:28.558853+00	2014-05-05 19:47:25.082752+00
2	7	\N	Please give us your email address and we will resend the confirmation	Resend Verification Email	\N	f	24	\N	2014-05-05 19:51:29.969921+00	Resend Verification Email	form	resend-verification-email		1	t			t	2014-05-05 19:51:29.971722+00	2014-05-05 19:51:29.971722+00
2	5	\N	This page is under construction	Support	\N	f	22	\N	2014-04-29 19:02:56+00	Support	richtextpage	help		1	t	1,2,3		t	2014-04-29 19:02:56.717975+00	2014-06-02 18:03:55.848268+00
2	8	\N	jkl;	Create Resource	\N	t	25	\N	2014-05-07 15:16:21.597138+00	Create Resource	richtextpage	create-resource		1	t			t	2014-05-07 15:16:21.598682+00	2014-05-07 15:16:21.598682+00
2	12	\N	share resource	Share resource	\N	f	29	\N	2014-06-02 18:08:59.906453+00	Share resource	richtextpage	share-resource		1	t			t	2014-06-02 18:08:59.931029+00	2014-06-02 18:08:59.931029+00
2	11	\N	hjkl	Resource landing	\N	f	28	\N	2014-06-02 18:07:38+00	Resource landing	richtextpage	resourcelanding		1	t			t	2014-06-02 18:07:38.184936+00	2014-06-02 18:09:05.842892+00
2	0	\N	Hydroshare is an online collaboration environment for sharing data, models, and code.  Join the community to start sharing.	Home	\N	f	6	\N	2014-03-05 16:16:07+00	Home	homepage	/		1	t			t	2014-03-05 16:16:07.848726+00	2014-08-03 20:16:24.927108+00
2	3	\N	This page is slated for release 2	Explore	\N	f	20	\N	2014-04-29 19:02:27+00	Explore	richtextpage	explore		1	t			t	2014-04-29 19:02:27.56175+00	2014-06-11 12:34:11.658582+00
2	4	\N	hjkl	Collaborate	\N	f	21	\N	2014-04-29 19:02:40+00	Collaborate	richtextpage	collaborate		1	t			t	2014-04-29 19:02:40.289254+00	2014-06-11 12:34:19.706092+00
2	0	17	Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?	Generic Resource Test	\N	f	18	\N	2014-04-16 15:24:10+00	Resources / Generic Resource Test	genericresource	resources/generic-resource-test	generic resources csv	1	t	1,2,3		t	2014-04-16 15:24:10.827227+00	2014-06-11 17:35:46.571788+00
2	14	\N	Computer models are widely used in hydrology and water resources management. A large variety of models exist, each tailored to address specific challenges related to hydrologic science and water resources management. When scientists and engineers apply one of these models to address a specific question, they must devote significant effort to set up, calibrate, and evaluate that model instance built for some place and time. In many cases, there is a benefit to sharing these computer models and associated datasets with the broader scientific community. Core to model reuse in any context is metadata describing the model. A standardized metadata framework applicable across models will foster interoperability and encourage reuse and sharing of existing resources. This paper reports on the development of a metadata framework for describing water models. We discuss steps taken to achieve this goal for the HydroShare system and within the context of a use case that describes a team-based hydrologic modeling project.\r	Text and figures for our iEMSs paper titled 'Metadata for Describing Water Models'	\N	f	37	\N	2014-06-11 17:12:11.368122+00	Text and figures for our iEMSs paper titled 'Metadata for Describing Water Models'	genericresource	text-and-figures-for-our-iemss-paper-titled-metadata-for-describing-water-models	Model Metadata	1	t		\N	t	2014-06-11 17:12:11.369766+00	2014-06-11 17:30:48.130381+00
2	15	\N	This data was gathered for the purpose of monitoring gain of water flow due to river restoration efforts	Provo River Water Flow 2009-12-12 to 2010-12-15	\N	f	38	\N	2014-06-11 17:31:48.845512+00	Provo River Water Flow 2009-12-12 to 2010-12-15	genericresource	provo-river-water-flow-2009-12-12-to-2010-12-15	restoration provo river	1	t		\N	t	2014-06-11 17:31:48.8472+00	2014-06-11 17:31:48.898211+00
2	23	\N	Test	Test resource-1 by PK	\N	f	48	\N	2014-07-18 22:06:18+00	Test resource-1 by PK	genericresource	test-resource-1-by-pk		1	t			t	2014-07-18 22:06:18.388064+00	2014-07-21 15:29:55.461353+00
2	18	\N	This resource contains water temperature observations in the Little Bear River at Mendon Road near Mendon, Utah, USA	Water Temperature in the Little Bear River at Mendon Road	\N	f	42	\N	2014-06-14 22:47:25.974212+00	Water Temperature in the Little Bear River at Mendon Road	genericresource	water-temperature-in-the-little-bear-river-at-mendon-road	Temperature Water Little Bear River Utah Water Quality	1	t		\N	t	2014-06-14 22:47:25.975798+00	2014-06-14 22:58:19.293597+00
2	15	\N	Provo river water flow measurements taken before and during river restoration efforts	Provo River Water Flow 2009-12-12 to 2010-12-15	\N	f	39	\N	2014-06-11 18:53:30.009644+00	Provo River Water Flow 2009-12-12 to 2010-12-15	genericresource	provo-river-water-flow-2009-12-12-to-2010-12-15-1	provo river	1	t		\N	t	2014-06-11 18:53:30.012053+00	2014-06-11 18:58:11.09853+00
2	16	\N	calibrated EPA-SWMM model for Rocky Branch watershed, Columbia, SC	EPA-SWMM model 	\N	f	40	\N	2014-06-12 13:20:19.716174+00	EPA-SWMM model 	genericresource	epa-swmm-model	EPA-SWMM model	1	t		\N	t	2014-06-12 13:20:19.717702+00	2014-06-12 13:20:19.76754+00
2	17	\N	A CSDMS Web Modeling Tool model run of the HydroTrend component with default model parameters.	HydroTrend - Run 1	\N	f	41	\N	2014-06-13 19:08:43.912725+00	HydroTrend - Run 1	genericresource	hydrotrend-run-1	CSDMS WMT HydroTrend	1	t		\N	t	2014-06-13 19:08:43.919745+00	2014-06-13 19:08:44.091329+00
2	31	\N	3. Test resource shared with dtarb	3. Test resource shared with dtarb	\N	f	56	\N	2014-07-20 13:17:15+00	3. Test resource shared with dtarb	genericresource	test-resource-shared-with-dtarb		1	t			t	2014-07-20 13:17:15.882149+00	2014-07-20 13:34:34.048555+00
2	27	\N	2. Test resource public dtarb	2. Test resource public dtarb	\N	f	52	\N	2014-07-20 12:57:43+00	2. Test resource public dtarb	genericresource	test-resource-public-dtarb		1	t			t	2014-07-20 12:57:43.597399+00	2014-07-20 13:35:20.196797+00
2	28	\N	4. Test resource shared with davidG	4. Test resource shared with davidG	\N	f	53	\N	2014-07-20 12:59:07+00	4. Test resource shared with davidG	genericresource	test-resource-shared-with-davidg		1	t			t	2014-07-20 12:59:07.347394+00	2014-07-20 13:36:07.991289+00
2	29	\N	5. test resource shared with david G view	5. test resource shared with david G view	\N	f	54	\N	2014-07-20 13:02:01+00	5. test resource shared with david G view	genericresource	test-resource-shared-with-david-g-view		1	t			t	2014-07-20 13:02:01.421387+00	2014-07-20 13:37:35.799437+00
2	32	\N	This is a test	Example Instance XML	\N	f	57	\N	2014-08-01 18:19:15.720644+00	Example Instance XML	genericresource	example-instance-xml	xml waterml	1	t		\N	t	2014-08-01 18:19:15.925066+00	2014-08-01 18:20:03.18949+00
2	22	\N	Peuker Douglas DEM	Peuker Douglas DEM	\N	f	47	\N	2014-07-18 18:49:16.78139+00	Peuker Douglas DEM	genericresource	peuker-douglas-dem		1	t		\N	t	2014-07-18 18:49:16.782872+00	2014-07-18 18:49:16.782872+00
2	20	\N	Torrent	Torrent	\N	f	45	\N	2014-07-18 17:59:50.333099+00	Torrent	genericresource	torrent-1		1	t		\N	t	2014-07-18 17:59:50.336708+00	2014-07-18 22:42:40.454151+00
2	24	\N	Test	Test	\N	f	49	\N	2014-07-18 22:43:29.405889+00	Test	genericresource	test		1	t		\N	t	2014-07-18 22:43:29.40739+00	2014-07-18 22:43:40.512075+00
2	25	\N	Test-2	Test resource-2 by PK	\N	f	50	\N	2014-07-18 23:53:51.334557+00	Test resource-2 by PK	genericresource	test-resource-2-by-pk		1	t		\N	t	2014-07-18 23:53:51.336229+00	2014-07-18 23:53:51.336229+00
2	26	\N	Test	Sample res-1 by Tester-1	\N	f	51	\N	2014-07-19 00:00:34.447568+00	Sample res-1 by Tester-1	genericresource	sample-res-1-by-tester-1		1	t		\N	t	2014-07-19 00:00:34.449123+00	2014-07-19 00:00:34.449123+00
2	21	\N	Tiff File for unknown location	Tiff File for unknown location	\N	f	46	\N	2014-07-18 18:33:01.972936+00	Tiff File for unknown location	genericresource	tiff-file-for-unknown-location		1	t		\N	t	2014-07-18 18:33:01.975064+00	2014-07-19 00:17:37.242501+00
2	19	\N	Torrent	Torrent	\N	f	44	\N	2014-07-18 17:52:44.547553+00	Torrent	genericresource	torrent		1	t		\N	t	2014-07-18 17:52:44.560677+00	2014-07-23 14:30:35.713684+00
2	33	\N	blah, blah, cannot spell blah	Test - push files in github	\N	f	58	\N	2014-08-26 18:51:19.414687+00	Test - push files in github	genericresource	test-push-files-in-github		1	t		\N	t	2014-08-26 18:51:19.434524+00	2014-08-26 18:51:19.446543+00
2	30	\N	1. Test resource public davidg	1. Test resource public davidg	\N	f	55	\N	2014-07-20 13:11:46+00	1. Test resource public davidg	genericresource	test-resource-public-davidg		1	t			t	2014-07-20 13:11:46.924359+00	2014-07-26 04:07:48.754278+00
\.


--
-- Name: pages_page_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('pages_page_id_seq', 58, true);


--
-- Data for Name: pages_richtextpage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY pages_richtextpage (content, page_ptr_id) FROM stdin;
<p>Thank you for signing up for HydroShare! We have sent you an email from hydroshare.org to verify your account.  Please click on the link within the email and verify your account with us and you can get started sharing data and models with HydroShare.</p>\n<p><a href="/hsapi/_internal/resend_verification_email/">Please click here if you do not receive a verification email within 1 hour.</a></p>	23
<p>jkl;</p>	25
<p>This page is under construction</p>	22
<p>share resource</p>	29
<p>hjkl</p>	28
<h1><b>HydroShare Statement of Privacy </b></h1>\n<p><em>Last modified July 7, 2013</em></p>\n<p>HydroShare is operated by a team of researchers associated with the Consortium of Universities for the Advancement of Hydrologic Science, Inc. and funded by the National Science Foundation.  The services are hosted at participating institutions including the Renaissance Computing Institute at University of North Carolina, Utah State University, Brigham Young University, Tufts, University of Virginia, University of California at San Diego, University of Texas, Purdue and CUAHSI.  In the following these are referred to as participating institutions.</p>\n<p>We respect your privacy. We will only use your personal identification information to support and manage your use of hydroshare.org, including the use of tracking cookies to facilitate hydroshare.org security procedures. The HydroShare participating institutions and the National Science Foundation (which funds hydroshare.org development) regularly request hydroshare.org usages statistics and other information. Usage of hydroshare.org is monitored and usage statistics are collected and reported on a regular basis. Hydroshare.org also reserves the right to contact you to request additional information or to keep you updated on changes to Hydroshare.org. You may opt out of receiving newsletters and other non-essential communications. No information that would identify you personally will be provided to sponsors or third parties without your permission.</p>\n<p>While HydroShare uses policies and procedures to manage the access to content according to the access control settings set by users all information posted or stored on hydroshare.org is potentially available to other users of hydroshare.org and the public. The HydroShare participating institutions and hydroshare.org disclaim any responsibility for the preservation of confidentiality of such information. <i>Do not post or store information on hydroshare.org if you expect to or are obligated to protect the confidentiality of that information.</i></p>	27
<h1>HydroShare Terms of Use</h1>\n<p><em>Last modified July 7, 2013</em></p>\n<p>Thank you for using the HydroShare hydrologic data sharing system hosted at hydroshare.org.  HydroShare services are provided by a team of researchers associated with the Consortium of Universities for the Advancement of Hydrologic Science, Inc. and funded by the National Science Foundation.  The services are hosted at participating institutions including the Renaissance Computing Institute at University of North Carolina, Utah State University, Brigham Young University, Tufts, University of Virginia, University of California at San Diego, University of Texas, Purdue and CUAHSI. Your access to hydroshare.org is subject to your agreement to these Terms of Use. By using our services at hydroshare.org, you are agreeing to these terms.  Please read them carefully.</p>\n<h2><b>Modification of the Agreement</b></h2>\n<p>We maintain the right to modify these Terms of Use and may do so by posting modifications on this page. Any modification is effective immediately upon posting the modification unless otherwise stated. Your continued use of hydroshare.org following the posting of any modification signifies your acceptance of that modification. You should regularly visit this page to review the current Terms of Use.</p>\n<h2><b>Conduct Using our Services</b></h2>\n<p>The hydroshare.org site is intended to support data and model sharing in hydrology.  This is broadly interpreted to include any discipline or endeavor that has something to do with water.  You are responsible at all times for using hydroshare.org in a manner that is legal, ethical, and not to the detriment of others and for purposes related to hydrology. You agree that you will not in your use of hydroshare.org:</p>\n<ul>\n<li>Violate any applicable law, commit a criminal offense or perform actions that might encourage others to commit a criminal offense or give rise to a civil liability;</li>\n<li>Post or transmit any unlawful, threatening, libelous, harassing, defamatory, vulgar, obscene, pornographic, profane, or otherwise objectionable content;</li>\n<li>Use hydroshare.org to impersonate other parties or entities;</li>\n<li>Use hydroshare.org to upload any content that contains a software virus, "Trojan Horse" or any other computer code, files, or programs that may alter, damage, or interrupt the functionality of hydroshare.org or the hardware or software of any other person who accesses hydroshare.org;</li>\n<li>Upload, post, email, or otherwise transmit any materials that you do not have a right to transmit under any law or under a contractual relationship;</li>\n<li>Alter, damage, or delete any content posted on hydroshare.org, except where such alterations or deletions are consistent with the access control settings of that content in hydroshare.org;</li>\n<li>Disrupt the normal flow of communication in any way;</li>\n<li>Claim a relationship with or speak for any business, association, or other organization for which you are not authorized to claim such a relationship;</li>\n<li>Post or transmit any unsolicited advertising, promotional materials, or other forms of solicitation;</li>\n<li>Post any material that infringes or violates the intellectual property rights of another.</li>\n</ul>\n<p>Certain portions of hydroshare.org are limited to registered users and/or allow a user to participate in online services by entering personal information. You agree that any information provided to hydroshare.org in these areas will be complete and accurate, and that you will neither register under the name of nor attempt to enter hydroshare.org under the name of another person or entity.</p>\n<p>You are responsible for maintaining the confidentiality of your user ID and password, if any, and for restricting access to your computer, and you agree to accept responsibility for all activities that occur under your account or password. Hydroshare.org does not authorize use of your User ID by third-parties.</p>\n<p>We may, in our sole discretion, terminate or suspend your access to and use of hydroshare.org without notice and for any reason, including for violation of these Terms of Use or for other conduct that we, in our sole discretion, believe to be unlawful or harmful to others. In the event of termination, you are no longer authorized to access hydroshare.org.</p>\n<h2><b>Disclaimers</b></h2>\n<p>HYDROSHARE AND ANY INFORMATION, PRODUCTS OR SERVICES ON IT ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. Hydroshare.org and its participating institutions do not warrant, and hereby disclaim any warranties, either express or implied, with respect to the accuracy, adequacy or completeness of any good, service, or information obtained from hydroshare.org. Hydroshare.org and its participating institutions do not warrant that Hydroshare.org will operate in an uninterrupted or error-free manner or that hydroshare.org is free of viruses or other harmful components. Use of hydroshare.org is at your own risk.</p>\n<p>You agree that hydroshare.org and its participating institutions shall have no liability for any consequential, indirect, punitive, special or incidental damages, whether foreseeable or unforeseeable (including, but not limited to, claims for defamation, errors, loss of data, or interruption in availability of data), arising out of or relating to your use of water-hub.org or any resource that you access through hydroshare.org.</p>\n<p>The hydroshare.org site hosts content from a number of authors. The statements and views of these authors are theirs alone, and do not reflect the stances or policies of the HydroShare research team or their sponsors, nor does their posting imply the endorsement of HydroShare or their sponsors.</p>\n<h2><b>Choice of Law/Forum Selection/Attorney Fees</b></h2>\n<p>You agree that any dispute arising out of or relating to hydroshare.org, whether based in contract, tort, statutory or other law, will be governed by federal law and by the laws of North Carolina, excluding its conflicts of law provisions. You further consent to the personal jurisdiction of and exclusive venue in the federal and state courts located in and serving the United States of America, North Carolina as the exclusive legal forums for any such dispute.</p>	26
<p>This page is slated for release 2</p>	20
<p>hjkl</p>	21
<p>hjkl</p>	19
\.


--
-- Data for Name: south_migrationhistory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY south_migrationhistory (id, app_name, migration, applied) FROM stdin;
1	conf	0001_initial	2014-02-04 14:52:00.511148+00
2	conf	0002_auto__add_field_setting_site	2014-02-04 14:52:00.537373+00
3	conf	0003_update_site_setting	2014-02-04 14:52:00.547859+00
4	conf	0004_ssl_account_settings_rename	2014-02-04 14:52:00.554576+00
5	core	0001_initial	2014-02-04 14:52:00.608024+00
6	pages	0001_initial	2014-02-04 14:52:00.701586+00
7	pages	0002_auto__del_field_page__keywords__add_field_page_keywords_string__chg_fi	2014-02-04 14:52:00.747451+00
8	blog	0001_initial	2014-02-04 14:52:00.85044+00
9	blog	0002_auto	2014-02-04 14:52:00.895957+00
10	blog	0003_categories	2014-02-04 14:52:00.914132+00
11	blog	0004_auto__del_field_blogpost_category	2014-02-04 14:52:00.932242+00
12	blog	0005_auto__del_comment__add_field_blogpost_comments_count__chg_field_blogpo	2014-02-04 14:52:00.982201+00
13	blog	0006_auto__del_field_blogpost__keywords__add_field_blogpost_keywords_string	2014-02-04 14:52:01.023672+00
14	core	0002_auto__del_keyword	2014-02-04 14:52:01.028807+00
15	core	0003_auto__add_sitepermission	2014-02-04 14:52:01.119037+00
16	core	0004_set_site_permissions	2014-02-04 14:52:01.131539+00
17	core	0005_auto__chg_field_sitepermission_user__del_unique_sitepermission_user	2014-02-04 14:52:01.195867+00
18	generic	0001_initial	2014-02-04 14:52:01.289041+00
19	generic	0002_auto__add_keyword__add_assignedkeyword	2014-02-04 14:52:01.338783+00
20	generic	0003_auto__add_rating	2014-02-04 14:52:01.377393+00
21	generic	0004_auto__chg_field_rating_object_pk__chg_field_assignedkeyword_object_pk	2014-02-04 14:52:01.416053+00
22	generic	0005_keyword_site	2014-02-04 14:52:01.44924+00
23	generic	0006_move_keywords	2014-02-04 14:52:01.469633+00
24	generic	0007_auto__add_field_assignedkeyword__order	2014-02-04 14:52:01.486981+00
25	generic	0008_set_keyword_order	2014-02-04 14:52:01.504656+00
26	generic	0009_auto__chg_field_keyword_title__chg_field_keyword_slug	2014-02-04 14:52:01.557798+00
27	generic	0009_auto__del_field_threadedcomment_email_hash	2014-02-04 14:52:01.578805+00
28	generic	0010_auto__chg_field_keyword_slug__chg_field_keyword_title	2014-02-04 14:52:01.622661+00
29	generic	0011_auto__add_field_threadedcomment_rating_count__add_field_threadedcommen	2014-02-04 14:52:01.670726+00
30	generic	0012_auto__add_field_rating_rating_date	2014-02-04 14:52:01.691022+00
31	generic	0013_auto__add_field_threadedcomment_rating_sum	2014-02-04 14:52:01.730808+00
32	generic	0014_auto__add_field_rating_user	2014-02-04 14:52:01.762666+00
33	blog	0007_auto__add_field_blogpost_site	2014-02-04 14:52:01.877031+00
34	blog	0008_auto__add_field_blogpost_rating_average__add_field_blogpost_rating_cou	2014-02-04 14:52:01.965313+00
35	blog	0009_auto__chg_field_blogpost_content	2014-02-04 14:52:02.005672+00
36	blog	0010_category_site_allow_comments	2014-02-04 14:52:02.070249+00
37	blog	0011_comment_site_data	2014-02-04 14:52:02.097641+00
38	blog	0012_auto__add_field_blogpost_featured_image	2014-02-04 14:52:02.122403+00
39	blog	0013_auto__chg_field_blogpost_featured_image	2014-02-04 14:52:02.162531+00
40	blog	0014_auto__add_field_blogpost_gen_description	2014-02-04 14:52:02.198521+00
41	blog	0015_auto__chg_field_blogcategory_title__chg_field_blogcategory_slug__chg_f	2014-02-04 14:52:02.289484+00
42	blog	0016_add_field_blogpost__meta_title	2014-02-04 14:52:02.313672+00
43	blog	0017_add_field_blogpost__related_posts	2014-02-04 14:52:02.366448+00
44	blog	0018_auto__add_field_blogpost_in_sitemap	2014-02-04 14:52:02.467502+00
45	blog	0019_auto__add_field_blogpost_rating_sum	2014-02-04 14:52:02.507725+00
46	blog	0020_auto__add_field_blogpost_created__add_field_blogpost_updated	2014-02-04 14:52:02.534471+00
47	forms	0001_initial	2014-02-04 14:52:02.720705+00
48	forms	0002_auto__add_field_field_placeholder_text	2014-02-04 14:52:02.750401+00
49	forms	0003_auto__chg_field_field_field_type	2014-02-04 14:52:02.784442+00
50	forms	0004_auto__chg_field_form_response__chg_field_form_content	2014-02-04 14:52:02.828912+00
51	forms	0005_auto__chg_field_fieldentry_value	2014-02-04 14:52:02.858265+00
52	pages	0003_auto__add_field_page_site	2014-02-04 14:52:02.953195+00
53	pages	0004_auto__del_contentpage__add_richtextpage	2014-02-04 14:52:02.966807+00
54	pages	0005_rename_contentpage	2014-02-04 14:52:02.977482+00
55	pages	0006_auto__add_field_page_gen_description	2014-02-04 14:52:03.011007+00
56	pages	0007_auto__chg_field_page_slug__chg_field_page_title	2014-02-04 14:52:03.056516+00
57	pages	0008_auto__add_link	2014-02-04 14:52:03.079694+00
58	pages	0009_add_field_page_in_menus	2014-02-04 14:52:03.116507+00
59	pages	0010_set_menus	2014-02-04 14:52:03.130399+00
60	pages	0011_delete_nav_flags	2014-02-04 14:52:03.143167+00
61	pages	0012_add_field_page__meta_title	2014-02-04 14:52:03.156269+00
62	pages	0013_auto__add_field_page_in_sitemap	2014-02-04 14:52:03.189639+00
63	pages	0014_auto__add_field_page_created__add_field_page_updated	2014-02-04 14:52:03.209679+00
64	galleries	0001_initial	2014-02-04 14:52:03.284181+00
66	django_extensions	0001_empty	2014-02-04 14:52:03.471041+00
67	djcelery	0001_initial	2014-02-04 14:52:03.774918+00
68	djcelery	0002_v25_changes	2014-02-04 14:52:03.865873+00
69	djcelery	0003_v26_changes	2014-02-04 14:52:03.896836+00
70	djcelery	0004_v30_changes	2014-02-04 14:52:03.919242+00
71	ga_resources	0001_initial	2014-02-04 14:52:04.186204+00
72	tastypie	0001_initial	2014-02-04 14:52:04.278957+00
73	tastypie	0002_add_apikey_index	2014-02-04 14:52:04.296604+00
75	dublincore	0001_initial	2014-02-26 15:45:18.64828+00
76	theme	0001_initial	2014-03-05 16:06:42.534048+00
77	blog_mods	0001_initial	2014-03-05 16:21:54.278652+00
88	hs_core	0001_initial	2014-04-16 15:18:27.812924+00
89	hs_core	0002_auto__add_field_genericresource_comments_count	2014-04-16 15:18:27.842061+00
90	hs_core	0003_auto	2014-04-16 15:18:27.922464+00
91	hs_core	0004_auto__add_resourcefile__del_field_genericresource_resource_file__del_f	2014-04-16 15:18:27.985661+00
92	hs_core	0005_auto__add_field_resourcefile_short_id	2014-04-16 15:18:28.008296+00
93	hs_core	0006_auto__del_field_resourcefile_short_id	2014-04-16 15:18:28.027463+00
94	hs_core	0007_auto__add_groupownership	2014-04-16 15:18:28.058919+00
95	hs_core	0008_auto__add_bags	2014-04-16 15:18:28.13897+00
96	hs_core	0009_auto__del_field_bags_path__add_field_bags_bag	2014-04-16 15:18:28.161103+00
97	hs_core	0010_auto__add_field_genericresource_doi	2014-04-16 15:18:28.187103+00
98	hs_scholar_profile	0001_initial	2014-04-16 15:18:44.477411+00
99	theme	0002_auto__add_userprofile	2014-06-09 03:22:10.642097+00
100	theme	0003_auto__add_field_userprofile_public	2014-06-09 03:46:05.875643+00
101	theme	0004_auto__add_field_userprofile_picture	2014-06-09 13:33:15.54643+00
102	theme	0005_auto__add_field_userprofile_cv__add_field_userprofile_details	2014-06-09 13:40:10.073603+00
103	hs_core	0011_auto__add_publisher__add_unique_publisher_content_type_object_id__add_	2014-08-21 15:13:53.90893+00
104	hs_core	0012_auto__chg_field_contributor_description__chg_field_contributor_researc	2014-08-26 18:47:01.01813+00
\.


--
-- Name: south_migrationhistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('south_migrationhistory_id_seq', 104, true);


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: tastypie_apiaccess; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY tastypie_apiaccess (id, identifier, url, request_method, accessed) FROM stdin;
\.


--
-- Name: tastypie_apiaccess_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('tastypie_apiaccess_id_seq', 1, false);


--
-- Data for Name: tastypie_apikey; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY tastypie_apikey (id, user_id, key, created) FROM stdin;
10	30	f74d2605510767c28d3abccf46aa5b69b13f0137	2014-06-11 17:14:02.638205+00
11	31	bc2e0952a0b38309d8f01f0bb88301d5800bd2c6	2014-06-11 17:36:01.009698+00
12	32	fe1cf331f02dee472e06763d627f7e6687761113	2014-06-11 18:04:42.272358+00
13	34	5bdff9b9bfc4034b7575e170812961264c56ec00	2014-06-18 16:14:37.13632+00
14	35	5d922c662d8fe4ab6aaa904903418f0e016a38ef	2014-06-23 15:33:19.193757+00
15	37	fa70eebfc879d1858485ba01c373d38d8cfb5366	2014-07-18 18:44:59.442748+00
16	40	43d137a82d0a8b8801731740e09c1a170c4c1260	2014-08-26 18:50:03.788644+00
\.


--
-- Name: tastypie_apikey_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('tastypie_apikey_id_seq', 16, true);


--
-- Data for Name: theme_homepage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY theme_homepage (page_ptr_id, heading, slide_in_one_icon, slide_in_one, slide_in_two_icon, slide_in_two, slide_in_three_icon, slide_in_three, header_background, header_image, welcome_heading, content, recent_blog_heading, number_recent_posts) FROM stdin;
6	Hydroshare							uploads/homepage/3913787974_7c36d03071_o.jpg	uploads/homepage/3957229820_4ac8c463aa_b.jpg	Share and Collaborate	<p>Hydroshare is an online collaboration environment for sharing data, models, and code.  Join the community to start sharing.</p>	Latest blog posts	3
\.


--
-- Data for Name: theme_iconbox; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY theme_iconbox (id, _order, homepage_id, icon, title, link_text, link) FROM stdin;
\.


--
-- Name: theme_iconbox_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('theme_iconbox_id_seq', 1, false);


--
-- Data for Name: theme_siteconfiguration; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY theme_siteconfiguration (id, site_id, col1_heading, col1_content, col2_heading, col2_content, col3_heading, col3_content, twitter_link, facebook_link, pinterest_link, youtube_link, github_link, linkedin_link, vk_link, gplus_link, has_social_network_links, copyright) FROM stdin;
1	1	Contact us	<p><a href="mailto:hydroshare@hydroshare.org">Email us at hydroshare.org</a></p>	Go social		Open Source	<p>HydroShare is Open Source. <a href="https://github.com/hydroshare/" target="_blank">Find us on Github</a>.</p>\n<p><a href="https://github.com/hydroshare/hydroshare2/issues?state=open">Report a bug here. </a></p>	http://twitter.com/cuahsi 	https://www.facebook.com/pages/CUAHSI-Consortium-of-Universities-for-the-Advancement-of-Hydrologic-Science-Inc/179921902590		http://www.youtube.com/user/CUAHSI	http://github.com/hydroshare	https://www.linkedin.com/company/2632114			t	&copy {% now "Y" %} CUAHSI. This material is based upon work supported by the National Science Foundation (NSF) under awards 1148453 and 1148090.  Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.
\.


--
-- Name: theme_siteconfiguration_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('theme_siteconfiguration_id_seq', 1, true);


--
-- Data for Name: theme_userprofile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY theme_userprofile (id, user_id, title, profession, subject_areas, organization, organization_type, phone_1, phone_1_type, phone_2, phone_2_type, public, picture, cv, details) FROM stdin;
1	14	Senior Research Software Developer	Researcher	Computer Science, Geography	RENCI	Research	919-445-9639	Work	919-308-7536	Mobile	t	\N	\N	\N
2	2	Senior Research Software Developer	Researcher	Computer Science, Geography	RENCI	Research	919-445-9639	Work	919-308-7536	Mobile	t	profile/106392586_00864f4db8_q.jpg	profile/CV2.doc.pdf	<p>I am the chief software architect of Hydroshare.  I am a seasoned Open Source software developer and research scientist, focusing on visualization, geographic data management and visualization, and data mining.</p>\n<p>I have been at UNC and RENCI as a researcher for 7 years.</p>\n<p>I am the author of the <a href="https://github.com/JeffHeard/ga_resources">Geoanalytics Framework</a>, a CMS and visualization framework for geographic data, focusing on compatibility, large or unusual data, and scientific data management.</p>
5	7	\N	Researcher	\N	\N	\N	\N	\N	\N	\N	t			\N
6	11	\N	Researcher	\N	\N	\N	\N	\N	\N	\N	t			\N
12	3	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
15	29	Associate Professor	Faculty	Hydrology, Water Resources, Hydroinformatics	University of Virginia	Higher Education		\N		\N	t			
16	30	Student Programmer	Student	Physics, Hydrology	BYU	Higher Education	435-640-9365	Mobile		\N	t	profile/21.jpg		<p>I work on HydroShare as a programmer.</p>
17	17	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
18	31	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
19	32		Software Developer		RENCI	Research		\N		\N	t			
20	33	Graduate Research Assistant	Student	hydrology and water resources	University of Virginia	Higher Education	8034633555	Mobile		\N	t			
21	9	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
22	34	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
23	35	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
24	5		Research Faculty	Hydrology	Utah State University	\N		\N		\N	t			
25	10	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
26	13	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
27	12	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
28	37		Student			\N		\N		\N	t			
29	38		Student			\N	7012354043	\N	7012354043	\N	t			
30	39		Student			\N	7012354043	\N	7012354043	\N	t			
31	40	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
32	41		Student			\N	8012315581	\N	8012315581	\N	t			
\.


--
-- Name: theme_userprofile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('theme_userprofile_id_seq', 32, true);


--
-- Name: auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions_group_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission_content_type_id_codename_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_key UNIQUE (content_type_id, codename);


--
-- Name: auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: blog_blogcategory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY blog_blogcategory
    ADD CONSTRAINT blog_blogcategory_pkey PRIMARY KEY (id);


--
-- Name: blog_blogpost_categories_blogpost_id_79f2a5569187bd14_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY blog_blogpost_categories
    ADD CONSTRAINT blog_blogpost_categories_blogpost_id_79f2a5569187bd14_uniq UNIQUE (blogpost_id, blogcategory_id);


--
-- Name: blog_blogpost_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY blog_blogpost_categories
    ADD CONSTRAINT blog_blogpost_categories_pkey PRIMARY KEY (id);


--
-- Name: blog_blogpost_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY blog_blogpost
    ADD CONSTRAINT blog_blogpost_pkey PRIMARY KEY (id);


--
-- Name: blog_blogpost_related_po_from_blogpost_id_3007eb9b6b16df8b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY blog_blogpost_related_posts
    ADD CONSTRAINT blog_blogpost_related_po_from_blogpost_id_3007eb9b6b16df8b_uniq UNIQUE (from_blogpost_id, to_blogpost_id);


--
-- Name: blog_blogpost_related_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY blog_blogpost_related_posts
    ADD CONSTRAINT blog_blogpost_related_posts_pkey PRIMARY KEY (id);


--
-- Name: celery_taskmeta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY celery_taskmeta
    ADD CONSTRAINT celery_taskmeta_pkey PRIMARY KEY (id);


--
-- Name: celery_taskmeta_task_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY celery_taskmeta
    ADD CONSTRAINT celery_taskmeta_task_id_key UNIQUE (task_id);


--
-- Name: celery_tasksetmeta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY celery_tasksetmeta
    ADD CONSTRAINT celery_tasksetmeta_pkey PRIMARY KEY (id);


--
-- Name: celery_tasksetmeta_taskset_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY celery_tasksetmeta
    ADD CONSTRAINT celery_tasksetmeta_taskset_id_key UNIQUE (taskset_id);


--
-- Name: conf_setting_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY conf_setting
    ADD CONSTRAINT conf_setting_pkey PRIMARY KEY (id);


--
-- Name: core_sitepermission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY core_sitepermission
    ADD CONSTRAINT core_sitepermission_pkey PRIMARY KEY (id);


--
-- Name: core_sitepermission_sit_sitepermission_id_31fc3b7b7e3badd5_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY core_sitepermission_sites
    ADD CONSTRAINT core_sitepermission_sit_sitepermission_id_31fc3b7b7e3badd5_uniq UNIQUE (sitepermission_id, site_id);


--
-- Name: core_sitepermission_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY core_sitepermission_sites
    ADD CONSTRAINT core_sitepermission_sites_pkey PRIMARY KEY (id);


--
-- Name: core_sitepermission_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY core_sitepermission
    ADD CONSTRAINT core_sitepermission_user_id_key UNIQUE (user_id);


--
-- Name: django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_comment_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_comment_flags
    ADD CONSTRAINT django_comment_flags_pkey PRIMARY KEY (id);


--
-- Name: django_comment_flags_user_id_comment_id_flag_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_comment_flags
    ADD CONSTRAINT django_comment_flags_user_id_comment_id_flag_key UNIQUE (user_id, comment_id, flag);


--
-- Name: django_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_comments
    ADD CONSTRAINT django_comments_pkey PRIMARY KEY (id);


--
-- Name: django_content_type_app_label_model_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_key UNIQUE (app_label, model);


--
-- Name: django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_irods_rodsenvironment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_irods_rodsenvironment
    ADD CONSTRAINT django_irods_rodsenvironment_pkey PRIMARY KEY (id);


--
-- Name: django_redirect_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_redirect
    ADD CONSTRAINT django_redirect_pkey PRIMARY KEY (id);


--
-- Name: django_redirect_site_id_old_path_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_redirect
    ADD CONSTRAINT django_redirect_site_id_old_path_key UNIQUE (site_id, old_path);


--
-- Name: django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: django_site_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_site
    ADD CONSTRAINT django_site_pkey PRIMARY KEY (id);


--
-- Name: djcelery_crontabschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_crontabschedule
    ADD CONSTRAINT djcelery_crontabschedule_pkey PRIMARY KEY (id);


--
-- Name: djcelery_intervalschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_intervalschedule
    ADD CONSTRAINT djcelery_intervalschedule_pkey PRIMARY KEY (id);


--
-- Name: djcelery_periodictask_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_periodictask
    ADD CONSTRAINT djcelery_periodictask_name_key UNIQUE (name);


--
-- Name: djcelery_periodictask_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_periodictask
    ADD CONSTRAINT djcelery_periodictask_pkey PRIMARY KEY (id);


--
-- Name: djcelery_periodictasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_periodictasks
    ADD CONSTRAINT djcelery_periodictasks_pkey PRIMARY KEY (ident);


--
-- Name: djcelery_taskstate_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_taskstate
    ADD CONSTRAINT djcelery_taskstate_pkey PRIMARY KEY (id);


--
-- Name: djcelery_taskstate_task_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_taskstate
    ADD CONSTRAINT djcelery_taskstate_task_id_key UNIQUE (task_id);


--
-- Name: djcelery_workerstate_hostname_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_workerstate
    ADD CONSTRAINT djcelery_workerstate_hostname_key UNIQUE (hostname);


--
-- Name: djcelery_workerstate_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY djcelery_workerstate
    ADD CONSTRAINT djcelery_workerstate_pkey PRIMARY KEY (id);


--
-- Name: dublincore_qualifieddublincoreelement_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelement
    ADD CONSTRAINT dublincore_qualifieddublincoreelement_pkey PRIMARY KEY (id);


--
-- Name: dublincore_qualifieddublincoreelementhistory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelementhistory
    ADD CONSTRAINT dublincore_qualifieddublincoreelementhistory_pkey PRIMARY KEY (id);


--
-- Name: forms_field_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY forms_field
    ADD CONSTRAINT forms_field_pkey PRIMARY KEY (id);


--
-- Name: forms_fieldentry_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY forms_fieldentry
    ADD CONSTRAINT forms_fieldentry_pkey PRIMARY KEY (id);


--
-- Name: forms_form_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY forms_form
    ADD CONSTRAINT forms_form_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: forms_formentry_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY forms_formentry
    ADD CONSTRAINT forms_formentry_pkey PRIMARY KEY (id);


--
-- Name: ga_irods_rodsenvironment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_irods_rodsenvironment
    ADD CONSTRAINT ga_irods_rodsenvironment_pkey PRIMARY KEY (id);


--
-- Name: ga_resources_catalogpage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_catalogpage
    ADD CONSTRAINT ga_resources_catalogpage_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: ga_resources_dataresource_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_dataresource
    ADD CONSTRAINT ga_resources_dataresource_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: ga_resources_orderedresource_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_orderedresource
    ADD CONSTRAINT ga_resources_orderedresource_pkey PRIMARY KEY (id);


--
-- Name: ga_resources_relatedresource_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_relatedresource
    ADD CONSTRAINT ga_resources_relatedresource_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: ga_resources_renderedlay_renderedlayer_id_12fa6280828b775a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_renderedlayer_styles
    ADD CONSTRAINT ga_resources_renderedlay_renderedlayer_id_12fa6280828b775a_uniq UNIQUE (renderedlayer_id, style_id);


--
-- Name: ga_resources_renderedlayer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_renderedlayer
    ADD CONSTRAINT ga_resources_renderedlayer_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: ga_resources_renderedlayer_styles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_renderedlayer_styles
    ADD CONSTRAINT ga_resources_renderedlayer_styles_pkey PRIMARY KEY (id);


--
-- Name: ga_resources_resourcegroup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_resourcegroup
    ADD CONSTRAINT ga_resources_resourcegroup_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: ga_resources_style_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_resources_style
    ADD CONSTRAINT ga_resources_style_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: galleries_gallery_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY galleries_gallery
    ADD CONSTRAINT galleries_gallery_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: galleries_galleryimage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY galleries_galleryimage
    ADD CONSTRAINT galleries_galleryimage_pkey PRIMARY KEY (id);


--
-- Name: generic_assignedkeyword_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY generic_assignedkeyword
    ADD CONSTRAINT generic_assignedkeyword_pkey PRIMARY KEY (id);


--
-- Name: generic_keyword_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY generic_keyword
    ADD CONSTRAINT generic_keyword_pkey PRIMARY KEY (id);


--
-- Name: generic_rating_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY generic_rating
    ADD CONSTRAINT generic_rating_pkey PRIMARY KEY (id);


--
-- Name: generic_threadedcomment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY generic_threadedcomment
    ADD CONSTRAINT generic_threadedcomment_pkey PRIMARY KEY (comment_ptr_id);


--
-- Name: hs_core_bags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_bags
    ADD CONSTRAINT hs_core_bags_pkey PRIMARY KEY (id);


--
-- Name: hs_core_contributor_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_contributor
    ADD CONSTRAINT hs_core_contributor_pkey PRIMARY KEY (id);


--
-- Name: hs_core_coremetadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_coremetadata
    ADD CONSTRAINT hs_core_coremetadata_pkey PRIMARY KEY (id);


--
-- Name: hs_core_coverage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_coverage
    ADD CONSTRAINT hs_core_coverage_pkey PRIMARY KEY (id);


--
-- Name: hs_core_creator_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_creator
    ADD CONSTRAINT hs_core_creator_pkey PRIMARY KEY (id);


--
-- Name: hs_core_date_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_date
    ADD CONSTRAINT hs_core_date_pkey PRIMARY KEY (id);


--
-- Name: hs_core_description_content_type_id_101f8a6db2013e88_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_description
    ADD CONSTRAINT hs_core_description_content_type_id_101f8a6db2013e88_uniq UNIQUE (content_type_id, object_id);


--
-- Name: hs_core_description_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_description
    ADD CONSTRAINT hs_core_description_pkey PRIMARY KEY (id);


--
-- Name: hs_core_externalprofilelink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_externalprofilelink
    ADD CONSTRAINT hs_core_externalprofilelink_pkey PRIMARY KEY (id);


--
-- Name: hs_core_externalprofilelink_type_58d89d5b73bb6a79_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_externalprofilelink
    ADD CONSTRAINT hs_core_externalprofilelink_type_58d89d5b73bb6a79_uniq UNIQUE (type, url, content_type_id);


--
-- Name: hs_core_format_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_format
    ADD CONSTRAINT hs_core_format_pkey PRIMARY KEY (id);


--
-- Name: hs_core_genericresourc_genericresource_id_1066ca4ece8eaae9_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_view_groups
    ADD CONSTRAINT hs_core_genericresourc_genericresource_id_1066ca4ece8eaae9_uniq UNIQUE (genericresource_id, group_id);


--
-- Name: hs_core_genericresourc_genericresource_id_17ca1f2998d362d9_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_owners
    ADD CONSTRAINT hs_core_genericresourc_genericresource_id_17ca1f2998d362d9_uniq UNIQUE (genericresource_id, user_id);


--
-- Name: hs_core_genericresourc_genericresource_id_2f4e7822117b5a55_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_edit_groups
    ADD CONSTRAINT hs_core_genericresourc_genericresource_id_2f4e7822117b5a55_uniq UNIQUE (genericresource_id, group_id);


--
-- Name: hs_core_genericresourc_genericresource_id_38e78a60f4d4ff6f_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_view_users
    ADD CONSTRAINT hs_core_genericresourc_genericresource_id_38e78a60f4d4ff6f_uniq UNIQUE (genericresource_id, user_id);


--
-- Name: hs_core_genericresourc_genericresource_id_65437b438fb7ae44_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_edit_users
    ADD CONSTRAINT hs_core_genericresourc_genericresource_id_65437b438fb7ae44_uniq UNIQUE (genericresource_id, user_id);


--
-- Name: hs_core_genericresource_edit_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_edit_groups
    ADD CONSTRAINT hs_core_genericresource_edit_groups_pkey PRIMARY KEY (id);


--
-- Name: hs_core_genericresource_edit_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_edit_users
    ADD CONSTRAINT hs_core_genericresource_edit_users_pkey PRIMARY KEY (id);


--
-- Name: hs_core_genericresource_owners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_owners
    ADD CONSTRAINT hs_core_genericresource_owners_pkey PRIMARY KEY (id);


--
-- Name: hs_core_genericresource_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource
    ADD CONSTRAINT hs_core_genericresource_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: hs_core_genericresource_view_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_view_groups
    ADD CONSTRAINT hs_core_genericresource_view_groups_pkey PRIMARY KEY (id);


--
-- Name: hs_core_genericresource_view_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_genericresource_view_users
    ADD CONSTRAINT hs_core_genericresource_view_users_pkey PRIMARY KEY (id);


--
-- Name: hs_core_groupownership_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_groupownership
    ADD CONSTRAINT hs_core_groupownership_pkey PRIMARY KEY (id);


--
-- Name: hs_core_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_identifier
    ADD CONSTRAINT hs_core_identifier_pkey PRIMARY KEY (id);


--
-- Name: hs_core_identifier_url_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_identifier
    ADD CONSTRAINT hs_core_identifier_url_key UNIQUE (url);


--
-- Name: hs_core_language_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_language
    ADD CONSTRAINT hs_core_language_pkey PRIMARY KEY (id);


--
-- Name: hs_core_publisher_content_type_id_1d402c032dd55330_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_publisher
    ADD CONSTRAINT hs_core_publisher_content_type_id_1d402c032dd55330_uniq UNIQUE (content_type_id, object_id);


--
-- Name: hs_core_publisher_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_publisher
    ADD CONSTRAINT hs_core_publisher_pkey PRIMARY KEY (id);


--
-- Name: hs_core_relation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_relation
    ADD CONSTRAINT hs_core_relation_pkey PRIMARY KEY (id);


--
-- Name: hs_core_resourcefile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_resourcefile
    ADD CONSTRAINT hs_core_resourcefile_pkey PRIMARY KEY (id);


--
-- Name: hs_core_rights_content_type_id_ef5b26c774a3f32_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_rights
    ADD CONSTRAINT hs_core_rights_content_type_id_ef5b26c774a3f32_uniq UNIQUE (content_type_id, object_id);


--
-- Name: hs_core_rights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_rights
    ADD CONSTRAINT hs_core_rights_pkey PRIMARY KEY (id);


--
-- Name: hs_core_source_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_source
    ADD CONSTRAINT hs_core_source_pkey PRIMARY KEY (id);


--
-- Name: hs_core_subject_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_subject
    ADD CONSTRAINT hs_core_subject_pkey PRIMARY KEY (id);


--
-- Name: hs_core_title_content_type_id_558a1cad4b729d8a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_title
    ADD CONSTRAINT hs_core_title_content_type_id_558a1cad4b729d8a_uniq UNIQUE (content_type_id, object_id);


--
-- Name: hs_core_title_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_title
    ADD CONSTRAINT hs_core_title_pkey PRIMARY KEY (id);


--
-- Name: hs_core_type_content_type_id_18ed89604613f1ed_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_type
    ADD CONSTRAINT hs_core_type_content_type_id_18ed89604613f1ed_uniq UNIQUE (content_type_id, object_id);


--
-- Name: hs_core_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_core_type
    ADD CONSTRAINT hs_core_type_pkey PRIMARY KEY (id);


--
-- Name: hs_party_addresscodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_addresscodelist
    ADD CONSTRAINT hs_party_addresscodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_party_choicetype_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_choicetype
    ADD CONSTRAINT hs_party_choicetype_pkey PRIMARY KEY (id);


--
-- Name: hs_party_city_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_city
    ADD CONSTRAINT hs_party_city_pkey PRIMARY KEY (id);


--
-- Name: hs_party_country_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_country
    ADD CONSTRAINT hs_party_country_pkey PRIMARY KEY (id);


--
-- Name: hs_party_emailcodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_emailcodelist
    ADD CONSTRAINT hs_party_emailcodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_party_externalidentifiercodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_externalidentifiercodelist
    ADD CONSTRAINT hs_party_externalidentifiercodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_party_externalorgidentifier_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_externalorgidentifier
    ADD CONSTRAINT hs_party_externalorgidentifier_pkey PRIMARY KEY (id);


--
-- Name: hs_party_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_group
    ADD CONSTRAINT hs_party_group_pkey PRIMARY KEY (party_ptr_id);


--
-- Name: hs_party_namealiascodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_namealiascodelist
    ADD CONSTRAINT hs_party_namealiascodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_party_organization_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organization
    ADD CONSTRAINT hs_party_organization_pkey PRIMARY KEY (party_ptr_id);


--
-- Name: hs_party_organizationassociation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organizationassociation
    ADD CONSTRAINT hs_party_organizationassociation_pkey PRIMARY KEY (id);


--
-- Name: hs_party_organizationcodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organizationcodelist
    ADD CONSTRAINT hs_party_organizationcodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_party_organizationemail_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organizationemail
    ADD CONSTRAINT hs_party_organizationemail_pkey PRIMARY KEY (id);


--
-- Name: hs_party_organizationlocation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organizationlocation
    ADD CONSTRAINT hs_party_organizationlocation_pkey PRIMARY KEY (id);


--
-- Name: hs_party_organizationname_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organizationname
    ADD CONSTRAINT hs_party_organizationname_pkey PRIMARY KEY (id);


--
-- Name: hs_party_organizationphone_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_organizationphone
    ADD CONSTRAINT hs_party_organizationphone_pkey PRIMARY KEY (id);


--
-- Name: hs_party_othername_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_othername
    ADD CONSTRAINT hs_party_othername_pkey PRIMARY KEY (id);


--
-- Name: hs_party_party_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_party
    ADD CONSTRAINT hs_party_party_pkey PRIMARY KEY (id);


--
-- Name: hs_party_person_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_person
    ADD CONSTRAINT hs_party_person_pkey PRIMARY KEY (party_ptr_id);


--
-- Name: hs_party_personemail_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_personemail
    ADD CONSTRAINT hs_party_personemail_pkey PRIMARY KEY (id);


--
-- Name: hs_party_personexternalidentifier_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_personexternalidentifier
    ADD CONSTRAINT hs_party_personexternalidentifier_pkey PRIMARY KEY (id);


--
-- Name: hs_party_personlocation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_personlocation
    ADD CONSTRAINT hs_party_personlocation_pkey PRIMARY KEY (id);


--
-- Name: hs_party_personphone_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_personphone
    ADD CONSTRAINT hs_party_personphone_pkey PRIMARY KEY (id);


--
-- Name: hs_party_phonecodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_phonecodelist
    ADD CONSTRAINT hs_party_phonecodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_party_region_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_region
    ADD CONSTRAINT hs_party_region_pkey PRIMARY KEY (id);


--
-- Name: hs_party_usercodelist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_party_usercodelist
    ADD CONSTRAINT hs_party_usercodelist_pkey PRIMARY KEY (code);


--
-- Name: hs_scholar_profile_city_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_city
    ADD CONSTRAINT hs_scholar_profile_city_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_country_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_country
    ADD CONSTRAINT hs_scholar_profile_country_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_externalidentifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_externalidentifiers
    ADD CONSTRAINT hs_scholar_profile_externalidentifiers_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_externalorgidentifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_externalorgidentifiers
    ADD CONSTRAINT hs_scholar_profile_externalorgidentifiers_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_organization_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_organization
    ADD CONSTRAINT hs_scholar_profile_organization_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_organizationemail_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_organizationemail
    ADD CONSTRAINT hs_scholar_profile_organizationemail_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_organizationlocation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_organizationlocation
    ADD CONSTRAINT hs_scholar_profile_organizationlocation_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_organizationphone_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_organizationphone
    ADD CONSTRAINT hs_scholar_profile_organizationphone_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_orgassociations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_orgassociations
    ADD CONSTRAINT hs_scholar_profile_orgassociations_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_othernames_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_othernames
    ADD CONSTRAINT hs_scholar_profile_othernames_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_person_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_person
    ADD CONSTRAINT hs_scholar_profile_person_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_personemail_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_personemail
    ADD CONSTRAINT hs_scholar_profile_personemail_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_personlocation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_personlocation
    ADD CONSTRAINT hs_scholar_profile_personlocation_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_personphone_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_personphone
    ADD CONSTRAINT hs_scholar_profile_personphone_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_region_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_region
    ADD CONSTRAINT hs_scholar_profile_region_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_scholar_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_scholar
    ADD CONSTRAINT hs_scholar_profile_scholar_pkey PRIMARY KEY (person_ptr_id);


--
-- Name: hs_scholar_profile_scholar_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_scholar
    ADD CONSTRAINT hs_scholar_profile_scholar_user_id_key UNIQUE (user_id);


--
-- Name: hs_scholar_profile_scholarexternalidentifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_scholarexternalidentifiers
    ADD CONSTRAINT hs_scholar_profile_scholarexternalidentifiers_pkey PRIMARY KEY (externalidentifiers_ptr_id);


--
-- Name: hs_scholar_profile_scholargroup_createdBy_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_scholargroup
    ADD CONSTRAINT "hs_scholar_profile_scholargroup_createdBy_id_key" UNIQUE ("createdBy_id");


--
-- Name: hs_scholar_profile_scholargroup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_scholargroup
    ADD CONSTRAINT hs_scholar_profile_scholargroup_pkey PRIMARY KEY (group_ptr_id);


--
-- Name: hs_scholar_profile_userdemographics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_userdemographics
    ADD CONSTRAINT hs_scholar_profile_userdemographics_pkey PRIMARY KEY (id);


--
-- Name: hs_scholar_profile_userkeywords_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_scholar_profile_userkeywords
    ADD CONSTRAINT hs_scholar_profile_userkeywords_pkey PRIMARY KEY (id);


--
-- Name: pages_contentpage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY pages_richtextpage
    ADD CONSTRAINT pages_contentpage_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: pages_link_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY pages_link
    ADD CONSTRAINT pages_link_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: pages_page_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY pages_page
    ADD CONSTRAINT pages_page_pkey PRIMARY KEY (id);


--
-- Name: south_migrationhistory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY south_migrationhistory
    ADD CONSTRAINT south_migrationhistory_pkey PRIMARY KEY (id);


--
-- Name: tastypie_apiaccess_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tastypie_apiaccess
    ADD CONSTRAINT tastypie_apiaccess_pkey PRIMARY KEY (id);


--
-- Name: tastypie_apikey_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tastypie_apikey
    ADD CONSTRAINT tastypie_apikey_pkey PRIMARY KEY (id);


--
-- Name: tastypie_apikey_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tastypie_apikey
    ADD CONSTRAINT tastypie_apikey_user_id_key UNIQUE (user_id);


--
-- Name: theme_homepage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY theme_homepage
    ADD CONSTRAINT theme_homepage_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: theme_iconbox_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY theme_iconbox
    ADD CONSTRAINT theme_iconbox_pkey PRIMARY KEY (id);


--
-- Name: theme_siteconfiguration_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY theme_siteconfiguration
    ADD CONSTRAINT theme_siteconfiguration_pkey PRIMARY KEY (id);


--
-- Name: theme_userprofile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY theme_userprofile
    ADD CONSTRAINT theme_userprofile_pkey PRIMARY KEY (id);


--
-- Name: theme_userprofile_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY theme_userprofile
    ADD CONSTRAINT theme_userprofile_user_id_key UNIQUE (user_id);


--
-- Name: auth_group_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_group_name_like ON auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_group_permissions_group_id ON auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_group_permissions_permission_id ON auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_permission_content_type_id ON auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_user_groups_group_id ON auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_user_groups_user_id ON auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_user_user_permissions_permission_id ON auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_user_user_permissions_user_id ON auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX auth_user_username_like ON auth_user USING btree (username varchar_pattern_ops);


--
-- Name: blog_blogcategory_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogcategory_site_id ON blog_blogcategory USING btree (site_id);


--
-- Name: blog_blogpost_categories_blogcategory_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogpost_categories_blogcategory_id ON blog_blogpost_categories USING btree (blogcategory_id);


--
-- Name: blog_blogpost_categories_blogpost_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogpost_categories_blogpost_id ON blog_blogpost_categories USING btree (blogpost_id);


--
-- Name: blog_blogpost_related_posts_from_blogpost_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogpost_related_posts_from_blogpost_id ON blog_blogpost_related_posts USING btree (from_blogpost_id);


--
-- Name: blog_blogpost_related_posts_to_blogpost_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogpost_related_posts_to_blogpost_id ON blog_blogpost_related_posts USING btree (to_blogpost_id);


--
-- Name: blog_blogpost_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogpost_site_id ON blog_blogpost USING btree (site_id);


--
-- Name: blog_blogpost_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX blog_blogpost_user_id ON blog_blogpost USING btree (user_id);


--
-- Name: celery_taskmeta_hidden; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX celery_taskmeta_hidden ON celery_taskmeta USING btree (hidden);


--
-- Name: celery_taskmeta_task_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX celery_taskmeta_task_id_like ON celery_taskmeta USING btree (task_id varchar_pattern_ops);


--
-- Name: celery_tasksetmeta_hidden; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX celery_tasksetmeta_hidden ON celery_tasksetmeta USING btree (hidden);


--
-- Name: celery_tasksetmeta_taskset_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX celery_tasksetmeta_taskset_id_like ON celery_tasksetmeta USING btree (taskset_id varchar_pattern_ops);


--
-- Name: conf_setting_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX conf_setting_site_id ON conf_setting USING btree (site_id);


--
-- Name: core_sitepermission_sites_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX core_sitepermission_sites_site_id ON core_sitepermission_sites USING btree (site_id);


--
-- Name: core_sitepermission_sites_sitepermission_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX core_sitepermission_sites_sitepermission_id ON core_sitepermission_sites USING btree (sitepermission_id);


--
-- Name: django_admin_log_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_admin_log_content_type_id ON django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_admin_log_user_id ON django_admin_log USING btree (user_id);


--
-- Name: django_comment_flags_comment_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comment_flags_comment_id ON django_comment_flags USING btree (comment_id);


--
-- Name: django_comment_flags_flag; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comment_flags_flag ON django_comment_flags USING btree (flag);


--
-- Name: django_comment_flags_flag_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comment_flags_flag_like ON django_comment_flags USING btree (flag varchar_pattern_ops);


--
-- Name: django_comment_flags_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comment_flags_user_id ON django_comment_flags USING btree (user_id);


--
-- Name: django_comments_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comments_content_type_id ON django_comments USING btree (content_type_id);


--
-- Name: django_comments_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comments_site_id ON django_comments USING btree (site_id);


--
-- Name: django_comments_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_comments_user_id ON django_comments USING btree (user_id);


--
-- Name: django_irods_rodsenvironment_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_irods_rodsenvironment_owner_id ON django_irods_rodsenvironment USING btree (owner_id);


--
-- Name: django_redirect_old_path; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_redirect_old_path ON django_redirect USING btree (old_path);


--
-- Name: django_redirect_old_path_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_redirect_old_path_like ON django_redirect USING btree (old_path varchar_pattern_ops);


--
-- Name: django_redirect_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_redirect_site_id ON django_redirect USING btree (site_id);


--
-- Name: django_session_expire_date; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_session_expire_date ON django_session USING btree (expire_date);


--
-- Name: django_session_session_key_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_session_session_key_like ON django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: djcelery_periodictask_crontab_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_periodictask_crontab_id ON djcelery_periodictask USING btree (crontab_id);


--
-- Name: djcelery_periodictask_interval_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_periodictask_interval_id ON djcelery_periodictask USING btree (interval_id);


--
-- Name: djcelery_periodictask_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_periodictask_name_like ON djcelery_periodictask USING btree (name varchar_pattern_ops);


--
-- Name: djcelery_taskstate_hidden; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_hidden ON djcelery_taskstate USING btree (hidden);


--
-- Name: djcelery_taskstate_name; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_name ON djcelery_taskstate USING btree (name);


--
-- Name: djcelery_taskstate_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_name_like ON djcelery_taskstate USING btree (name varchar_pattern_ops);


--
-- Name: djcelery_taskstate_state; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_state ON djcelery_taskstate USING btree (state);


--
-- Name: djcelery_taskstate_state_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_state_like ON djcelery_taskstate USING btree (state varchar_pattern_ops);


--
-- Name: djcelery_taskstate_task_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_task_id_like ON djcelery_taskstate USING btree (task_id varchar_pattern_ops);


--
-- Name: djcelery_taskstate_tstamp; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_tstamp ON djcelery_taskstate USING btree (tstamp);


--
-- Name: djcelery_taskstate_worker_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_taskstate_worker_id ON djcelery_taskstate USING btree (worker_id);


--
-- Name: djcelery_workerstate_hostname_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_workerstate_hostname_like ON djcelery_workerstate USING btree (hostname varchar_pattern_ops);


--
-- Name: djcelery_workerstate_last_heartbeat; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX djcelery_workerstate_last_heartbeat ON djcelery_workerstate USING btree (last_heartbeat);


--
-- Name: dublincore_qualifieddublincoreelement_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dublincore_qualifieddublincoreelement_content_type_id ON dublincore_qualifieddublincoreelement USING btree (content_type_id);


--
-- Name: dublincore_qualifieddublincoreelementhistory_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dublincore_qualifieddublincoreelementhistory_content_type_id ON dublincore_qualifieddublincoreelementhistory USING btree (content_type_id);


--
-- Name: dublincore_qualifieddublincoreelementhistory_qdce_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dublincore_qualifieddublincoreelementhistory_qdce_id ON dublincore_qualifieddublincoreelementhistory USING btree (qdce_id);


--
-- Name: forms_field_form_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX forms_field_form_id ON forms_field USING btree (form_id);


--
-- Name: forms_fieldentry_entry_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX forms_fieldentry_entry_id ON forms_fieldentry USING btree (entry_id);


--
-- Name: forms_formentry_form_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX forms_formentry_form_id ON forms_formentry USING btree (form_id);


--
-- Name: ga_irods_rodsenvironment_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_irods_rodsenvironment_owner_id ON ga_irods_rodsenvironment USING btree (owner_id);


--
-- Name: ga_resources_catalogpage_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_catalogpage_owner_id ON ga_resources_catalogpage USING btree (owner_id);


--
-- Name: ga_resources_dataresource_bounding_box_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_dataresource_bounding_box_id ON ga_resources_dataresource USING gist (bounding_box);


--
-- Name: ga_resources_dataresource_native_bounding_box_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_dataresource_native_bounding_box_id ON ga_resources_dataresource USING gist (native_bounding_box);


--
-- Name: ga_resources_dataresource_next_refresh; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_dataresource_next_refresh ON ga_resources_dataresource USING btree (next_refresh);


--
-- Name: ga_resources_dataresource_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_dataresource_owner_id ON ga_resources_dataresource USING btree (owner_id);


--
-- Name: ga_resources_orderedresource_data_resource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_orderedresource_data_resource_id ON ga_resources_orderedresource USING btree (data_resource_id);


--
-- Name: ga_resources_orderedresource_resource_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_orderedresource_resource_group_id ON ga_resources_orderedresource USING btree (resource_group_id);


--
-- Name: ga_resources_relatedresource_foreign_resource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_relatedresource_foreign_resource_id ON ga_resources_relatedresource USING btree (foreign_resource_id);


--
-- Name: ga_resources_renderedlayer_data_resource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_renderedlayer_data_resource_id ON ga_resources_renderedlayer USING btree (data_resource_id);


--
-- Name: ga_resources_renderedlayer_default_style_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_renderedlayer_default_style_id ON ga_resources_renderedlayer USING btree (default_style_id);


--
-- Name: ga_resources_renderedlayer_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_renderedlayer_owner_id ON ga_resources_renderedlayer USING btree (owner_id);


--
-- Name: ga_resources_renderedlayer_styles_renderedlayer_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_renderedlayer_styles_renderedlayer_id ON ga_resources_renderedlayer_styles USING btree (renderedlayer_id);


--
-- Name: ga_resources_renderedlayer_styles_style_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_renderedlayer_styles_style_id ON ga_resources_renderedlayer_styles USING btree (style_id);


--
-- Name: ga_resources_style_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_resources_style_owner_id ON ga_resources_style USING btree (owner_id);


--
-- Name: galleries_galleryimage_gallery_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX galleries_galleryimage_gallery_id ON galleries_galleryimage USING btree (gallery_id);


--
-- Name: generic_assignedkeyword_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX generic_assignedkeyword_content_type_id ON generic_assignedkeyword USING btree (content_type_id);


--
-- Name: generic_assignedkeyword_keyword_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX generic_assignedkeyword_keyword_id ON generic_assignedkeyword USING btree (keyword_id);


--
-- Name: generic_keyword_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX generic_keyword_site_id ON generic_keyword USING btree (site_id);


--
-- Name: generic_rating_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX generic_rating_content_type_id ON generic_rating USING btree (content_type_id);


--
-- Name: generic_rating_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX generic_rating_user_id ON generic_rating USING btree (user_id);


--
-- Name: generic_threadedcomment_replied_to_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX generic_threadedcomment_replied_to_id ON generic_threadedcomment USING btree (replied_to_id);


--
-- Name: hs_core_bags_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_bags_content_type_id ON hs_core_bags USING btree (content_type_id);


--
-- Name: hs_core_bags_timestamp; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_bags_timestamp ON hs_core_bags USING btree ("timestamp");


--
-- Name: hs_core_contributor_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_contributor_content_type_id ON hs_core_contributor USING btree (content_type_id);


--
-- Name: hs_core_coverage_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_coverage_content_type_id ON hs_core_coverage USING btree (content_type_id);


--
-- Name: hs_core_creator_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_creator_content_type_id ON hs_core_creator USING btree (content_type_id);


--
-- Name: hs_core_date_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_date_content_type_id ON hs_core_date USING btree (content_type_id);


--
-- Name: hs_core_description_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_description_content_type_id ON hs_core_description USING btree (content_type_id);


--
-- Name: hs_core_externalprofilelink_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_externalprofilelink_content_type_id ON hs_core_externalprofilelink USING btree (content_type_id);


--
-- Name: hs_core_format_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_format_content_type_id ON hs_core_format USING btree (content_type_id);


--
-- Name: hs_core_genericresource_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_content_type_id ON hs_core_genericresource USING btree (content_type_id);


--
-- Name: hs_core_genericresource_creator_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_creator_id ON hs_core_genericresource USING btree (creator_id);


--
-- Name: hs_core_genericresource_doi; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_doi ON hs_core_genericresource USING btree (doi);


--
-- Name: hs_core_genericresource_doi_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_doi_like ON hs_core_genericresource USING btree (doi varchar_pattern_ops);


--
-- Name: hs_core_genericresource_edit_groups_genericresource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_edit_groups_genericresource_id ON hs_core_genericresource_edit_groups USING btree (genericresource_id);


--
-- Name: hs_core_genericresource_edit_groups_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_edit_groups_user_id ON hs_core_genericresource_edit_groups USING btree (group_id);


--
-- Name: hs_core_genericresource_edit_users_genericresource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_edit_users_genericresource_id ON hs_core_genericresource_edit_users USING btree (genericresource_id);


--
-- Name: hs_core_genericresource_edit_users_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_edit_users_user_id ON hs_core_genericresource_edit_users USING btree (user_id);


--
-- Name: hs_core_genericresource_last_changed_by_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_last_changed_by_id ON hs_core_genericresource USING btree (last_changed_by_id);


--
-- Name: hs_core_genericresource_owners_genericresource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_owners_genericresource_id ON hs_core_genericresource_owners USING btree (genericresource_id);


--
-- Name: hs_core_genericresource_owners_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_owners_user_id ON hs_core_genericresource_owners USING btree (user_id);


--
-- Name: hs_core_genericresource_short_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_short_id ON hs_core_genericresource USING btree (short_id);


--
-- Name: hs_core_genericresource_short_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_short_id_like ON hs_core_genericresource USING btree (short_id varchar_pattern_ops);


--
-- Name: hs_core_genericresource_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_user_id ON hs_core_genericresource USING btree (user_id);


--
-- Name: hs_core_genericresource_view_groups_genericresource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_view_groups_genericresource_id ON hs_core_genericresource_view_groups USING btree (genericresource_id);


--
-- Name: hs_core_genericresource_view_groups_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_view_groups_group_id ON hs_core_genericresource_view_groups USING btree (group_id);


--
-- Name: hs_core_genericresource_view_users_genericresource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_view_users_genericresource_id ON hs_core_genericresource_view_users USING btree (genericresource_id);


--
-- Name: hs_core_genericresource_view_users_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_genericresource_view_users_user_id ON hs_core_genericresource_view_users USING btree (user_id);


--
-- Name: hs_core_groupownership_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_groupownership_group_id ON hs_core_groupownership USING btree (group_id);


--
-- Name: hs_core_groupownership_owner_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_groupownership_owner_id ON hs_core_groupownership USING btree (owner_id);


--
-- Name: hs_core_identifier_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_identifier_content_type_id ON hs_core_identifier USING btree (content_type_id);


--
-- Name: hs_core_identifier_url_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_identifier_url_like ON hs_core_identifier USING btree (url varchar_pattern_ops);


--
-- Name: hs_core_language_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_language_content_type_id ON hs_core_language USING btree (content_type_id);


--
-- Name: hs_core_publisher_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_publisher_content_type_id ON hs_core_publisher USING btree (content_type_id);


--
-- Name: hs_core_relation_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_relation_content_type_id ON hs_core_relation USING btree (content_type_id);


--
-- Name: hs_core_resourcefile_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_resourcefile_content_type_id ON hs_core_resourcefile USING btree (content_type_id);


--
-- Name: hs_core_rights_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_rights_content_type_id ON hs_core_rights USING btree (content_type_id);


--
-- Name: hs_core_source_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_source_content_type_id ON hs_core_source USING btree (content_type_id);


--
-- Name: hs_core_subject_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_subject_content_type_id ON hs_core_subject USING btree (content_type_id);


--
-- Name: hs_core_title_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_title_content_type_id ON hs_core_title USING btree (content_type_id);


--
-- Name: hs_core_type_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_core_type_content_type_id ON hs_core_type USING btree (content_type_id);


--
-- Name: hs_party_addresscodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_addresscodelist_code_like ON hs_party_addresscodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_party_emailcodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_emailcodelist_code_like ON hs_party_emailcodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_party_externalidentifiercodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_externalidentifiercodelist_code_like ON hs_party_externalidentifiercodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_party_externalorgidentifier_identifierName_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_externalorgidentifier_identifierName_id" ON hs_party_externalorgidentifier USING btree ("identifierName_id");


--
-- Name: hs_party_externalorgidentifier_identifierName_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_externalorgidentifier_identifierName_id_like" ON hs_party_externalorgidentifier USING btree ("identifierName_id" varchar_pattern_ops);


--
-- Name: hs_party_externalorgidentifier_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_externalorgidentifier_organization_id ON hs_party_externalorgidentifier USING btree (organization_id);


--
-- Name: hs_party_group_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_group_site_id ON hs_party_group USING btree (site_id);


--
-- Name: hs_party_namealiascodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_namealiascodelist_code_like ON hs_party_namealiascodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_party_organization_organizationType_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_organization_organizationType_id" ON hs_party_organization USING btree ("organizationType_id");


--
-- Name: hs_party_organization_organizationType_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_organization_organizationType_id_like" ON hs_party_organization USING btree ("organizationType_id" varchar_pattern_ops);


--
-- Name: hs_party_organization_parentOrganization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_organization_parentOrganization_id" ON hs_party_organization USING btree ("parentOrganization_id");


--
-- Name: hs_party_organization_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organization_site_id ON hs_party_organization USING btree (site_id);


--
-- Name: hs_party_organizationassociation_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationassociation_organization_id ON hs_party_organizationassociation USING btree (organization_id);


--
-- Name: hs_party_organizationassociation_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationassociation_person_id ON hs_party_organizationassociation USING btree (person_id);


--
-- Name: hs_party_organizationcodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationcodelist_code_like ON hs_party_organizationcodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_party_organizationemail_email_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationemail_email_type_id ON hs_party_organizationemail USING btree (email_type_id);


--
-- Name: hs_party_organizationemail_email_type_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationemail_email_type_id_like ON hs_party_organizationemail USING btree (email_type_id varchar_pattern_ops);


--
-- Name: hs_party_organizationemail_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationemail_organization_id ON hs_party_organizationemail USING btree (organization_id);


--
-- Name: hs_party_organizationlocation_address_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationlocation_address_type_id ON hs_party_organizationlocation USING btree (address_type_id);


--
-- Name: hs_party_organizationlocation_address_type_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationlocation_address_type_id_like ON hs_party_organizationlocation USING btree (address_type_id varchar_pattern_ops);


--
-- Name: hs_party_organizationlocation_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationlocation_organization_id ON hs_party_organizationlocation USING btree (organization_id);


--
-- Name: hs_party_organizationname_annotation_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationname_annotation_id ON hs_party_organizationname USING btree (annotation_id);


--
-- Name: hs_party_organizationname_annotation_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationname_annotation_id_like ON hs_party_organizationname USING btree (annotation_id varchar_pattern_ops);


--
-- Name: hs_party_organizationname_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationname_organization_id ON hs_party_organizationname USING btree (organization_id);


--
-- Name: hs_party_organizationphone_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationphone_organization_id ON hs_party_organizationphone USING btree (organization_id);


--
-- Name: hs_party_organizationphone_phone_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationphone_phone_type_id ON hs_party_organizationphone USING btree (phone_type_id);


--
-- Name: hs_party_organizationphone_phone_type_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_organizationphone_phone_type_id_like ON hs_party_organizationphone USING btree (phone_type_id varchar_pattern_ops);


--
-- Name: hs_party_othername_annotation_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_othername_annotation_id ON hs_party_othername USING btree (annotation_id);


--
-- Name: hs_party_othername_annotation_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_othername_annotation_id_like ON hs_party_othername USING btree (annotation_id varchar_pattern_ops);


--
-- Name: hs_party_othername_persons_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_othername_persons_id ON hs_party_othername USING btree (persons_id);


--
-- Name: hs_party_person_primaryOrganizationRecord_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_person_primaryOrganizationRecord_id" ON hs_party_person USING btree ("primaryOrganizationRecord_id");


--
-- Name: hs_party_person_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_person_site_id ON hs_party_person USING btree (site_id);


--
-- Name: hs_party_personemail_email_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personemail_email_type_id ON hs_party_personemail USING btree (email_type_id);


--
-- Name: hs_party_personemail_email_type_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personemail_email_type_id_like ON hs_party_personemail USING btree (email_type_id varchar_pattern_ops);


--
-- Name: hs_party_personemail_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personemail_person_id ON hs_party_personemail USING btree (person_id);


--
-- Name: hs_party_personexternalidentifier_identifierName_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_personexternalidentifier_identifierName_id" ON hs_party_personexternalidentifier USING btree ("identifierName_id");


--
-- Name: hs_party_personexternalidentifier_identifierName_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_party_personexternalidentifier_identifierName_id_like" ON hs_party_personexternalidentifier USING btree ("identifierName_id" varchar_pattern_ops);


--
-- Name: hs_party_personexternalidentifier_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personexternalidentifier_person_id ON hs_party_personexternalidentifier USING btree (person_id);


--
-- Name: hs_party_personlocation_address_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personlocation_address_type_id ON hs_party_personlocation USING btree (address_type_id);


--
-- Name: hs_party_personlocation_address_type_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personlocation_address_type_id_like ON hs_party_personlocation USING btree (address_type_id varchar_pattern_ops);


--
-- Name: hs_party_personlocation_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personlocation_person_id ON hs_party_personlocation USING btree (person_id);


--
-- Name: hs_party_personphone_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personphone_person_id ON hs_party_personphone USING btree (person_id);


--
-- Name: hs_party_personphone_phone_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personphone_phone_type_id ON hs_party_personphone USING btree (phone_type_id);


--
-- Name: hs_party_personphone_phone_type_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_personphone_phone_type_id_like ON hs_party_personphone USING btree (phone_type_id varchar_pattern_ops);


--
-- Name: hs_party_phonecodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_phonecodelist_code_like ON hs_party_phonecodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_party_usercodelist_code_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_party_usercodelist_code_like ON hs_party_usercodelist USING btree (code varchar_pattern_ops);


--
-- Name: hs_scholar_profile_externalorgidentifiers_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_externalorgidentifiers_organization_id ON hs_scholar_profile_externalorgidentifiers USING btree (organization_id);


--
-- Name: hs_scholar_profile_organization_parentOrganization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX "hs_scholar_profile_organization_parentOrganization_id" ON hs_scholar_profile_organization USING btree ("parentOrganization_id");


--
-- Name: hs_scholar_profile_organization_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_organization_site_id ON hs_scholar_profile_organization USING btree (site_id);


--
-- Name: hs_scholar_profile_organizationemail_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_organizationemail_organization_id ON hs_scholar_profile_organizationemail USING btree (organization_id);


--
-- Name: hs_scholar_profile_organizationlocation_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_organizationlocation_organization_id ON hs_scholar_profile_organizationlocation USING btree (organization_id);


--
-- Name: hs_scholar_profile_organizationphone_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_organizationphone_organization_id ON hs_scholar_profile_organizationphone USING btree (organization_id);


--
-- Name: hs_scholar_profile_orgassociations_organization_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_orgassociations_organization_id ON hs_scholar_profile_orgassociations USING btree (organization_id);


--
-- Name: hs_scholar_profile_orgassociations_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_orgassociations_person_id ON hs_scholar_profile_orgassociations USING btree (person_id);


--
-- Name: hs_scholar_profile_othernames_persons_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_othernames_persons_id ON hs_scholar_profile_othernames USING btree (persons_id);


--
-- Name: hs_scholar_profile_person_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_person_site_id ON hs_scholar_profile_person USING btree (site_id);


--
-- Name: hs_scholar_profile_personemail_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_personemail_person_id ON hs_scholar_profile_personemail USING btree (person_id);


--
-- Name: hs_scholar_profile_personlocation_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_personlocation_person_id ON hs_scholar_profile_personlocation USING btree (person_id);


--
-- Name: hs_scholar_profile_personphone_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_personphone_person_id ON hs_scholar_profile_personphone USING btree (person_id);


--
-- Name: hs_scholar_profile_scholar_demographics_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_scholar_demographics_id ON hs_scholar_profile_scholar USING btree (demographics_id);


--
-- Name: hs_scholar_profile_scholarexternalidentifiers_scholar_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_scholarexternalidentifiers_scholar_id ON hs_scholar_profile_scholarexternalidentifiers USING btree (scholar_id);


--
-- Name: hs_scholar_profile_scholargroup_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_scholargroup_site_id ON hs_scholar_profile_scholargroup USING btree (site_id);


--
-- Name: hs_scholar_profile_userdemographics_city_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_userdemographics_city_id ON hs_scholar_profile_userdemographics USING btree (city_id);


--
-- Name: hs_scholar_profile_userdemographics_country_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_userdemographics_country_id ON hs_scholar_profile_userdemographics USING btree (country_id);


--
-- Name: hs_scholar_profile_userdemographics_region_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_userdemographics_region_id ON hs_scholar_profile_userdemographics USING btree (region_id);


--
-- Name: hs_scholar_profile_userkeywords_person_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_scholar_profile_userkeywords_person_id ON hs_scholar_profile_userkeywords USING btree (person_id);


--
-- Name: pages_page_parent_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX pages_page_parent_id ON pages_page USING btree (parent_id);


--
-- Name: pages_page_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX pages_page_site_id ON pages_page USING btree (site_id);


--
-- Name: tastypie_apikey_key; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tastypie_apikey_key ON tastypie_apikey USING btree (key);


--
-- Name: theme_iconbox_homepage_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX theme_iconbox_homepage_id ON theme_iconbox USING btree (homepage_id);


--
-- Name: theme_siteconfiguration_site_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX theme_siteconfiguration_site_id ON theme_siteconfiguration USING btree (site_id);


--
-- Name: address_type_id_refs_code_540b122d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationlocation
    ADD CONSTRAINT address_type_id_refs_code_540b122d FOREIGN KEY (address_type_id) REFERENCES hs_party_addresscodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: address_type_id_refs_code_d0fdde8c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personlocation
    ADD CONSTRAINT address_type_id_refs_code_d0fdde8c FOREIGN KEY (address_type_id) REFERENCES hs_party_addresscodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: annotation_id_refs_code_7baf2f4c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_othername
    ADD CONSTRAINT annotation_id_refs_code_7baf2f4c FOREIGN KEY (annotation_id) REFERENCES hs_party_namealiascodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: annotation_id_refs_code_8fed8f55; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationname
    ADD CONSTRAINT annotation_id_refs_code_8fed8f55 FOREIGN KEY (annotation_id) REFERENCES hs_party_namealiascodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_fkey FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: blogcategory_id_refs_id_91693b1c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost_categories
    ADD CONSTRAINT blogcategory_id_refs_id_91693b1c FOREIGN KEY (blogcategory_id) REFERENCES blog_blogcategory(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: blogpost_id_refs_id_6a2ad936; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost_categories
    ADD CONSTRAINT blogpost_id_refs_id_6a2ad936 FOREIGN KEY (blogpost_id) REFERENCES blog_blogpost(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: city_id_refs_id_19f81b19; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_userdemographics
    ADD CONSTRAINT city_id_refs_id_19f81b19 FOREIGN KEY (city_id) REFERENCES hs_scholar_profile_city(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: comment_ptr_id_refs_id_d4c241e5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_threadedcomment
    ADD CONSTRAINT comment_ptr_id_refs_id_d4c241e5 FOREIGN KEY (comment_ptr_id) REFERENCES django_comments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_016474ea; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_publisher
    ADD CONSTRAINT content_type_id_refs_id_016474ea FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_07d4acf0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource
    ADD CONSTRAINT content_type_id_refs_id_07d4acf0 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_0dbe97eb; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_subject
    ADD CONSTRAINT content_type_id_refs_id_0dbe97eb FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_0f7fd1d0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_type
    ADD CONSTRAINT content_type_id_refs_id_0f7fd1d0 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_14a23aea; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_language
    ADD CONSTRAINT content_type_id_refs_id_14a23aea FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_1c638e93; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_rating
    ADD CONSTRAINT content_type_id_refs_id_1c638e93 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_2efc891d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_title
    ADD CONSTRAINT content_type_id_refs_id_2efc891d FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_408804a4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_externalprofilelink
    ADD CONSTRAINT content_type_id_refs_id_408804a4 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_4285c85f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_resourcefile
    ADD CONSTRAINT content_type_id_refs_id_4285c85f FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_7504b98d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelementhistory
    ADD CONSTRAINT content_type_id_refs_id_7504b98d FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_7b5f3840; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_relation
    ADD CONSTRAINT content_type_id_refs_id_7b5f3840 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_7fb920c4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_contributor
    ADD CONSTRAINT content_type_id_refs_id_7fb920c4 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_8af9db16; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_identifier
    ADD CONSTRAINT content_type_id_refs_id_8af9db16 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_9cf1fb54; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_source
    ADD CONSTRAINT content_type_id_refs_id_9cf1fb54 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_a4717fc0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_date
    ADD CONSTRAINT content_type_id_refs_id_a4717fc0 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_a73b225b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_coverage
    ADD CONSTRAINT content_type_id_refs_id_a73b225b FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_c36d959c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_assignedkeyword
    ADD CONSTRAINT content_type_id_refs_id_c36d959c FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_c5f70efd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_description
    ADD CONSTRAINT content_type_id_refs_id_c5f70efd FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_c639bc3f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_format
    ADD CONSTRAINT content_type_id_refs_id_c639bc3f FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_c88d0ee7; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_bags
    ADD CONSTRAINT content_type_id_refs_id_c88d0ee7 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_d043b34a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT content_type_id_refs_id_d043b34a FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_db605579; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_creator
    ADD CONSTRAINT content_type_id_refs_id_db605579 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_f2470641; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_rights
    ADD CONSTRAINT content_type_id_refs_id_f2470641 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: content_type_id_refs_id_fc6222af; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelement
    ADD CONSTRAINT content_type_id_refs_id_fc6222af FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: country_id_refs_id_7a53f3f7; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_userdemographics
    ADD CONSTRAINT country_id_refs_id_7a53f3f7 FOREIGN KEY (country_id) REFERENCES hs_scholar_profile_country(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: createdBy_id_refs_person_ptr_id_24851b27; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholargroup
    ADD CONSTRAINT "createdBy_id_refs_person_ptr_id_24851b27" FOREIGN KEY ("createdBy_id") REFERENCES hs_scholar_profile_scholar(person_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: crontab_id_refs_id_286da0d1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_periodictask
    ADD CONSTRAINT crontab_id_refs_id_286da0d1 FOREIGN KEY (crontab_id) REFERENCES djcelery_crontabschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: data_resource_id_refs_page_ptr_id_a59a4665; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_orderedresource
    ADD CONSTRAINT data_resource_id_refs_page_ptr_id_a59a4665 FOREIGN KEY (data_resource_id) REFERENCES ga_resources_dataresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: data_resource_id_refs_page_ptr_id_e2b8544b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer
    ADD CONSTRAINT data_resource_id_refs_page_ptr_id_e2b8544b FOREIGN KEY (data_resource_id) REFERENCES ga_resources_dataresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: default_style_id_refs_page_ptr_id_1538365b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer
    ADD CONSTRAINT default_style_id_refs_page_ptr_id_1538365b FOREIGN KEY (default_style_id) REFERENCES ga_resources_style(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: demographics_id_refs_id_14c866dc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholar
    ADD CONSTRAINT demographics_id_refs_id_14c866dc FOREIGN KEY (demographics_id) REFERENCES hs_scholar_profile_userdemographics(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_content_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_fkey FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_comment_flags_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comment_flags
    ADD CONSTRAINT django_comment_flags_comment_id_fkey FOREIGN KEY (comment_id) REFERENCES django_comments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_comment_flags_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comment_flags
    ADD CONSTRAINT django_comment_flags_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_comments_content_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comments
    ADD CONSTRAINT django_comments_content_type_id_fkey FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_comments_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comments
    ADD CONSTRAINT django_comments_site_id_fkey FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_irods_rodsenvironment_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_irods_rodsenvironment
    ADD CONSTRAINT django_irods_rodsenvironment_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: email_type_id_refs_code_56e785f9; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personemail
    ADD CONSTRAINT email_type_id_refs_code_56e785f9 FOREIGN KEY (email_type_id) REFERENCES hs_party_emailcodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: email_type_id_refs_code_d463e90b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationemail
    ADD CONSTRAINT email_type_id_refs_code_d463e90b FOREIGN KEY (email_type_id) REFERENCES hs_party_emailcodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: entry_id_refs_id_e329b086; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_fieldentry
    ADD CONSTRAINT entry_id_refs_id_e329b086 FOREIGN KEY (entry_id) REFERENCES forms_formentry(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: externalidentifiers_ptr_id_refs_id_53f620d2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholarexternalidentifiers
    ADD CONSTRAINT externalidentifiers_ptr_id_refs_id_53f620d2 FOREIGN KEY (externalidentifiers_ptr_id) REFERENCES hs_scholar_profile_externalidentifiers(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: foreign_resource_id_refs_page_ptr_id_f3121e9c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_relatedresource
    ADD CONSTRAINT foreign_resource_id_refs_page_ptr_id_f3121e9c FOREIGN KEY (foreign_resource_id) REFERENCES ga_resources_dataresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: form_id_refs_page_ptr_id_4d605921; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_formentry
    ADD CONSTRAINT form_id_refs_page_ptr_id_4d605921 FOREIGN KEY (form_id) REFERENCES forms_form(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: form_id_refs_page_ptr_id_5a752766; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_field
    ADD CONSTRAINT form_id_refs_page_ptr_id_5a752766 FOREIGN KEY (form_id) REFERENCES forms_form(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: from_blogpost_id_refs_id_6404941b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost_related_posts
    ADD CONSTRAINT from_blogpost_id_refs_id_6404941b FOREIGN KEY (from_blogpost_id) REFERENCES blog_blogpost(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ga_irods_rodsenvironment_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_irods_rodsenvironment
    ADD CONSTRAINT ga_irods_rodsenvironment_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: gallery_id_refs_page_ptr_id_d6457fc6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY galleries_galleryimage
    ADD CONSTRAINT gallery_id_refs_page_ptr_id_d6457fc6 FOREIGN KEY (gallery_id) REFERENCES galleries_gallery(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: genericresource_id_refs_page_ptr_id_063888a3; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_groups
    ADD CONSTRAINT genericresource_id_refs_page_ptr_id_063888a3 FOREIGN KEY (genericresource_id) REFERENCES hs_core_genericresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: genericresource_id_refs_page_ptr_id_1b325f2a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_view_groups
    ADD CONSTRAINT genericresource_id_refs_page_ptr_id_1b325f2a FOREIGN KEY (genericresource_id) REFERENCES hs_core_genericresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: genericresource_id_refs_page_ptr_id_2d0a4979; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_users
    ADD CONSTRAINT genericresource_id_refs_page_ptr_id_2d0a4979 FOREIGN KEY (genericresource_id) REFERENCES hs_core_genericresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: genericresource_id_refs_page_ptr_id_8ba7d05f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_view_users
    ADD CONSTRAINT genericresource_id_refs_page_ptr_id_8ba7d05f FOREIGN KEY (genericresource_id) REFERENCES hs_core_genericresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: genericresource_id_refs_page_ptr_id_f3be5566; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_owners
    ADD CONSTRAINT genericresource_id_refs_page_ptr_id_f3be5566 FOREIGN KEY (genericresource_id) REFERENCES hs_core_genericresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: group_id_refs_id_07cb9889; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_groupownership
    ADD CONSTRAINT group_id_refs_id_07cb9889 FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: group_id_refs_id_2bf6790f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_view_groups
    ADD CONSTRAINT group_id_refs_id_2bf6790f FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: group_id_refs_id_f4b32aac; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT group_id_refs_id_f4b32aac FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: group_ptr_id_refs_id_5deda983; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholargroup
    ADD CONSTRAINT group_ptr_id_refs_id_5deda983 FOREIGN KEY (group_ptr_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: homepage_id_refs_page_ptr_id_f766bdfd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_iconbox
    ADD CONSTRAINT homepage_id_refs_page_ptr_id_f766bdfd FOREIGN KEY (homepage_id) REFERENCES theme_homepage(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: identifierName_id_refs_code_d53ad41b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personexternalidentifier
    ADD CONSTRAINT "identifierName_id_refs_code_d53ad41b" FOREIGN KEY ("identifierName_id") REFERENCES hs_party_externalidentifiercodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: identifierName_id_refs_code_fbc35c1f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_externalorgidentifier
    ADD CONSTRAINT "identifierName_id_refs_code_fbc35c1f" FOREIGN KEY ("identifierName_id") REFERENCES hs_party_externalidentifiercodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: interval_id_refs_id_1829f358; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_periodictask
    ADD CONSTRAINT interval_id_refs_id_1829f358 FOREIGN KEY (interval_id) REFERENCES djcelery_intervalschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: keyword_id_refs_id_aa70ce50; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_assignedkeyword
    ADD CONSTRAINT keyword_id_refs_id_aa70ce50 FOREIGN KEY (keyword_id) REFERENCES generic_keyword(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organizationType_id_refs_code_f5cc1b06; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organization
    ADD CONSTRAINT "organizationType_id_refs_code_f5cc1b06" FOREIGN KEY ("organizationType_id") REFERENCES hs_party_organizationcodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_id_3dc2b44d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organizationphone
    ADD CONSTRAINT organization_id_refs_id_3dc2b44d FOREIGN KEY (organization_id) REFERENCES hs_scholar_profile_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_id_902d1e8d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organizationlocation
    ADD CONSTRAINT organization_id_refs_id_902d1e8d FOREIGN KEY (organization_id) REFERENCES hs_scholar_profile_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_id_bf864794; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_orgassociations
    ADD CONSTRAINT organization_id_refs_id_bf864794 FOREIGN KEY (organization_id) REFERENCES hs_scholar_profile_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_id_d3109675; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organizationemail
    ADD CONSTRAINT organization_id_refs_id_d3109675 FOREIGN KEY (organization_id) REFERENCES hs_scholar_profile_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_id_e49f9749; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_externalorgidentifiers
    ADD CONSTRAINT organization_id_refs_id_e49f9749 FOREIGN KEY (organization_id) REFERENCES hs_scholar_profile_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_party_ptr_id_3414fe3c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationphone
    ADD CONSTRAINT organization_id_refs_party_ptr_id_3414fe3c FOREIGN KEY (organization_id) REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_party_ptr_id_3d58b415; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_externalorgidentifier
    ADD CONSTRAINT organization_id_refs_party_ptr_id_3d58b415 FOREIGN KEY (organization_id) REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_party_ptr_id_933e120e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationemail
    ADD CONSTRAINT organization_id_refs_party_ptr_id_933e120e FOREIGN KEY (organization_id) REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_party_ptr_id_aeafced6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationassociation
    ADD CONSTRAINT organization_id_refs_party_ptr_id_aeafced6 FOREIGN KEY (organization_id) REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_party_ptr_id_e8cc2840; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationname
    ADD CONSTRAINT organization_id_refs_party_ptr_id_e8cc2840 FOREIGN KEY (organization_id) REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: organization_id_refs_party_ptr_id_fd2c3320; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationlocation
    ADD CONSTRAINT organization_id_refs_party_ptr_id_fd2c3320 FOREIGN KEY (organization_id) REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: owner_id_refs_id_4a4141f5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_dataresource
    ADD CONSTRAINT owner_id_refs_id_4a4141f5 FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: owner_id_refs_id_d528c757; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_catalogpage
    ADD CONSTRAINT owner_id_refs_id_d528c757 FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: owner_id_refs_id_e2271514; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_groupownership
    ADD CONSTRAINT owner_id_refs_id_e2271514 FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: owner_id_refs_id_ee8494bc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer
    ADD CONSTRAINT owner_id_refs_id_ee8494bc FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: owner_id_refs_id_f919891d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_style
    ADD CONSTRAINT owner_id_refs_id_f919891d FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_1f0514ba; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_relatedresource
    ADD CONSTRAINT page_ptr_id_refs_id_1f0514ba FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_2adddb0b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_link
    ADD CONSTRAINT page_ptr_id_refs_id_2adddb0b FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_41a57472; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource
    ADD CONSTRAINT page_ptr_id_refs_id_41a57472 FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_558d29bc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_richtextpage
    ADD CONSTRAINT page_ptr_id_refs_id_558d29bc FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_5ea3a75a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_dataresource
    ADD CONSTRAINT page_ptr_id_refs_id_5ea3a75a FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_75804475; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY galleries_gallery
    ADD CONSTRAINT page_ptr_id_refs_id_75804475 FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_93df8296; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_resourcegroup
    ADD CONSTRAINT page_ptr_id_refs_id_93df8296 FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_a8ba09aa; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_catalogpage
    ADD CONSTRAINT page_ptr_id_refs_id_a8ba09aa FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_ae3b1c29; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_style
    ADD CONSTRAINT page_ptr_id_refs_id_ae3b1c29 FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_bf381bd5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_homepage
    ADD CONSTRAINT page_ptr_id_refs_id_bf381bd5 FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_f73583c5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer
    ADD CONSTRAINT page_ptr_id_refs_id_f73583c5 FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: page_ptr_id_refs_id_fe19b67b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_form
    ADD CONSTRAINT page_ptr_id_refs_id_fe19b67b FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: parentOrganization_id_refs_id_0d5d7e04; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organization
    ADD CONSTRAINT "parentOrganization_id_refs_id_0d5d7e04" FOREIGN KEY ("parentOrganization_id") REFERENCES hs_scholar_profile_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: parentOrganization_id_refs_party_ptr_id_fb22991c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organization
    ADD CONSTRAINT "parentOrganization_id_refs_party_ptr_id_fb22991c" FOREIGN KEY ("parentOrganization_id") REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: parent_id_refs_id_68963b8e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_page
    ADD CONSTRAINT parent_id_refs_id_68963b8e FOREIGN KEY (parent_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: party_ptr_id_refs_id_a4c921fd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_person
    ADD CONSTRAINT party_ptr_id_refs_id_a4c921fd FOREIGN KEY (party_ptr_id) REFERENCES hs_party_party(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: party_ptr_id_refs_id_b233f9c9; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_group
    ADD CONSTRAINT party_ptr_id_refs_id_b233f9c9 FOREIGN KEY (party_ptr_id) REFERENCES hs_party_party(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: party_ptr_id_refs_id_c897f9af; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organization
    ADD CONSTRAINT party_ptr_id_refs_id_c897f9af FOREIGN KEY (party_ptr_id) REFERENCES hs_party_party(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_id_0f828f02; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_personphone
    ADD CONSTRAINT person_id_refs_id_0f828f02 FOREIGN KEY (person_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_id_15958bad; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_orgassociations
    ADD CONSTRAINT person_id_refs_id_15958bad FOREIGN KEY (person_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_id_7066e467; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_userkeywords
    ADD CONSTRAINT person_id_refs_id_7066e467 FOREIGN KEY (person_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_id_988d2157; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_personemail
    ADD CONSTRAINT person_id_refs_id_988d2157 FOREIGN KEY (person_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_id_cd05bc69; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_personlocation
    ADD CONSTRAINT person_id_refs_id_cd05bc69 FOREIGN KEY (person_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_party_ptr_id_37520c31; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationassociation
    ADD CONSTRAINT person_id_refs_party_ptr_id_37520c31 FOREIGN KEY (person_id) REFERENCES hs_party_person(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_party_ptr_id_3af9b7d7; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personphone
    ADD CONSTRAINT person_id_refs_party_ptr_id_3af9b7d7 FOREIGN KEY (person_id) REFERENCES hs_party_person(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_party_ptr_id_679331e1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personlocation
    ADD CONSTRAINT person_id_refs_party_ptr_id_679331e1 FOREIGN KEY (person_id) REFERENCES hs_party_person(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_party_ptr_id_8c5cca63; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personexternalidentifier
    ADD CONSTRAINT person_id_refs_party_ptr_id_8c5cca63 FOREIGN KEY (person_id) REFERENCES hs_party_person(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_id_refs_party_ptr_id_a7a2c64b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personemail
    ADD CONSTRAINT person_id_refs_party_ptr_id_a7a2c64b FOREIGN KEY (person_id) REFERENCES hs_party_person(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: person_ptr_id_refs_id_68cfedf7; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholar
    ADD CONSTRAINT person_ptr_id_refs_id_68cfedf7 FOREIGN KEY (person_ptr_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: persons_id_refs_id_9a63bcca; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_othernames
    ADD CONSTRAINT persons_id_refs_id_9a63bcca FOREIGN KEY (persons_id) REFERENCES hs_scholar_profile_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: persons_id_refs_party_ptr_id_08307bb2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_othername
    ADD CONSTRAINT persons_id_refs_party_ptr_id_08307bb2 FOREIGN KEY (persons_id) REFERENCES hs_party_person(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: phone_type_id_refs_code_1a00e417; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_personphone
    ADD CONSTRAINT phone_type_id_refs_code_1a00e417 FOREIGN KEY (phone_type_id) REFERENCES hs_party_phonecodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: phone_type_id_refs_code_9880d355; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organizationphone
    ADD CONSTRAINT phone_type_id_refs_code_9880d355 FOREIGN KEY (phone_type_id) REFERENCES hs_party_phonecodelist(code) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: primaryOrganizationRecord_id_refs_party_ptr_id_fed37680; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_person
    ADD CONSTRAINT "primaryOrganizationRecord_id_refs_party_ptr_id_fed37680" FOREIGN KEY ("primaryOrganizationRecord_id") REFERENCES hs_party_organization(party_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: qdce_id_refs_id_7eb27ec4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelementhistory
    ADD CONSTRAINT qdce_id_refs_id_7eb27ec4 FOREIGN KEY (qdce_id) REFERENCES dublincore_qualifieddublincoreelement(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: region_id_refs_id_ee73987e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_userdemographics
    ADD CONSTRAINT region_id_refs_id_ee73987e FOREIGN KEY (region_id) REFERENCES hs_scholar_profile_region(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: renderedlayer_id_refs_page_ptr_id_7bc3ed6b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer_styles
    ADD CONSTRAINT renderedlayer_id_refs_page_ptr_id_7bc3ed6b FOREIGN KEY (renderedlayer_id) REFERENCES ga_resources_renderedlayer(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: replied_to_id_refs_comment_ptr_id_83bd8e31; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_threadedcomment
    ADD CONSTRAINT replied_to_id_refs_comment_ptr_id_83bd8e31 FOREIGN KEY (replied_to_id) REFERENCES generic_threadedcomment(comment_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: resource_group_id_refs_page_ptr_id_9dce21a0; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_orderedresource
    ADD CONSTRAINT resource_group_id_refs_page_ptr_id_9dce21a0 FOREIGN KEY (resource_group_id) REFERENCES ga_resources_resourcegroup(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: scholar_id_refs_person_ptr_id_2aa668e3; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholarexternalidentifiers
    ADD CONSTRAINT scholar_id_refs_person_ptr_id_2aa668e3 FOREIGN KEY (scholar_id) REFERENCES hs_scholar_profile_scholar(person_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_1ba836f6; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_person
    ADD CONSTRAINT site_id_refs_id_1ba836f6 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_242b097b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_scholargroup
    ADD CONSTRAINT site_id_refs_id_242b097b FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_29e7e142; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY conf_setting
    ADD CONSTRAINT site_id_refs_id_29e7e142 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_390e2add; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_redirect
    ADD CONSTRAINT site_id_refs_id_390e2add FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_550d54a5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_person
    ADD CONSTRAINT site_id_refs_id_550d54a5 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_6c5d0e92; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_group
    ADD CONSTRAINT site_id_refs_id_6c5d0e92 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_70c9ac77; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_page
    ADD CONSTRAINT site_id_refs_id_70c9ac77 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_8566506f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_party_organization
    ADD CONSTRAINT site_id_refs_id_8566506f FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_8ee83179; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_siteconfiguration
    ADD CONSTRAINT site_id_refs_id_8ee83179 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_91a6d9d4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY core_sitepermission_sites
    ADD CONSTRAINT site_id_refs_id_91a6d9d4 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_93afc60f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogcategory
    ADD CONSTRAINT site_id_refs_id_93afc60f FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_ac21095f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost
    ADD CONSTRAINT site_id_refs_id_ac21095f FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_bf232785; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_scholar_profile_organization
    ADD CONSTRAINT site_id_refs_id_bf232785 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: site_id_refs_id_f6393455; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_keyword
    ADD CONSTRAINT site_id_refs_id_f6393455 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sitepermission_id_refs_id_7dccdcbd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY core_sitepermission_sites
    ADD CONSTRAINT sitepermission_id_refs_id_7dccdcbd FOREIGN KEY (sitepermission_id) REFERENCES core_sitepermission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: style_id_refs_page_ptr_id_934fbf43; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_resources_renderedlayer_styles
    ADD CONSTRAINT style_id_refs_page_ptr_id_934fbf43 FOREIGN KEY (style_id) REFERENCES ga_resources_style(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: to_blogpost_id_refs_id_6404941b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost_related_posts
    ADD CONSTRAINT to_blogpost_id_refs_id_6404941b FOREIGN KEY (to_blogpost_id) REFERENCES blog_blogpost(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_01a962b8; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY blog_blogpost
    ADD CONSTRAINT user_id_refs_id_01a962b8 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_9436ba96; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_rating
    ADD CONSTRAINT user_id_refs_id_9436ba96 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_ba84458b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_groups
    ADD CONSTRAINT user_id_refs_id_ba84458b FOREIGN KEY (group_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: worker_id_refs_id_6fd8ce95; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY djcelery_taskstate
    ADD CONSTRAINT worker_id_refs_id_6fd8ce95 FOREIGN KEY (worker_id) REFERENCES djcelery_workerstate(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

