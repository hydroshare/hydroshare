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
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_users DROP CONSTRAINT user_id_refs_id_e7c0ddff;
ALTER TABLE ONLY public.hs_core_genericresource_edit_groups DROP CONSTRAINT user_id_refs_id_ba84458b;
ALTER TABLE ONLY public.core_sitepermission DROP CONSTRAINT user_id_refs_id_b319fa2a;
ALTER TABLE ONLY public.theme_userprofile DROP CONSTRAINT user_id_refs_id_b13e9651;
ALTER TABLE ONLY public.hs_core_genericresource_owners DROP CONSTRAINT user_id_refs_id_ae3696a7;
ALTER TABLE ONLY public.tastypie_apikey DROP CONSTRAINT user_id_refs_id_990aee10;
ALTER TABLE ONLY public.generic_rating DROP CONSTRAINT user_id_refs_id_9436ba96;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_owners DROP CONSTRAINT user_id_refs_id_8d852095;
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT user_id_refs_id_7e75022f;
ALTER TABLE ONLY public.django_docker_processes_dockerprocess DROP CONSTRAINT user_id_refs_id_77917a71;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT user_id_refs_id_4dc23c39;
ALTER TABLE ONLY public.hs_core_genericresource_edit_users DROP CONSTRAINT user_id_refs_id_4876f3f8;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT user_id_refs_id_40c41112;
ALTER TABLE ONLY public.hs_core_genericresource_view_users DROP CONSTRAINT user_id_refs_id_13f09379;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_users DROP CONSTRAINT user_id_refs_id_0326e167;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource DROP CONSTRAINT user_id_refs_id_01f3936e;
ALTER TABLE ONLY public.blog_blogpost DROP CONSTRAINT user_id_refs_id_01a962b8;
ALTER TABLE ONLY public.blog_blogpost_related_posts DROP CONSTRAINT to_blogpost_id_refs_id_6404941b;
ALTER TABLE ONLY public.ga_resources_renderedlayer_styles DROP CONSTRAINT style_id_refs_page_ptr_id_934fbf43;
ALTER TABLE ONLY public.core_sitepermission_sites DROP CONSTRAINT sitepermission_id_refs_id_7dccdcbd;
ALTER TABLE ONLY public.generic_keyword DROP CONSTRAINT site_id_refs_id_f6393455;
ALTER TABLE ONLY public.blog_blogpost DROP CONSTRAINT site_id_refs_id_ac21095f;
ALTER TABLE ONLY public.blog_blogcategory DROP CONSTRAINT site_id_refs_id_93afc60f;
ALTER TABLE ONLY public.core_sitepermission_sites DROP CONSTRAINT site_id_refs_id_91a6d9d4;
ALTER TABLE ONLY public.theme_siteconfiguration DROP CONSTRAINT site_id_refs_id_8ee83179;
ALTER TABLE ONLY public.pages_page DROP CONSTRAINT site_id_refs_id_70c9ac77;
ALTER TABLE ONLY public.django_redirect DROP CONSTRAINT site_id_refs_id_390e2add;
ALTER TABLE ONLY public.conf_setting DROP CONSTRAINT site_id_refs_id_29e7e142;
ALTER TABLE ONLY public.ga_resources_orderedresource DROP CONSTRAINT resource_group_id_refs_page_ptr_id_9dce21a0;
ALTER TABLE ONLY public.generic_threadedcomment DROP CONSTRAINT replied_to_id_refs_comment_ptr_id_83bd8e31;
ALTER TABLE ONLY public.ga_resources_renderedlayer_styles DROP CONSTRAINT renderedlayer_id_refs_page_ptr_id_7bc3ed6b;
ALTER TABLE ONLY public.dublincore_qualifieddublincoreelementhistory DROP CONSTRAINT qdce_id_refs_id_7eb27ec4;
ALTER TABLE ONLY public.django_docker_processes_dockerprocess DROP CONSTRAINT profile_id_refs_id_dfb05146;
ALTER TABLE ONLY public.pages_page DROP CONSTRAINT parent_id_refs_id_68963b8e;
ALTER TABLE ONLY public.forms_form DROP CONSTRAINT page_ptr_id_refs_id_fe19b67b;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT page_ptr_id_refs_id_f73583c5;
ALTER TABLE ONLY public.theme_homepage DROP CONSTRAINT page_ptr_id_refs_id_bf381bd5;
ALTER TABLE ONLY public.ga_resources_style DROP CONSTRAINT page_ptr_id_refs_id_ae3b1c29;
ALTER TABLE ONLY public.ga_resources_catalogpage DROP CONSTRAINT page_ptr_id_refs_id_a8ba09aa;
ALTER TABLE ONLY public.ga_resources_resourcegroup DROP CONSTRAINT page_ptr_id_refs_id_93df8296;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource DROP CONSTRAINT page_ptr_id_refs_id_8aa2112f;
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
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT last_changed_by_id_refs_id_7e75022f;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource DROP CONSTRAINT last_changed_by_id_refs_id_01f3936e;
ALTER TABLE ONLY public.generic_assignedkeyword DROP CONSTRAINT keyword_id_refs_id_aa70ce50;
ALTER TABLE ONLY public.djcelery_periodictask DROP CONSTRAINT interval_id_refs_id_1829f358;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_users DROP CONSTRAINT instresource_id_refs_page_ptr_id_f104c81a;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_groups DROP CONSTRAINT instresource_id_refs_page_ptr_id_d4cb5d6d;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_owners DROP CONSTRAINT instresource_id_refs_page_ptr_id_b67c9746;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_users DROP CONSTRAINT instresource_id_refs_page_ptr_id_a88be7c5;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_groups DROP CONSTRAINT instresource_id_refs_page_ptr_id_9e592426;
ALTER TABLE ONLY public.theme_iconbox DROP CONSTRAINT homepage_id_refs_page_ptr_id_f766bdfd;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT group_id_refs_id_f4b32aac;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_groups DROP CONSTRAINT group_id_refs_id_eafd3ff4;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_groups DROP CONSTRAINT group_id_refs_id_c1faeb19;
ALTER TABLE ONLY public.hs_core_genericresource_view_groups DROP CONSTRAINT group_id_refs_id_2bf6790f;
ALTER TABLE ONLY public.hs_core_groupownership DROP CONSTRAINT group_id_refs_id_07cb9889;
ALTER TABLE ONLY public.hs_core_genericresource_owners DROP CONSTRAINT genericresource_id_refs_page_ptr_id_f3be5566;
ALTER TABLE ONLY public.hs_core_genericresource_view_users DROP CONSTRAINT genericresource_id_refs_page_ptr_id_8ba7d05f;
ALTER TABLE ONLY public.hs_core_genericresource_edit_users DROP CONSTRAINT genericresource_id_refs_page_ptr_id_2d0a4979;
ALTER TABLE ONLY public.hs_core_genericresource_view_groups DROP CONSTRAINT genericresource_id_refs_page_ptr_id_1b325f2a;
ALTER TABLE ONLY public.hs_core_genericresource_edit_groups DROP CONSTRAINT genericresource_id_refs_page_ptr_id_063888a3;
ALTER TABLE ONLY public.galleries_galleryimage DROP CONSTRAINT gallery_id_refs_page_ptr_id_d6457fc6;
ALTER TABLE ONLY public.ga_ows_ogrlayer DROP CONSTRAINT ga_ows_ogrlayer_dataset_id_fkey;
ALTER TABLE ONLY public.ga_ows_ogrdataset DROP CONSTRAINT ga_ows_ogrdataset_collection_id_fkey;
ALTER TABLE ONLY public.blog_blogpost_related_posts DROP CONSTRAINT from_blogpost_id_refs_id_6404941b;
ALTER TABLE ONLY public.forms_field DROP CONSTRAINT form_id_refs_page_ptr_id_5a752766;
ALTER TABLE ONLY public.forms_formentry DROP CONSTRAINT form_id_refs_page_ptr_id_4d605921;
ALTER TABLE ONLY public.ga_resources_relatedresource DROP CONSTRAINT foreign_resource_id_refs_page_ptr_id_f3121e9c;
ALTER TABLE ONLY public.forms_fieldentry DROP CONSTRAINT entry_id_refs_id_e329b086;
ALTER TABLE ONLY public.django_docker_processes_dockervolume DROP CONSTRAINT docker_profile_id_refs_id_c613f9db;
ALTER TABLE ONLY public.django_docker_processes_dockerenvvar DROP CONSTRAINT docker_profile_id_refs_id_bcaa597c;
ALTER TABLE ONLY public.django_docker_processes_containeroverrides DROP CONSTRAINT docker_profile_id_refs_id_a60496a5;
ALTER TABLE ONLY public.django_docker_processes_dockerport DROP CONSTRAINT docker_profile_id_refs_id_7f4076c3;
ALTER TABLE ONLY public.django_docker_processes_dockerlink DROP CONSTRAINT docker_profile_id_refs_id_0a9ee02d;
ALTER TABLE ONLY public.django_docker_processes_overridelink DROP CONSTRAINT docker_profile_from_id_refs_id_e64bf6f2;
ALTER TABLE ONLY public.django_docker_processes_dockerlink DROP CONSTRAINT docker_profile_from_id_refs_id_0a9ee02d;
ALTER TABLE ONLY public.django_docker_processes_dockerlink DROP CONSTRAINT docker_overrides_id_refs_id_f4fdaf84;
ALTER TABLE ONLY public.django_irods_rodsenvironment DROP CONSTRAINT django_irods_rodsenvironment_owner_id_fkey;
ALTER TABLE ONLY public.django_comments DROP CONSTRAINT django_comments_user_id_fkey;
ALTER TABLE ONLY public.django_comments DROP CONSTRAINT django_comments_site_id_fkey;
ALTER TABLE ONLY public.django_comments DROP CONSTRAINT django_comments_content_type_id_fkey;
ALTER TABLE ONLY public.django_comment_flags DROP CONSTRAINT django_comment_flags_user_id_fkey;
ALTER TABLE ONLY public.django_comment_flags DROP CONSTRAINT django_comment_flags_comment_id_fkey;
ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_user_id_fkey;
ALTER TABLE ONLY public.django_admin_log DROP CONSTRAINT django_admin_log_content_type_id_fkey;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT default_style_id_refs_page_ptr_id_1538365b;
ALTER TABLE ONLY public.ga_resources_renderedlayer DROP CONSTRAINT data_resource_id_refs_page_ptr_id_e2b8544b;
ALTER TABLE ONLY public.ga_resources_orderedresource DROP CONSTRAINT data_resource_id_refs_page_ptr_id_a59a4665;
ALTER TABLE ONLY public.djcelery_periodictask DROP CONSTRAINT crontab_id_refs_id_286da0d1;
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT creator_id_refs_id_7e75022f;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource DROP CONSTRAINT creator_id_refs_id_01f3936e;
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
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource DROP CONSTRAINT content_type_id_refs_id_27cd1620;
ALTER TABLE ONLY public.generic_rating DROP CONSTRAINT content_type_id_refs_id_1c638e93;
ALTER TABLE ONLY public.hs_core_language DROP CONSTRAINT content_type_id_refs_id_14a23aea;
ALTER TABLE ONLY public.hs_core_type DROP CONSTRAINT content_type_id_refs_id_0f7fd1d0;
ALTER TABLE ONLY public.hs_core_subject DROP CONSTRAINT content_type_id_refs_id_0dbe97eb;
ALTER TABLE ONLY public.hs_core_genericresource DROP CONSTRAINT content_type_id_refs_id_07d4acf0;
ALTER TABLE ONLY public.hs_core_publisher DROP CONSTRAINT content_type_id_refs_id_016474ea;
ALTER TABLE ONLY public.django_docker_processes_overrideport DROP CONSTRAINT container_overrides_id_refs_id_ef853568;
ALTER TABLE ONLY public.django_docker_processes_overridelink DROP CONSTRAINT container_overrides_id_refs_id_92d17cd7;
ALTER TABLE ONLY public.django_docker_processes_overridevolume DROP CONSTRAINT container_overrides_id_refs_id_78c1f902;
ALTER TABLE ONLY public.django_docker_processes_overrideenvvar DROP CONSTRAINT container_overrides_id_refs_id_510a839c;
ALTER TABLE ONLY public.generic_threadedcomment DROP CONSTRAINT comment_ptr_id_refs_id_d4c241e5;
ALTER TABLE ONLY public.blog_blogpost_categories DROP CONSTRAINT blogpost_id_refs_id_6a2ad936;
ALTER TABLE ONLY public.blog_blogpost_categories DROP CONSTRAINT blogcategory_id_refs_id_91693b1c;
ALTER TABLE ONLY public.auth_user_user_permissions DROP CONSTRAINT auth_user_user_permissions_permission_id_fkey;
ALTER TABLE ONLY public.auth_user_groups DROP CONSTRAINT auth_user_groups_group_id_fkey;
ALTER TABLE ONLY public.auth_group_permissions DROP CONSTRAINT auth_group_permissions_permission_id_fkey;
DROP INDEX public.theme_siteconfiguration_site_id;
DROP INDEX public.theme_iconbox_homepage_id;
DROP INDEX public.tastypie_apikey_key;
DROP INDEX public.pages_page_site_id;
DROP INDEX public.pages_page_parent_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_view_users_user_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_view_users_instresour6b12;
DROP INDEX public.hs_rhessys_inst_resource_instresource_view_groups_instresou980b;
DROP INDEX public.hs_rhessys_inst_resource_instresource_view_groups_group_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_user_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_short_id_like;
DROP INDEX public.hs_rhessys_inst_resource_instresource_short_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_owners_user_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_owners_instresource_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_last_changed_by_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_edit_users_user_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_edit_users_instresour6ff4;
DROP INDEX public.hs_rhessys_inst_resource_instresource_edit_groups_instresou1d45;
DROP INDEX public.hs_rhessys_inst_resource_instresource_edit_groups_group_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_doi_like;
DROP INDEX public.hs_rhessys_inst_resource_instresource_doi;
DROP INDEX public.hs_rhessys_inst_resource_instresource_creator_id;
DROP INDEX public.hs_rhessys_inst_resource_instresource_content_type_id;
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
DROP INDEX public.ga_ows_ogrlayer_name_like;
DROP INDEX public.ga_ows_ogrlayer_name;
DROP INDEX public.ga_ows_ogrlayer_human_name_like;
DROP INDEX public.ga_ows_ogrlayer_human_name;
DROP INDEX public.ga_ows_ogrlayer_extent_id;
DROP INDEX public.ga_ows_ogrlayer_dataset_id;
DROP INDEX public.ga_ows_ogrdataset_name_like;
DROP INDEX public.ga_ows_ogrdataset_name;
DROP INDEX public.ga_ows_ogrdataset_human_name_like;
DROP INDEX public.ga_ows_ogrdataset_human_name;
DROP INDEX public.ga_ows_ogrdataset_extent_id;
DROP INDEX public.ga_ows_ogrdataset_collection_id;
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
DROP INDEX public.django_docker_processes_overridevolume_container_overrides_id;
DROP INDEX public.django_docker_processes_overrideport_container_overrides_id;
DROP INDEX public.django_docker_processes_overridelink_docker_profile_from_id;
DROP INDEX public.django_docker_processes_overridelink_container_overrides_id;
DROP INDEX public.django_docker_processes_overrideenvvar_container_overrides_id;
DROP INDEX public.django_docker_processes_dockervolume_docker_profile_id;
DROP INDEX public.django_docker_processes_dockerprofile_name_like;
DROP INDEX public.django_docker_processes_dockerprocess_user_id;
DROP INDEX public.django_docker_processes_dockerprocess_token_like;
DROP INDEX public.django_docker_processes_dockerprocess_profile_id;
DROP INDEX public.django_docker_processes_dockerport_docker_profile_id;
DROP INDEX public.django_docker_processes_dockerlink_docker_profile_id;
DROP INDEX public.django_docker_processes_dockerlink_docker_profile_from_id;
DROP INDEX public.django_docker_processes_dockerlink_docker_overrides_id;
DROP INDEX public.django_docker_processes_dockerenvvar_docker_profile_id;
DROP INDEX public.django_docker_processes_containeroverrides_docker_profile_id;
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
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_users DROP CONSTRAINT hs_rhessys_inst_resource_instresource_view_users_pkey;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_groups DROP CONSTRAINT hs_rhessys_inst_resource_instresource_view_groups_pkey;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource DROP CONSTRAINT hs_rhessys_inst_resource_instresource_pkey;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_owners DROP CONSTRAINT hs_rhessys_inst_resource_instresource_owners_pkey;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_users DROP CONSTRAINT hs_rhessys_inst_resource_instresource_edit_users_pkey;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_groups DROP CONSTRAINT hs_rhessys_inst_resource_instresource_edit_groups_pkey;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_groups DROP CONSTRAINT hs_rhessys_inst_resource_i_instresource_id_7a81bdda38a7864_uniq;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_users DROP CONSTRAINT hs_rhessys_inst_resource__instresource_id_628be0f6ac14948d_uniq;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_view_users DROP CONSTRAINT hs_rhessys_inst_resource__instresource_id_55a671d29d314ba2_uniq;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_edit_groups DROP CONSTRAINT hs_rhessys_inst_resource__instresource_id_45fd306dda50ac33_uniq;
ALTER TABLE ONLY public.hs_rhessys_inst_resource_instresource_owners DROP CONSTRAINT hs_rhessys_inst_resource__instresource_id_23958bb64d02c7e0_uniq;
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
ALTER TABLE ONLY public.ga_ows_ogrlayer DROP CONSTRAINT ga_ows_ogrlayer_pkey;
ALTER TABLE ONLY public.ga_ows_ogrdatasetcollection DROP CONSTRAINT ga_ows_ogrdatasetcollection_pkey;
ALTER TABLE ONLY public.ga_ows_ogrdataset DROP CONSTRAINT ga_ows_ogrdataset_pkey;
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
ALTER TABLE ONLY public.django_migrations DROP CONSTRAINT django_migrations_pkey;
ALTER TABLE ONLY public.django_irods_rodsenvironment DROP CONSTRAINT django_irods_rodsenvironment_pkey;
ALTER TABLE ONLY public.django_docker_processes_overridevolume DROP CONSTRAINT django_docker_processes_overridevolume_pkey;
ALTER TABLE ONLY public.django_docker_processes_overrideport DROP CONSTRAINT django_docker_processes_overrideport_pkey;
ALTER TABLE ONLY public.django_docker_processes_overridelink DROP CONSTRAINT django_docker_processes_overridelink_pkey;
ALTER TABLE ONLY public.django_docker_processes_overrideenvvar DROP CONSTRAINT django_docker_processes_overrideenvvar_pkey;
ALTER TABLE ONLY public.django_docker_processes_dockervolume DROP CONSTRAINT django_docker_processes_dockervolume_pkey;
ALTER TABLE ONLY public.django_docker_processes_dockerprofile DROP CONSTRAINT django_docker_processes_dockerprofile_pkey;
ALTER TABLE ONLY public.django_docker_processes_dockerprofile DROP CONSTRAINT django_docker_processes_dockerprofile_name_key;
ALTER TABLE ONLY public.django_docker_processes_dockerprocess DROP CONSTRAINT django_docker_processes_dockerprocess_token_key;
ALTER TABLE ONLY public.django_docker_processes_dockerprocess DROP CONSTRAINT django_docker_processes_dockerprocess_pkey;
ALTER TABLE ONLY public.django_docker_processes_dockerport DROP CONSTRAINT django_docker_processes_dockerport_pkey;
ALTER TABLE ONLY public.django_docker_processes_dockerlink DROP CONSTRAINT django_docker_processes_dockerlink_pkey;
ALTER TABLE ONLY public.django_docker_processes_dockerenvvar DROP CONSTRAINT django_docker_processes_dockerenvvar_pkey;
ALTER TABLE ONLY public.django_docker_processes_containeroverrides DROP CONSTRAINT django_docker_processes_containeroverrides_pkey;
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
ALTER TABLE public.hs_rhessys_inst_resource_instresource_view_users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_rhessys_inst_resource_instresource_view_groups ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_rhessys_inst_resource_instresource_owners ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_rhessys_inst_resource_instresource_edit_users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.hs_rhessys_inst_resource_instresource_edit_groups ALTER COLUMN id DROP DEFAULT;
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
ALTER TABLE public.ga_ows_ogrlayer ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.ga_ows_ogrdatasetcollection ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.ga_ows_ogrdataset ALTER COLUMN id DROP DEFAULT;
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
ALTER TABLE public.django_migrations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_irods_rodsenvironment ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_overridevolume ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_overrideport ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_overridelink ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_overrideenvvar ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_dockervolume ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_dockerprofile ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_dockerprocess ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_dockerport ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_dockerlink ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_dockerenvvar ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.django_docker_processes_containeroverrides ALTER COLUMN id DROP DEFAULT;
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
DROP SEQUENCE public.hs_rhessys_inst_resource_instresource_view_users_id_seq;
DROP TABLE public.hs_rhessys_inst_resource_instresource_view_users;
DROP SEQUENCE public.hs_rhessys_inst_resource_instresource_view_groups_id_seq;
DROP TABLE public.hs_rhessys_inst_resource_instresource_view_groups;
DROP SEQUENCE public.hs_rhessys_inst_resource_instresource_owners_id_seq;
DROP TABLE public.hs_rhessys_inst_resource_instresource_owners;
DROP SEQUENCE public.hs_rhessys_inst_resource_instresource_edit_users_id_seq;
DROP TABLE public.hs_rhessys_inst_resource_instresource_edit_users;
DROP SEQUENCE public.hs_rhessys_inst_resource_instresource_edit_groups_id_seq;
DROP TABLE public.hs_rhessys_inst_resource_instresource_edit_groups;
DROP TABLE public.hs_rhessys_inst_resource_instresource;
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
DROP SEQUENCE public.ga_ows_ogrlayer_id_seq;
DROP TABLE public.ga_ows_ogrlayer;
DROP SEQUENCE public.ga_ows_ogrdatasetcollection_id_seq;
DROP TABLE public.ga_ows_ogrdatasetcollection;
DROP SEQUENCE public.ga_ows_ogrdataset_id_seq;
DROP TABLE public.ga_ows_ogrdataset;
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
DROP SEQUENCE public.django_migrations_id_seq;
DROP TABLE public.django_migrations;
DROP SEQUENCE public.django_irods_rodsenvironment_id_seq;
DROP TABLE public.django_irods_rodsenvironment;
DROP SEQUENCE public.django_docker_processes_overridevolume_id_seq;
DROP TABLE public.django_docker_processes_overridevolume;
DROP SEQUENCE public.django_docker_processes_overrideport_id_seq;
DROP TABLE public.django_docker_processes_overrideport;
DROP SEQUENCE public.django_docker_processes_overridelink_id_seq;
DROP TABLE public.django_docker_processes_overridelink;
DROP SEQUENCE public.django_docker_processes_overrideenvvar_id_seq;
DROP TABLE public.django_docker_processes_overrideenvvar;
DROP SEQUENCE public.django_docker_processes_dockervolume_id_seq;
DROP TABLE public.django_docker_processes_dockervolume;
DROP SEQUENCE public.django_docker_processes_dockerprofile_id_seq;
DROP TABLE public.django_docker_processes_dockerprofile;
DROP SEQUENCE public.django_docker_processes_dockerprocess_id_seq;
DROP TABLE public.django_docker_processes_dockerprocess;
DROP SEQUENCE public.django_docker_processes_dockerport_id_seq;
DROP TABLE public.django_docker_processes_dockerport;
DROP SEQUENCE public.django_docker_processes_dockerlink_id_seq;
DROP TABLE public.django_docker_processes_dockerlink;
DROP SEQUENCE public.django_docker_processes_dockerenvvar_id_seq;
DROP TABLE public.django_docker_processes_dockerenvvar;
DROP SEQUENCE public.django_docker_processes_containeroverrides_id_seq;
DROP TABLE public.django_docker_processes_containeroverrides;
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
-- Name: django_docker_processes_containeroverrides; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_containeroverrides (
    id integer NOT NULL,
    docker_profile_id integer NOT NULL,
    name character varying(256) NOT NULL,
    command text,
    working_dir character varying(65536),
    "user" character varying(65536),
    entrypoint character varying(65536),
    privileged boolean NOT NULL,
    lxc_conf character varying(65536),
    memory_limit integer NOT NULL,
    cpu_shares integer,
    dns text,
    net character varying(8)
);


ALTER TABLE public.django_docker_processes_containeroverrides OWNER TO postgres;

--
-- Name: django_docker_processes_containeroverrides_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_containeroverrides_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_containeroverrides_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_containeroverrides_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_containeroverrides_id_seq OWNED BY django_docker_processes_containeroverrides.id;


--
-- Name: django_docker_processes_dockerenvvar; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_dockerenvvar (
    id integer NOT NULL,
    docker_profile_id integer NOT NULL,
    name character varying(1024) NOT NULL,
    value text NOT NULL
);


ALTER TABLE public.django_docker_processes_dockerenvvar OWNER TO postgres;

--
-- Name: django_docker_processes_dockerenvvar_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_dockerenvvar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_dockerenvvar_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_dockerenvvar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_dockerenvvar_id_seq OWNED BY django_docker_processes_dockerenvvar.id;


--
-- Name: django_docker_processes_dockerlink; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_dockerlink (
    id integer NOT NULL,
    docker_profile_id integer NOT NULL,
    link_name character varying(256) NOT NULL,
    docker_profile_from_id integer NOT NULL,
    docker_overrides_id integer
);


ALTER TABLE public.django_docker_processes_dockerlink OWNER TO postgres;

--
-- Name: django_docker_processes_dockerlink_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_dockerlink_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_dockerlink_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_dockerlink_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_dockerlink_id_seq OWNED BY django_docker_processes_dockerlink.id;


--
-- Name: django_docker_processes_dockerport; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_dockerport (
    id integer NOT NULL,
    docker_profile_id integer NOT NULL,
    host character varying(65536) NOT NULL,
    container character varying(65536) NOT NULL
);


ALTER TABLE public.django_docker_processes_dockerport OWNER TO postgres;

--
-- Name: django_docker_processes_dockerport_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_dockerport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_dockerport_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_dockerport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_dockerport_id_seq OWNED BY django_docker_processes_dockerport.id;


--
-- Name: django_docker_processes_dockerprocess; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_dockerprocess (
    id integer NOT NULL,
    profile_id integer NOT NULL,
    container_id character varying(128),
    token character varying(128) NOT NULL,
    logs text,
    finished boolean NOT NULL,
    error boolean NOT NULL,
    user_id integer
);


ALTER TABLE public.django_docker_processes_dockerprocess OWNER TO postgres;

--
-- Name: django_docker_processes_dockerprocess_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_dockerprocess_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_dockerprocess_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_dockerprocess_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_dockerprocess_id_seq OWNED BY django_docker_processes_dockerprocess.id;


--
-- Name: django_docker_processes_dockerprofile; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_dockerprofile (
    id integer NOT NULL,
    name character varying(1024) NOT NULL,
    git_repository character varying(16384) NOT NULL,
    git_use_submodules boolean NOT NULL,
    git_username character varying(256),
    git_password character varying(64),
    commit_id character varying(64),
    branch character varying(1024)
);


ALTER TABLE public.django_docker_processes_dockerprofile OWNER TO postgres;

--
-- Name: django_docker_processes_dockerprofile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_dockerprofile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_dockerprofile_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_dockerprofile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_dockerprofile_id_seq OWNED BY django_docker_processes_dockerprofile.id;


--
-- Name: django_docker_processes_dockervolume; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_dockervolume (
    id integer NOT NULL,
    docker_profile_id integer NOT NULL,
    host character varying(65536),
    container character varying(65536) NOT NULL,
    readonly boolean NOT NULL
);


ALTER TABLE public.django_docker_processes_dockervolume OWNER TO postgres;

--
-- Name: django_docker_processes_dockervolume_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_dockervolume_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_dockervolume_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_dockervolume_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_dockervolume_id_seq OWNED BY django_docker_processes_dockervolume.id;


--
-- Name: django_docker_processes_overrideenvvar; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_overrideenvvar (
    id integer NOT NULL,
    container_overrides_id integer NOT NULL,
    name character varying(1024) NOT NULL,
    value text NOT NULL
);


ALTER TABLE public.django_docker_processes_overrideenvvar OWNER TO postgres;

--
-- Name: django_docker_processes_overrideenvvar_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_overrideenvvar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_overrideenvvar_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_overrideenvvar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_overrideenvvar_id_seq OWNED BY django_docker_processes_overrideenvvar.id;


--
-- Name: django_docker_processes_overridelink; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_overridelink (
    id integer NOT NULL,
    container_overrides_id integer NOT NULL,
    link_name character varying(256) NOT NULL,
    docker_profile_from_id integer NOT NULL
);


ALTER TABLE public.django_docker_processes_overridelink OWNER TO postgres;

--
-- Name: django_docker_processes_overridelink_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_overridelink_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_overridelink_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_overridelink_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_overridelink_id_seq OWNED BY django_docker_processes_overridelink.id;


--
-- Name: django_docker_processes_overrideport; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_overrideport (
    id integer NOT NULL,
    container_overrides_id integer NOT NULL,
    host character varying(65536) NOT NULL,
    container character varying(65536) NOT NULL
);


ALTER TABLE public.django_docker_processes_overrideport OWNER TO postgres;

--
-- Name: django_docker_processes_overrideport_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_overrideport_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_overrideport_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_overrideport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_overrideport_id_seq OWNED BY django_docker_processes_overrideport.id;


--
-- Name: django_docker_processes_overridevolume; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_docker_processes_overridevolume (
    id integer NOT NULL,
    container_overrides_id integer NOT NULL,
    host character varying(65536) NOT NULL,
    container character varying(65536) NOT NULL
);


ALTER TABLE public.django_docker_processes_overridevolume OWNER TO postgres;

--
-- Name: django_docker_processes_overridevolume_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_docker_processes_overridevolume_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_docker_processes_overridevolume_id_seq OWNER TO postgres;

--
-- Name: django_docker_processes_overridevolume_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_docker_processes_overridevolume_id_seq OWNED BY django_docker_processes_overridevolume.id;


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
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_migrations_id_seq OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_migrations_id_seq OWNED BY django_migrations.id;


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
-- Name: ga_ows_ogrdataset; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_ows_ogrdataset (
    id integer NOT NULL,
    collection_id integer NOT NULL,
    location text NOT NULL,
    checksum character varying(32) NOT NULL,
    name character varying(255) NOT NULL,
    human_name text,
    extent geometry(Polygon,4326) NOT NULL
);


ALTER TABLE public.ga_ows_ogrdataset OWNER TO postgres;

--
-- Name: ga_ows_ogrdataset_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ga_ows_ogrdataset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ga_ows_ogrdataset_id_seq OWNER TO postgres;

--
-- Name: ga_ows_ogrdataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ga_ows_ogrdataset_id_seq OWNED BY ga_ows_ogrdataset.id;


--
-- Name: ga_ows_ogrdatasetcollection; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_ows_ogrdatasetcollection (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE public.ga_ows_ogrdatasetcollection OWNER TO postgres;

--
-- Name: ga_ows_ogrdatasetcollection_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ga_ows_ogrdatasetcollection_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ga_ows_ogrdatasetcollection_id_seq OWNER TO postgres;

--
-- Name: ga_ows_ogrdatasetcollection_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ga_ows_ogrdatasetcollection_id_seq OWNED BY ga_ows_ogrdatasetcollection.id;


--
-- Name: ga_ows_ogrlayer; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ga_ows_ogrlayer (
    id integer NOT NULL,
    dataset_id integer NOT NULL,
    name character varying(255) NOT NULL,
    human_name text,
    extent geometry(Polygon,4326) NOT NULL
);


ALTER TABLE public.ga_ows_ogrlayer OWNER TO postgres;

--
-- Name: ga_ows_ogrlayer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE ga_ows_ogrlayer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ga_ows_ogrlayer_id_seq OWNER TO postgres;

--
-- Name: ga_ows_ogrlayer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE ga_ows_ogrlayer_id_seq OWNED BY ga_ows_ogrlayer.id;


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
    bag character varying(500),
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
    abstract text NOT NULL,
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
    resource_file character varying(500) NOT NULL,
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
-- Name: hs_rhessys_inst_resource_instresource; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_rhessys_inst_resource_instresource (
    page_ptr_id integer NOT NULL,
    comments_count integer NOT NULL,
    content text NOT NULL,
    user_id integer NOT NULL,
    creator_id integer NOT NULL,
    public boolean NOT NULL,
    frozen boolean NOT NULL,
    do_not_distribute boolean NOT NULL,
    discoverable boolean NOT NULL,
    published_and_frozen boolean NOT NULL,
    last_changed_by_id integer,
    short_id character varying(32) NOT NULL,
    doi character varying(1024),
    name character varying(50) NOT NULL,
    git_repo character varying(200) NOT NULL,
    git_username character varying(50) NOT NULL,
    git_password character varying(50) NOT NULL,
    commit_id character varying(50) NOT NULL,
    model_desc character varying(500) NOT NULL,
    git_branch character varying(50) NOT NULL,
    study_area_bbox character varying(50) NOT NULL,
    model_command_line_parameters character varying(500) NOT NULL,
    project_name character varying(100) NOT NULL,
    object_id integer,
    content_type_id integer,
    CONSTRAINT ck_object_id_pstv_545705995d642cef CHECK ((object_id >= 0)),
    CONSTRAINT hs_rhessys_inst_resource_instresource_object_id_check CHECK ((object_id >= 0))
);


ALTER TABLE public.hs_rhessys_inst_resource_instresource OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_rhessys_inst_resource_instresource_edit_groups (
    id integer NOT NULL,
    instresource_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.hs_rhessys_inst_resource_instresource_edit_groups OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_rhessys_inst_resource_instresource_edit_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_rhessys_inst_resource_instresource_edit_groups_id_seq OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_rhessys_inst_resource_instresource_edit_groups_id_seq OWNED BY hs_rhessys_inst_resource_instresource_edit_groups.id;


--
-- Name: hs_rhessys_inst_resource_instresource_edit_users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_rhessys_inst_resource_instresource_edit_users (
    id integer NOT NULL,
    instresource_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.hs_rhessys_inst_resource_instresource_edit_users OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_edit_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_rhessys_inst_resource_instresource_edit_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_rhessys_inst_resource_instresource_edit_users_id_seq OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_edit_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_rhessys_inst_resource_instresource_edit_users_id_seq OWNED BY hs_rhessys_inst_resource_instresource_edit_users.id;


--
-- Name: hs_rhessys_inst_resource_instresource_owners; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_rhessys_inst_resource_instresource_owners (
    id integer NOT NULL,
    instresource_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.hs_rhessys_inst_resource_instresource_owners OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_owners_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_rhessys_inst_resource_instresource_owners_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_rhessys_inst_resource_instresource_owners_id_seq OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_owners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_rhessys_inst_resource_instresource_owners_id_seq OWNED BY hs_rhessys_inst_resource_instresource_owners.id;


--
-- Name: hs_rhessys_inst_resource_instresource_view_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_rhessys_inst_resource_instresource_view_groups (
    id integer NOT NULL,
    instresource_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.hs_rhessys_inst_resource_instresource_view_groups OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_view_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_rhessys_inst_resource_instresource_view_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_rhessys_inst_resource_instresource_view_groups_id_seq OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_view_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_rhessys_inst_resource_instresource_view_groups_id_seq OWNED BY hs_rhessys_inst_resource_instresource_view_groups.id;


--
-- Name: hs_rhessys_inst_resource_instresource_view_users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hs_rhessys_inst_resource_instresource_view_users (
    id integer NOT NULL,
    instresource_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.hs_rhessys_inst_resource_instresource_view_users OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_view_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hs_rhessys_inst_resource_instresource_view_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.hs_rhessys_inst_resource_instresource_view_users_id_seq OWNER TO postgres;

--
-- Name: hs_rhessys_inst_resource_instresource_view_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hs_rhessys_inst_resource_instresource_view_users_id_seq OWNED BY hs_rhessys_inst_resource_instresource_view_users.id;


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

ALTER TABLE ONLY django_docker_processes_containeroverrides ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_containeroverrides_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerenvvar ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_dockerenvvar_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerlink ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_dockerlink_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerport ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_dockerport_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerprocess ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_dockerprocess_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerprofile ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_dockerprofile_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockervolume ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_dockervolume_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overrideenvvar ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_overrideenvvar_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overridelink ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_overridelink_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overrideport ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_overrideport_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overridevolume ALTER COLUMN id SET DEFAULT nextval('django_docker_processes_overridevolume_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_irods_rodsenvironment ALTER COLUMN id SET DEFAULT nextval('django_irods_rodsenvironment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq'::regclass);


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

ALTER TABLE ONLY ga_ows_ogrdataset ALTER COLUMN id SET DEFAULT nextval('ga_ows_ogrdataset_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_ows_ogrdatasetcollection ALTER COLUMN id SET DEFAULT nextval('ga_ows_ogrdatasetcollection_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_ows_ogrlayer ALTER COLUMN id SET DEFAULT nextval('ga_ows_ogrlayer_id_seq'::regclass);


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

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_groups ALTER COLUMN id SET DEFAULT nextval('hs_rhessys_inst_resource_instresource_edit_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_users ALTER COLUMN id SET DEFAULT nextval('hs_rhessys_inst_resource_instresource_edit_users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_owners ALTER COLUMN id SET DEFAULT nextval('hs_rhessys_inst_resource_instresource_owners_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_groups ALTER COLUMN id SET DEFAULT nextval('hs_rhessys_inst_resource_instresource_view_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_users ALTER COLUMN id SET DEFAULT nextval('hs_rhessys_inst_resource_instresource_view_users_id_seq'::regclass);


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
200	1	37
201	1	36
202	1	65
203	1	66
204	1	67
205	1	68
206	1	69
207	1	34
208	1	24
209	1	25
210	1	26
211	1	27
212	1	22
213	1	23
214	1	40
215	1	76
216	1	75
217	1	74
218	1	73
219	1	72
220	1	71
221	1	70
222	1	95
223	1	97
224	1	96
225	1	39
226	1	38
227	1	58
228	1	57
229	1	56
230	1	51
231	1	50
232	1	35
233	1	52
\.


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', 233, true);


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
299	Can add country	100	add_country
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
281	Can add party	94	add_party
282	Can change party	94	change_party
283	Can delete party	94	delete_party
284	Can add address code list	95	add_addresscodelist
285	Can change address code list	95	change_addresscodelist
286	Can delete address code list	95	delete_addresscodelist
287	Can add phone code list	96	add_phonecodelist
288	Can change phone code list	96	change_phonecodelist
289	Can delete phone code list	96	delete_phonecodelist
290	Can add email code list	97	add_emailcodelist
291	Can change email code list	97	change_emailcodelist
292	Can delete email code list	97	delete_emailcodelist
293	Can add city	98	add_city
294	Can change city	98	change_city
295	Can delete city	98	delete_city
296	Can add region	99	add_region
297	Can change region	99	change_region
298	Can delete region	99	delete_region
300	Can change country	100	change_country
301	Can delete country	100	delete_country
302	Can add external identifier code list	101	add_externalidentifiercodelist
303	Can change external identifier code list	101	change_externalidentifiercodelist
304	Can delete external identifier code list	101	delete_externalidentifiercodelist
305	Can add name alias code list	102	add_namealiascodelist
306	Can change name alias code list	102	change_namealiascodelist
307	Can delete name alias code list	102	delete_namealiascodelist
308	Can add person	103	add_person
309	Can change person	103	change_person
310	Can delete person	103	delete_person
311	Can add person email	104	add_personemail
312	Can change person email	104	change_personemail
313	Can delete person email	104	delete_personemail
314	Can add person location	105	add_personlocation
315	Can change person location	105	change_personlocation
316	Can delete person location	105	delete_personlocation
317	Can add person phone	106	add_personphone
318	Can change person phone	106	change_personphone
319	Can delete person phone	106	delete_personphone
320	Can add person external identifier	107	add_personexternalidentifier
321	Can change person external identifier	107	change_personexternalidentifier
322	Can delete person external identifier	107	delete_personexternalidentifier
323	Can add user code list	108	add_usercodelist
324	Can change user code list	108	change_usercodelist
325	Can delete user code list	108	delete_usercodelist
326	Can add other name	109	add_othername
327	Can change other name	109	change_othername
328	Can delete other name	109	delete_othername
329	Can add organization code list	110	add_organizationcodelist
330	Can change organization code list	110	change_organizationcodelist
331	Can delete organization code list	110	delete_organizationcodelist
332	Can add organization	111	add_organization
333	Can change organization	111	change_organization
334	Can delete organization	111	delete_organization
335	Can add organization email	112	add_organizationemail
336	Can change organization email	112	change_organizationemail
337	Can delete organization email	112	delete_organizationemail
338	Can add organization location	113	add_organizationlocation
339	Can change organization location	113	change_organizationlocation
340	Can delete organization location	113	delete_organizationlocation
341	Can add organization phone	114	add_organizationphone
342	Can change organization phone	114	change_organizationphone
343	Can delete organization phone	114	delete_organizationphone
344	Can add organization name	115	add_organizationname
345	Can change organization name	115	change_organizationname
346	Can delete organization name	115	delete_organizationname
347	Can add external org identifier	116	add_externalorgidentifier
348	Can change external org identifier	116	change_externalorgidentifier
349	Can delete external org identifier	116	delete_externalorgidentifier
350	Can add group	117	add_group
351	Can change group	117	change_group
352	Can delete group	117	delete_group
353	Can add organization association	118	add_organizationassociation
354	Can change organization association	118	change_organizationassociation
355	Can delete organization association	118	delete_organizationassociation
356	Can add choice type	119	add_choicetype
357	Can change choice type	119	change_choicetype
358	Can delete choice type	119	delete_choicetype
359	Can add docker profile	120	add_dockerprofile
360	Can change docker profile	120	change_dockerprofile
361	Can delete docker profile	120	delete_dockerprofile
362	Can add container overrides	121	add_containeroverrides
363	Can change container overrides	121	change_containeroverrides
364	Can delete container overrides	121	delete_containeroverrides
365	Can add override env var	122	add_overrideenvvar
366	Can change override env var	122	change_overrideenvvar
367	Can delete override env var	122	delete_overrideenvvar
368	Can add override volume	123	add_overridevolume
369	Can change override volume	123	change_overridevolume
370	Can delete override volume	123	delete_overridevolume
371	Can add override link	124	add_overridelink
372	Can change override link	124	change_overridelink
373	Can delete override link	124	delete_overridelink
374	Can add override port	125	add_overrideport
375	Can change override port	125	change_overrideport
376	Can delete override port	125	delete_overrideport
377	Can add docker link	126	add_dockerlink
378	Can change docker link	126	change_dockerlink
379	Can delete docker link	126	delete_dockerlink
380	Can add docker env var	127	add_dockerenvvar
381	Can change docker env var	127	change_dockerenvvar
382	Can delete docker env var	127	delete_dockerenvvar
383	Can add docker volume	128	add_dockervolume
384	Can change docker volume	128	change_dockervolume
385	Can delete docker volume	128	delete_dockervolume
386	Can add docker port	129	add_dockerport
387	Can change docker port	129	change_dockerport
388	Can delete docker port	129	delete_dockerport
389	Can add docker process	130	add_dockerprocess
390	Can change docker process	130	change_dockerprocess
391	Can delete docker process	130	delete_dockerprocess
392	Can add RHESSys Instance Resource	131	add_instresource
393	Can change RHESSys Instance Resource	131	change_instresource
394	Can delete RHESSys Instance Resource	131	delete_instresource
395	Can add post gis geometry columns	132	add_postgisgeometrycolumns
396	Can change post gis geometry columns	132	change_postgisgeometrycolumns
397	Can delete post gis geometry columns	132	delete_postgisgeometrycolumns
398	Can add post gis spatial ref sys	133	add_postgisspatialrefsys
399	Can change post gis spatial ref sys	133	change_postgisspatialrefsys
400	Can delete post gis spatial ref sys	133	delete_postgisspatialrefsys
401	Can add iRODS Environment	134	add_rodsenvironment
402	Can change iRODS Environment	134	change_rodsenvironment
403	Can delete iRODS Environment	134	delete_rodsenvironment
404	Can add ogr dataset collection	135	add_ogrdatasetcollection
405	Can change ogr dataset collection	135	change_ogrdatasetcollection
406	Can delete ogr dataset collection	135	delete_ogrdatasetcollection
407	Can add ogr dataset	136	add_ogrdataset
408	Can change ogr dataset	136	change_ogrdataset
409	Can delete ogr dataset	136	delete_ogrdataset
410	Can add ogr layer	137	add_ogrlayer
411	Can change ogr layer	137	change_ogrlayer
412	Can delete ogr layer	137	delete_ogrlayer
\.


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_permission_id_seq', 412, true);


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$12000$yo6wShVYEQIT$Et3iysrxfBjq2yfo/ubiuiklUfYglZ1vuDNfPjiR8Fw=	2014-11-20 15:50:23.888713+00	t	admin			example@example.com	t	t	2014-02-04 14:51:59.864755+00
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_user_groups_id_seq', 232, true);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('auth_user_id_seq', 157, true);


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
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
1	UA-54192818-1	GOOGLE_ANALYTICS_ID	1
2	10	SEARCH_PER_PAGE	1
3	5	COMMENTS_NUM_LATEST	1
4		ACCOUNTS_APPROVAL_EMAILS	1
5	1	RICHTEXT_FILTER_LEVEL	1
6	True	COMMENTS_UNAPPROVED_VISIBLE	1
7	An open source content management platform.	SITE_TAGLINE	1
8	True	COMMENTS_REMOVED_VISIBLE	1
9		BITLY_ACCESS_TOKEN	1
10	False	SSL_ENABLED	1
11		AKISMET_API_KEY	1
12	True	COMMENTS_DEFAULT_APPROVED	1
13	5	BLOG_POST_PER_PAGE	1
14		COMMENTS_NOTIFICATION_EMAILS	1
15		COMMENTS_DISQUS_API_PUBLIC_KEY	1
16		COMMENTS_DISQUS_API_SECRET_KEY	1
17	False	COMMENTS_ACCOUNT_REQUIRED	1
18	10	MAX_PAGING_LINKS	1
19	4	TAG_CLOUD_SIZES	1
20		COMMENTS_DISQUS_SHORTNAME	1
21		SSL_FORCE_HOST	1
22	False	RATINGS_ACCOUNT_REQUIRED	1
\.


--
-- Name: conf_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('conf_setting_id_seq', 22, true);


--
-- Data for Name: core_sitepermission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY core_sitepermission (id, user_id) FROM stdin;
\.


--
-- Name: core_sitepermission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('core_sitepermission_id_seq', 137, true);


--
-- Data for Name: core_sitepermission_sites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY core_sitepermission_sites (id, sitepermission_id, site_id) FROM stdin;
\.


--
-- Name: core_sitepermission_sites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('core_sitepermission_sites_id_seq', 137, true);


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_admin_log (id, action_time, user_id, content_type_id, object_id, object_repr, action_flag, change_message) FROM stdin;
863	2014-11-20 15:21:07.280905+00	1	50	1	SiteConfiguration object	2	Changed col3_content and id.
327	2014-11-20 14:58:12.78253+00	1	3	148	Bruce	3	
555	2014-11-20 15:00:52.565854+00	1	3	79	mtlash	3	
227	2014-11-20 14:28:13.437617+00	1	3	148	Bruce	3	
228	2014-11-20 14:28:13.446742+00	1	3	5	Castronova	3	
229	2014-11-20 14:28:13.449736+00	1	3	108	Colinbagley	3	
230	2014-11-20 14:28:13.453886+00	1	3	132	Guyfin	3	
231	2014-11-20 14:28:13.456532+00	1	3	48	LenoraS	3	
232	2014-11-20 14:28:13.459221+00	1	3	151	MeganMallard	3	
233	2014-11-20 14:28:13.46183+00	1	3	49	Swoodward	3	
234	2014-11-20 14:28:13.463924+00	1	3	61	Tim_Whiteaker	3	
235	2014-11-20 14:28:13.465899+00	1	3	146	abhijoey234	3	
236	2014-11-20 14:28:13.469427+00	1	3	136	ablemann	3	
237	2014-11-20 14:28:13.473006+00	1	3	115	acgold_4	3	
238	2014-11-20 14:28:13.476457+00	1	3	144	akebedew	3	
239	2014-11-20 14:28:13.480172+00	1	3	80	akilic	3	
240	2014-11-20 14:28:13.482526+00	1	3	129	alan_d_snow	3	
241	2014-11-20 14:28:13.486004+00	1	3	118	amabdallah	3	
242	2014-11-20 14:28:13.488528+00	1	3	87	apadmana	3	
243	2014-11-20 14:28:13.491623+00	1	3	15	ashsemien	3	
244	2014-11-20 14:28:13.494266+00	1	3	140	asouid	3	
245	2014-11-20 14:28:13.496891+00	1	3	71	aufdenkampe	3	
246	2014-11-20 14:28:13.500931+00	1	3	55	bartnijssen	3	
247	2014-11-20 14:28:13.504785+00	1	3	152	bdame	3	
248	2014-11-20 14:28:13.509487+00	1	3	74	beighley	3	
249	2014-11-20 14:28:13.512619+00	1	3	141	bjacobson	3	
250	2014-11-20 14:28:13.514933+00	1	3	109	blmartin	3	
251	2014-11-20 14:28:13.518721+00	1	3	130	brynstclair	3	
252	2014-11-20 14:28:13.520742+00	1	3	75	bwemple	3	
253	2014-11-20 14:28:13.522811+00	1	3	66	caitlinfeehan	3	
254	2014-11-20 14:28:13.5257+00	1	3	138	carolineloop	3	
255	2014-11-20 14:28:13.529034+00	1	3	8	carolxsong	3	
256	2014-11-20 14:28:13.534264+00	1	3	63	cas214	3	
257	2014-11-20 14:28:13.536387+00	1	3	64	cband	3	
258	2014-11-20 14:28:13.538407+00	1	3	154	chhandana	3	
259	2014-11-20 14:28:13.540589+00	1	3	89	chmuibk	3	
260	2014-11-20 14:28:13.547684+00	1	3	69	cjohnsto	3	
261	2014-11-20 14:28:13.55477+00	1	3	103	cjones21	3	
262	2014-11-20 14:28:13.559635+00	1	3	134	crh2pw	3	
263	2014-11-20 14:28:13.56694+00	1	3	4	danames	3	
264	2014-11-20 14:28:13.574845+00	1	3	119	danames2	3	
265	2014-11-20 14:28:13.580607+00	1	3	114	danehurst	3	
266	2014-11-20 14:28:13.588579+00	1	3	145	davidmkey	3	
267	2014-11-20 14:28:13.592331+00	1	3	62	dbtarb	3	
268	2014-11-20 14:28:13.595634+00	1	3	46	demo	3	
269	2014-11-20 14:28:13.60236+00	1	3	107	diet_rich08	3	
270	2014-11-20 14:28:13.60913+00	1	3	111	ditmore	3	
271	2014-11-20 14:28:13.614285+00	1	3	95	donpark	3	
272	2014-11-20 14:28:13.617149+00	1	3	65	drfuka	3	
273	2014-11-20 14:28:13.619173+00	1	3	77	dsmackay	3	
274	2014-11-20 14:28:13.62117+00	1	3	12	dtarb	3	
275	2014-11-20 14:28:13.622964+00	1	3	124	dtarb1	3	
276	2014-11-20 14:28:13.624714+00	1	3	126	dtarb2	3	
277	2014-11-20 14:28:13.628344+00	1	3	102	dtarbrenci	3	
278	2014-11-20 14:28:13.631929+00	1	3	93	dtarbunc	3	
279	2014-11-20 14:28:13.633969+00	1	3	99	dtarbunc1	3	
280	2014-11-20 14:28:13.636421+00	1	3	73	dwilusz1	3	
281	2014-11-20 14:28:13.638301+00	1	3	78	eistan20	3	
282	2014-11-20 14:28:13.640504+00	1	3	85	fanye	3	
283	2014-11-20 14:28:13.642582+00	1	3	104	gaffey	3	
284	2014-11-20 14:28:13.644778+00	1	3	149	garybc	3	
285	2014-11-20 14:28:13.648479+00	1	3	110	henriquepdp	3	
286	2014-11-20 14:28:13.651987+00	1	3	125	hongyi	3	
287	2014-11-20 14:28:13.655462+00	1	3	9	horsburgh	3	
288	2014-11-20 14:28:13.657354+00	1	3	96	hyi	3	
289	2014-11-20 14:28:13.659473+00	1	3	10	jamy	3	
290	2014-11-20 14:28:13.661509+00	1	3	34	jarrigo@cuahsi.org	3	
291	2014-11-20 14:28:13.664012+00	1	3	39	jasonc	3	
292	2014-11-20 14:28:13.66706+00	1	3	91	jching	3	
293	2014-11-20 14:28:13.669816+00	1	3	3	jeff	3	
294	2014-11-20 14:28:13.672004+00	1	3	38	jeffheard	3	
295	2014-11-20 14:28:13.674167+00	1	3	54	jirikadlec2	3	
296	2014-11-20 14:28:13.676197+00	1	3	68	jncole	3	
297	2014-11-20 14:28:13.678794+00	1	3	29	jon_goodall	3	
298	2014-11-20 14:28:13.681053+00	1	3	94	jonglee1	3	
299	2014-11-20 14:28:13.682993+00	1	3	106	jplovette	3	
300	2014-11-20 14:28:13.685893+00	1	3	36	jsadler2	3	
301	2014-11-20 14:28:13.690426+00	1	3	156	jterstriep	3	
302	2014-11-20 14:28:13.693069+00	1	3	76	kkyong77	3	
303	2014-11-20 14:28:13.697131+00	1	3	112	klutton	3	
304	2014-11-20 14:28:13.700959+00	1	3	117	kshparajuli	3	
305	2014-11-20 14:28:13.703106+00	1	3	53	lanzhao	3	
306	2014-11-20 14:28:13.705457+00	1	3	58	lband	3	
307	2014-11-20 14:28:13.709102+00	1	3	32	lisa	3	
308	2014-11-20 14:28:13.712504+00	1	3	121	madelinemerck	3	
309	2014-11-20 14:28:13.715092+00	1	3	133	marklewis	3	
310	2014-11-20 14:28:13.717053+00	1	3	6	martinn	3	
311	2014-11-20 14:28:13.718916+00	1	3	155	matthewturk	3	
312	2014-11-20 14:28:13.720671+00	1	3	150	mesco92	3	
313	2014-11-20 14:28:13.722492+00	1	3	137	mjs	3	
314	2014-11-20 14:28:13.72443+00	1	3	92	mjstealey	3	
315	2014-11-20 14:28:13.726374+00	1	3	120	mleonardo	3	
316	2014-11-20 14:28:13.728661+00	1	3	84	moni	3	
317	2014-11-20 14:28:13.732159+00	1	3	97	moon	3	
318	2014-11-20 14:28:13.734838+00	1	3	33	morsy	3	
319	2014-11-20 14:28:13.737005+00	1	3	59	mr_fnord	3	
320	2014-11-20 14:28:13.738908+00	1	3	82	mrl17	3	
321	2014-11-20 14:28:13.740815+00	1	3	79	mtlash	3	
322	2014-11-20 14:28:13.742635+00	1	3	50	myersjd	3	
323	2014-11-20 14:28:13.744766+00	1	3	142	n8urgrl	3	
324	2014-11-20 14:28:13.746623+00	1	3	116	nolankwood	3	
325	2014-11-20 14:28:13.748563+00	1	3	70	peckhams	3	
326	2014-11-20 14:29:22.340163+00	1	7	1	localhost:8000	2	Changed domain.
328	2014-11-20 14:58:12.790107+00	1	3	5	Castronova	3	
329	2014-11-20 14:58:12.793713+00	1	3	108	Colinbagley	3	
330	2014-11-20 14:58:12.795808+00	1	3	132	Guyfin	3	
331	2014-11-20 14:58:12.798084+00	1	3	48	LenoraS	3	
332	2014-11-20 14:58:12.801376+00	1	3	151	MeganMallard	3	
333	2014-11-20 14:58:12.804906+00	1	3	49	Swoodward	3	
334	2014-11-20 14:58:12.806966+00	1	3	61	Tim_Whiteaker	3	
335	2014-11-20 14:58:12.809022+00	1	3	146	abhijoey234	3	
336	2014-11-20 14:58:12.810857+00	1	3	136	ablemann	3	
337	2014-11-20 14:58:12.81256+00	1	3	115	acgold_4	3	
338	2014-11-20 14:58:12.814514+00	1	3	144	akebedew	3	
339	2014-11-20 14:58:12.816204+00	1	3	80	akilic	3	
340	2014-11-20 14:58:12.8178+00	1	3	129	alan_d_snow	3	
341	2014-11-20 14:58:12.820223+00	1	3	118	amabdallah	3	
342	2014-11-20 14:58:12.822717+00	1	3	87	apadmana	3	
343	2014-11-20 14:58:12.824862+00	1	3	15	ashsemien	3	
344	2014-11-20 14:58:12.826672+00	1	3	140	asouid	3	
345	2014-11-20 14:58:12.830124+00	1	3	71	aufdenkampe	3	
346	2014-11-20 14:58:12.832645+00	1	3	55	bartnijssen	3	
347	2014-11-20 14:58:12.834661+00	1	3	152	bdame	3	
348	2014-11-20 14:58:12.837201+00	1	3	74	beighley	3	
349	2014-11-20 14:58:12.839482+00	1	3	141	bjacobson	3	
350	2014-11-20 14:58:12.84171+00	1	3	109	blmartin	3	
351	2014-11-20 14:58:12.844059+00	1	3	130	brynstclair	3	
352	2014-11-20 14:58:12.846494+00	1	3	75	bwemple	3	
353	2014-11-20 14:58:12.848304+00	1	3	66	caitlinfeehan	3	
354	2014-11-20 14:58:12.850807+00	1	3	138	carolineloop	3	
355	2014-11-20 14:58:12.852598+00	1	3	8	carolxsong	3	
356	2014-11-20 14:58:12.854834+00	1	3	63	cas214	3	
357	2014-11-20 14:58:12.856822+00	1	3	64	cband	3	
358	2014-11-20 14:58:12.8587+00	1	3	154	chhandana	3	
359	2014-11-20 14:58:12.861121+00	1	3	89	chmuibk	3	
360	2014-11-20 14:58:12.864551+00	1	3	69	cjohnsto	3	
361	2014-11-20 14:58:12.866971+00	1	3	103	cjones21	3	
362	2014-11-20 14:58:12.870379+00	1	3	134	crh2pw	3	
363	2014-11-20 14:58:12.875049+00	1	3	4	danames	3	
364	2014-11-20 14:58:12.877177+00	1	3	119	danames2	3	
365	2014-11-20 14:58:12.879208+00	1	3	114	danehurst	3	
366	2014-11-20 14:58:12.882568+00	1	3	145	davidmkey	3	
367	2014-11-20 14:58:12.884415+00	1	3	62	dbtarb	3	
368	2014-11-20 14:58:12.886877+00	1	3	46	demo	3	
369	2014-11-20 14:58:12.890949+00	1	3	107	diet_rich08	3	
370	2014-11-20 14:58:12.893387+00	1	3	111	ditmore	3	
371	2014-11-20 14:58:12.895322+00	1	3	95	donpark	3	
372	2014-11-20 14:58:12.897162+00	1	3	65	drfuka	3	
373	2014-11-20 14:58:12.898988+00	1	3	77	dsmackay	3	
374	2014-11-20 14:58:12.901462+00	1	3	12	dtarb	3	
375	2014-11-20 14:58:12.90446+00	1	3	124	dtarb1	3	
376	2014-11-20 14:58:12.90691+00	1	3	126	dtarb2	3	
377	2014-11-20 14:58:12.909272+00	1	3	102	dtarbrenci	3	
378	2014-11-20 14:58:12.912828+00	1	3	93	dtarbunc	3	
379	2014-11-20 14:58:12.914865+00	1	3	99	dtarbunc1	3	
380	2014-11-20 14:58:12.916722+00	1	3	73	dwilusz1	3	
381	2014-11-20 14:58:12.918576+00	1	3	78	eistan20	3	
382	2014-11-20 14:58:12.9206+00	1	3	85	fanye	3	
383	2014-11-20 14:58:12.923078+00	1	3	104	gaffey	3	
384	2014-11-20 14:58:12.926053+00	1	3	149	garybc	3	
385	2014-11-20 14:58:12.929919+00	1	3	110	henriquepdp	3	
386	2014-11-20 14:58:12.933989+00	1	3	125	hongyi	3	
387	2014-11-20 14:58:12.936841+00	1	3	9	horsburgh	3	
388	2014-11-20 14:58:12.939252+00	1	3	96	hyi	3	
389	2014-11-20 14:58:12.942165+00	1	3	10	jamy	3	
390	2014-11-20 14:58:12.944817+00	1	3	34	jarrigo@cuahsi.org	3	
391	2014-11-20 14:58:12.947065+00	1	3	39	jasonc	3	
392	2014-11-20 14:58:12.948888+00	1	3	91	jching	3	
393	2014-11-20 14:58:12.951017+00	1	3	3	jeff	3	
394	2014-11-20 14:58:12.952826+00	1	3	38	jeffheard	3	
395	2014-11-20 14:58:12.954684+00	1	3	54	jirikadlec2	3	
396	2014-11-20 14:58:12.956485+00	1	3	68	jncole	3	
397	2014-11-20 14:58:12.958266+00	1	3	29	jon_goodall	3	
398	2014-11-20 14:58:12.960518+00	1	3	94	jonglee1	3	
399	2014-11-20 14:58:12.962525+00	1	3	106	jplovette	3	
400	2014-11-20 14:58:12.964388+00	1	3	36	jsadler2	3	
401	2014-11-20 14:58:12.966535+00	1	3	156	jterstriep	3	
402	2014-11-20 14:58:12.969128+00	1	3	76	kkyong77	3	
403	2014-11-20 14:58:12.97295+00	1	3	112	klutton	3	
404	2014-11-20 14:58:12.975876+00	1	3	117	kshparajuli	3	
405	2014-11-20 14:58:12.977798+00	1	3	53	lanzhao	3	
406	2014-11-20 14:58:12.980353+00	1	3	58	lband	3	
407	2014-11-20 14:58:12.982278+00	1	3	32	lisa	3	
408	2014-11-20 14:58:12.984163+00	1	3	121	madelinemerck	3	
409	2014-11-20 14:58:12.987563+00	1	3	133	marklewis	3	
410	2014-11-20 14:58:12.991279+00	1	3	6	martinn	3	
411	2014-11-20 14:58:12.993453+00	1	3	155	matthewturk	3	
412	2014-11-20 14:58:12.995556+00	1	3	150	mesco92	3	
413	2014-11-20 14:58:12.99772+00	1	3	137	mjs	3	
414	2014-11-20 14:58:12.999678+00	1	3	92	mjstealey	3	
415	2014-11-20 14:58:13.001531+00	1	3	120	mleonardo	3	
416	2014-11-20 14:58:13.004503+00	1	3	84	moni	3	
417	2014-11-20 14:58:13.006754+00	1	3	97	moon	3	
418	2014-11-20 14:58:13.009158+00	1	3	33	morsy	3	
419	2014-11-20 14:58:13.010929+00	1	3	59	mr_fnord	3	
420	2014-11-20 14:58:13.013036+00	1	3	82	mrl17	3	
421	2014-11-20 14:58:13.014921+00	1	3	79	mtlash	3	
422	2014-11-20 14:58:13.01672+00	1	3	50	myersjd	3	
423	2014-11-20 14:58:13.018548+00	1	3	142	n8urgrl	3	
424	2014-11-20 14:58:13.020838+00	1	3	116	nolankwood	3	
425	2014-11-20 14:58:13.02375+00	1	3	70	peckhams	3	
426	2014-11-20 14:58:13.025765+00	1	3	47	peterfitch	3	
427	2014-11-20 14:58:13.029124+00	1	3	57	pkdash	3	
428	2014-11-20 14:58:13.032399+00	1	3	16	platosken	3	
429	2014-11-20 14:58:13.034594+00	1	3	83	prasad999	3	
430	2014-11-20 14:58:13.036563+00	1	3	7	rayi	3	
431	2014-11-20 14:58:13.038804+00	1	3	44	rayi@computer.org	3	
432	2014-11-20 14:58:13.041863+00	1	3	45	rayi@renci.org	3	
433	2014-11-20 14:58:13.044853+00	1	3	56	reynola3	3	
434	2014-11-20 14:58:13.047277+00	1	3	88	rfun	3	
435	2014-11-20 14:58:13.049246+00	1	3	67	ridaszak	3	
436	2014-11-20 14:58:13.051128+00	1	3	90	rjhudson.illinois	3	
437	2014-11-20 14:58:13.053222+00	1	3	131	rodeogeorge	3	
438	2014-11-20 14:58:13.055148+00	1	3	14	root	3	
439	2014-11-20 14:58:13.057064+00	1	3	105	rrstanto	3	
440	2014-11-20 14:58:13.059896+00	1	3	127	rschweik	3	
441	2014-11-20 14:58:13.062144+00	1	3	98	selimnairb	3	
442	2014-11-20 14:58:13.064415+00	1	3	86	shaowen	3	
443	2014-11-20 14:58:13.066437+00	1	3	30	shaun	3	
444	2014-11-20 14:58:13.068938+00	1	3	11	shaunjl	3	
445	2014-11-20 14:58:13.071363+00	1	3	147	sjmcgrane	3	
446	2014-11-20 14:58:13.074299+00	1	3	143	smclinton	3	
447	2014-11-20 14:58:13.076693+00	1	3	135	solomonvimal	3	
448	2014-11-20 14:58:13.078624+00	1	3	17	srj9	3	
449	2014-11-20 14:58:13.080581+00	1	3	157	stvhoey	3	
450	2014-11-20 14:58:13.082995+00	1	3	128	tanza9	3	
451	2014-11-20 14:58:13.084869+00	1	3	153	tarabongio	3	
452	2014-11-20 14:58:13.087858+00	1	3	81	test	3	
453	2014-11-20 14:58:13.091434+00	1	3	2	th	3	
454	2014-11-20 14:58:13.093757+00	1	3	60	tony-castronova	3	
455	2014-11-20 14:58:13.095787+00	1	3	139	tufford	3	
456	2014-11-20 14:58:13.097643+00	1	3	13	valentinedwv	3	
457	2014-11-20 14:58:13.099729+00	1	3	51	vmmerwade	3	
458	2014-11-20 14:58:13.101647+00	1	3	113	wyaniero	3	
459	2014-11-20 14:58:13.103866+00	1	3	52	yirugi	3	
460	2014-11-20 14:58:13.105981+00	1	3	123	zsdlightning	3	
461	2014-11-20 15:00:52.331533+00	1	3	148	Bruce	3	
462	2014-11-20 15:00:52.334607+00	1	3	5	Castronova	3	
463	2014-11-20 15:00:52.33671+00	1	3	108	Colinbagley	3	
464	2014-11-20 15:00:52.338582+00	1	3	132	Guyfin	3	
465	2014-11-20 15:00:52.340959+00	1	3	48	LenoraS	3	
466	2014-11-20 15:00:52.343268+00	1	3	151	MeganMallard	3	
467	2014-11-20 15:00:52.346077+00	1	3	49	Swoodward	3	
468	2014-11-20 15:00:52.348973+00	1	3	61	Tim_Whiteaker	3	
469	2014-11-20 15:00:52.351419+00	1	3	146	abhijoey234	3	
470	2014-11-20 15:00:52.353712+00	1	3	136	ablemann	3	
471	2014-11-20 15:00:52.356099+00	1	3	115	acgold_4	3	
472	2014-11-20 15:00:52.358176+00	1	3	144	akebedew	3	
473	2014-11-20 15:00:52.359813+00	1	3	80	akilic	3	
474	2014-11-20 15:00:52.361617+00	1	3	129	alan_d_snow	3	
475	2014-11-20 15:00:52.363718+00	1	3	118	amabdallah	3	
476	2014-11-20 15:00:52.365951+00	1	3	87	apadmana	3	
477	2014-11-20 15:00:52.368302+00	1	3	15	ashsemien	3	
478	2014-11-20 15:00:52.370873+00	1	3	140	asouid	3	
479	2014-11-20 15:00:52.372885+00	1	3	71	aufdenkampe	3	
480	2014-11-20 15:00:52.375042+00	1	3	55	bartnijssen	3	
481	2014-11-20 15:00:52.376933+00	1	3	152	bdame	3	
482	2014-11-20 15:00:52.378766+00	1	3	74	beighley	3	
483	2014-11-20 15:00:52.380989+00	1	3	141	bjacobson	3	
484	2014-11-20 15:00:52.384647+00	1	3	109	blmartin	3	
485	2014-11-20 15:00:52.388538+00	1	3	130	brynstclair	3	
486	2014-11-20 15:00:52.392879+00	1	3	75	bwemple	3	
487	2014-11-20 15:00:52.397098+00	1	3	66	caitlinfeehan	3	
488	2014-11-20 15:00:52.40073+00	1	3	138	carolineloop	3	
489	2014-11-20 15:00:52.403632+00	1	3	8	carolxsong	3	
490	2014-11-20 15:00:52.406141+00	1	3	63	cas214	3	
491	2014-11-20 15:00:52.408581+00	1	3	64	cband	3	
492	2014-11-20 15:00:52.411103+00	1	3	154	chhandana	3	
493	2014-11-20 15:00:52.413116+00	1	3	89	chmuibk	3	
494	2014-11-20 15:00:52.415465+00	1	3	69	cjohnsto	3	
495	2014-11-20 15:00:52.419131+00	1	3	103	cjones21	3	
496	2014-11-20 15:00:52.421748+00	1	3	134	crh2pw	3	
497	2014-11-20 15:00:52.423977+00	1	3	4	danames	3	
498	2014-11-20 15:00:52.425883+00	1	3	119	danames2	3	
499	2014-11-20 15:00:52.429254+00	1	3	114	danehurst	3	
500	2014-11-20 15:00:52.43273+00	1	3	145	davidmkey	3	
501	2014-11-20 15:00:52.435+00	1	3	62	dbtarb	3	
502	2014-11-20 15:00:52.437149+00	1	3	46	demo	3	
503	2014-11-20 15:00:52.439191+00	1	3	107	diet_rich08	3	
504	2014-11-20 15:00:52.441591+00	1	3	111	ditmore	3	
505	2014-11-20 15:00:52.444002+00	1	3	95	donpark	3	
506	2014-11-20 15:00:52.446372+00	1	3	65	drfuka	3	
507	2014-11-20 15:00:52.448687+00	1	3	77	dsmackay	3	
508	2014-11-20 15:00:52.451414+00	1	3	12	dtarb	3	
509	2014-11-20 15:00:52.453572+00	1	3	124	dtarb1	3	
510	2014-11-20 15:00:52.455815+00	1	3	126	dtarb2	3	
511	2014-11-20 15:00:52.457939+00	1	3	102	dtarbrenci	3	
512	2014-11-20 15:00:52.459822+00	1	3	93	dtarbunc	3	
513	2014-11-20 15:00:52.46176+00	1	3	99	dtarbunc1	3	
514	2014-11-20 15:00:52.463671+00	1	3	73	dwilusz1	3	
515	2014-11-20 15:00:52.465483+00	1	3	78	eistan20	3	
516	2014-11-20 15:00:52.46721+00	1	3	85	fanye	3	
517	2014-11-20 15:00:52.469548+00	1	3	104	gaffey	3	
518	2014-11-20 15:00:52.473229+00	1	3	149	garybc	3	
519	2014-11-20 15:00:52.475942+00	1	3	110	henriquepdp	3	
520	2014-11-20 15:00:52.478268+00	1	3	125	hongyi	3	
521	2014-11-20 15:00:52.480848+00	1	3	9	horsburgh	3	
522	2014-11-20 15:00:52.482964+00	1	3	96	hyi	3	
523	2014-11-20 15:00:52.485634+00	1	3	10	jamy	3	
524	2014-11-20 15:00:52.49018+00	1	3	34	jarrigo@cuahsi.org	3	
525	2014-11-20 15:00:52.493061+00	1	3	39	jasonc	3	
526	2014-11-20 15:00:52.495184+00	1	3	91	jching	3	
527	2014-11-20 15:00:52.496932+00	1	3	3	jeff	3	
528	2014-11-20 15:00:52.498735+00	1	3	38	jeffheard	3	
529	2014-11-20 15:00:52.500737+00	1	3	54	jirikadlec2	3	
530	2014-11-20 15:00:52.50226+00	1	3	68	jncole	3	
531	2014-11-20 15:00:52.505073+00	1	3	29	jon_goodall	3	
532	2014-11-20 15:00:52.506931+00	1	3	94	jonglee1	3	
533	2014-11-20 15:00:52.509318+00	1	3	106	jplovette	3	
534	2014-11-20 15:00:52.51217+00	1	3	36	jsadler2	3	
535	2014-11-20 15:00:52.51456+00	1	3	156	jterstriep	3	
536	2014-11-20 15:00:52.516889+00	1	3	76	kkyong77	3	
537	2014-11-20 15:00:52.518949+00	1	3	112	klutton	3	
538	2014-11-20 15:00:52.521411+00	1	3	117	kshparajuli	3	
539	2014-11-20 15:00:52.524273+00	1	3	53	lanzhao	3	
540	2014-11-20 15:00:52.527075+00	1	3	58	lband	3	
541	2014-11-20 15:00:52.529912+00	1	3	32	lisa	3	
542	2014-11-20 15:00:52.532486+00	1	3	121	madelinemerck	3	
543	2014-11-20 15:00:52.53543+00	1	3	133	marklewis	3	
544	2014-11-20 15:00:52.537866+00	1	3	6	martinn	3	
545	2014-11-20 15:00:52.53995+00	1	3	155	matthewturk	3	
546	2014-11-20 15:00:52.542586+00	1	3	150	mesco92	3	
547	2014-11-20 15:00:52.544844+00	1	3	137	mjs	3	
548	2014-11-20 15:00:52.546983+00	1	3	92	mjstealey	3	
549	2014-11-20 15:00:52.551052+00	1	3	120	mleonardo	3	
550	2014-11-20 15:00:52.553625+00	1	3	84	moni	3	
551	2014-11-20 15:00:52.555988+00	1	3	97	moon	3	
552	2014-11-20 15:00:52.558266+00	1	3	33	morsy	3	
553	2014-11-20 15:00:52.56102+00	1	3	59	mr_fnord	3	
554	2014-11-20 15:00:52.5634+00	1	3	82	mrl17	3	
556	2014-11-20 15:00:52.568299+00	1	3	50	myersjd	3	
557	2014-11-20 15:00:52.571087+00	1	3	142	n8urgrl	3	
558	2014-11-20 15:00:52.575351+00	1	3	116	nolankwood	3	
559	2014-11-20 15:00:52.583171+00	1	3	70	peckhams	3	
560	2014-11-20 15:00:52.585548+00	1	3	47	peterfitch	3	
561	2014-11-20 15:00:52.592366+00	1	3	57	pkdash	3	
562	2014-11-20 15:00:52.599657+00	1	3	16	platosken	3	
563	2014-11-20 15:00:52.603871+00	1	3	83	prasad999	3	
564	2014-11-20 15:00:52.606024+00	1	3	7	rayi	3	
565	2014-11-20 15:00:52.609055+00	1	3	44	rayi@computer.org	3	
566	2014-11-20 15:00:52.61183+00	1	3	45	rayi@renci.org	3	
567	2014-11-20 15:00:52.61381+00	1	3	56	reynola3	3	
568	2014-11-20 15:00:52.615895+00	1	3	88	rfun	3	
569	2014-11-20 15:00:52.617552+00	1	3	67	ridaszak	3	
570	2014-11-20 15:00:52.619988+00	1	3	90	rjhudson.illinois	3	
571	2014-11-20 15:00:52.624789+00	1	3	131	rodeogeorge	3	
572	2014-11-20 15:00:52.628281+00	1	3	14	root	3	
573	2014-11-20 15:00:52.630189+00	1	3	105	rrstanto	3	
574	2014-11-20 15:00:52.632364+00	1	3	127	rschweik	3	
575	2014-11-20 15:00:52.636563+00	1	3	98	selimnairb	3	
576	2014-11-20 15:00:52.638786+00	1	3	86	shaowen	3	
577	2014-11-20 15:00:52.640777+00	1	3	30	shaun	3	
578	2014-11-20 15:00:52.643049+00	1	3	11	shaunjl	3	
579	2014-11-20 15:00:52.64535+00	1	3	147	sjmcgrane	3	
580	2014-11-20 15:00:52.64767+00	1	3	143	smclinton	3	
581	2014-11-20 15:00:52.650054+00	1	3	135	solomonvimal	3	
582	2014-11-20 15:00:52.652586+00	1	3	17	srj9	3	
583	2014-11-20 15:00:52.65718+00	1	3	157	stvhoey	3	
584	2014-11-20 15:00:52.659842+00	1	3	128	tanza9	3	
585	2014-11-20 15:00:52.661823+00	1	3	153	tarabongio	3	
586	2014-11-20 15:00:52.665521+00	1	3	81	test	3	
587	2014-11-20 15:00:52.669307+00	1	3	2	th	3	
588	2014-11-20 15:00:52.672326+00	1	3	60	tony-castronova	3	
589	2014-11-20 15:00:52.674121+00	1	3	139	tufford	3	
590	2014-11-20 15:00:52.676882+00	1	3	13	valentinedwv	3	
591	2014-11-20 15:00:52.67906+00	1	3	51	vmmerwade	3	
592	2014-11-20 15:00:52.681499+00	1	3	113	wyaniero	3	
593	2014-11-20 15:00:52.685389+00	1	3	52	yirugi	3	
594	2014-11-20 15:00:52.687879+00	1	3	123	zsdlightning	3	
595	2014-11-20 15:08:52.03889+00	1	3	148	Bruce	3	
596	2014-11-20 15:08:52.042631+00	1	3	5	Castronova	3	
597	2014-11-20 15:08:52.045822+00	1	3	108	Colinbagley	3	
598	2014-11-20 15:08:52.048384+00	1	3	132	Guyfin	3	
599	2014-11-20 15:08:52.051999+00	1	3	48	LenoraS	3	
600	2014-11-20 15:08:52.05457+00	1	3	151	MeganMallard	3	
601	2014-11-20 15:08:52.056629+00	1	3	49	Swoodward	3	
602	2014-11-20 15:08:52.060261+00	1	3	61	Tim_Whiteaker	3	
603	2014-11-20 15:08:52.063217+00	1	3	146	abhijoey234	3	
604	2014-11-20 15:08:52.065378+00	1	3	136	ablemann	3	
605	2014-11-20 15:08:52.067319+00	1	3	115	acgold_4	3	
606	2014-11-20 15:08:52.069132+00	1	3	144	akebedew	3	
607	2014-11-20 15:08:52.071191+00	1	3	80	akilic	3	
608	2014-11-20 15:08:52.07336+00	1	3	129	alan_d_snow	3	
609	2014-11-20 15:08:52.075617+00	1	3	118	amabdallah	3	
610	2014-11-20 15:08:52.077938+00	1	3	87	apadmana	3	
611	2014-11-20 15:08:52.080587+00	1	3	15	ashsemien	3	
612	2014-11-20 15:08:52.082563+00	1	3	140	asouid	3	
613	2014-11-20 15:08:52.084748+00	1	3	71	aufdenkampe	3	
614	2014-11-20 15:08:52.086803+00	1	3	55	bartnijssen	3	
615	2014-11-20 15:08:52.089913+00	1	3	152	bdame	3	
616	2014-11-20 15:08:52.092105+00	1	3	74	beighley	3	
617	2014-11-20 15:08:52.094077+00	1	3	141	bjacobson	3	
618	2014-11-20 15:08:52.096109+00	1	3	109	blmartin	3	
619	2014-11-20 15:08:52.099195+00	1	3	130	brynstclair	3	
620	2014-11-20 15:08:52.103033+00	1	3	75	bwemple	3	
621	2014-11-20 15:08:52.105248+00	1	3	66	caitlinfeehan	3	
622	2014-11-20 15:08:52.10728+00	1	3	138	carolineloop	3	
623	2014-11-20 15:08:52.109435+00	1	3	8	carolxsong	3	
624	2014-11-20 15:08:52.111226+00	1	3	63	cas214	3	
625	2014-11-20 15:08:52.113307+00	1	3	64	cband	3	
626	2014-11-20 15:08:52.115909+00	1	3	154	chhandana	3	
627	2014-11-20 15:08:52.117356+00	1	3	89	chmuibk	3	
628	2014-11-20 15:08:52.120123+00	1	3	69	cjohnsto	3	
629	2014-11-20 15:08:52.122846+00	1	3	103	cjones21	3	
630	2014-11-20 15:08:52.125396+00	1	3	134	crh2pw	3	
631	2014-11-20 15:08:52.127573+00	1	3	4	danames	3	
632	2014-11-20 15:08:52.129415+00	1	3	119	danames2	3	
633	2014-11-20 15:08:52.131317+00	1	3	114	danehurst	3	
634	2014-11-20 15:08:52.133641+00	1	3	145	davidmkey	3	
635	2014-11-20 15:08:52.135834+00	1	3	62	dbtarb	3	
636	2014-11-20 15:08:52.137777+00	1	3	46	demo	3	
637	2014-11-20 15:08:52.139784+00	1	3	107	diet_rich08	3	
638	2014-11-20 15:08:52.142268+00	1	3	111	ditmore	3	
639	2014-11-20 15:08:52.144652+00	1	3	95	donpark	3	
640	2014-11-20 15:08:52.148579+00	1	3	65	drfuka	3	
641	2014-11-20 15:08:52.152217+00	1	3	77	dsmackay	3	
642	2014-11-20 15:08:52.154886+00	1	3	12	dtarb	3	
643	2014-11-20 15:08:52.15772+00	1	3	124	dtarb1	3	
644	2014-11-20 15:08:52.161911+00	1	3	126	dtarb2	3	
645	2014-11-20 15:08:52.165746+00	1	3	102	dtarbrenci	3	
646	2014-11-20 15:08:52.167774+00	1	3	93	dtarbunc	3	
647	2014-11-20 15:08:52.169983+00	1	3	99	dtarbunc1	3	
648	2014-11-20 15:08:52.172066+00	1	3	73	dwilusz1	3	
649	2014-11-20 15:08:52.174309+00	1	3	78	eistan20	3	
650	2014-11-20 15:08:52.176727+00	1	3	85	fanye	3	
651	2014-11-20 15:08:52.179268+00	1	3	104	gaffey	3	
652	2014-11-20 15:08:52.181433+00	1	3	149	garybc	3	
653	2014-11-20 15:08:52.183605+00	1	3	110	henriquepdp	3	
654	2014-11-20 15:08:52.185459+00	1	3	125	hongyi	3	
655	2014-11-20 15:08:52.187464+00	1	3	9	horsburgh	3	
656	2014-11-20 15:08:52.189232+00	1	3	96	hyi	3	
657	2014-11-20 15:08:52.191728+00	1	3	10	jamy	3	
658	2014-11-20 15:08:52.193591+00	1	3	34	jarrigo@cuahsi.org	3	
659	2014-11-20 15:08:52.19538+00	1	3	39	jasonc	3	
660	2014-11-20 15:08:52.197367+00	1	3	91	jching	3	
661	2014-11-20 15:08:52.199865+00	1	3	3	jeff	3	
662	2014-11-20 15:08:52.203699+00	1	3	38	jeffheard	3	
663	2014-11-20 15:08:52.205742+00	1	3	54	jirikadlec2	3	
664	2014-11-20 15:08:52.207931+00	1	3	68	jncole	3	
665	2014-11-20 15:08:52.210305+00	1	3	29	jon_goodall	3	
666	2014-11-20 15:08:52.212366+00	1	3	94	jonglee1	3	
667	2014-11-20 15:08:52.214263+00	1	3	106	jplovette	3	
668	2014-11-20 15:08:52.216105+00	1	3	36	jsadler2	3	
669	2014-11-20 15:08:52.218411+00	1	3	156	jterstriep	3	
670	2014-11-20 15:08:52.22294+00	1	3	76	kkyong77	3	
671	2014-11-20 15:08:52.226411+00	1	3	112	klutton	3	
672	2014-11-20 15:08:52.229301+00	1	3	117	kshparajuli	3	
673	2014-11-20 15:08:52.232346+00	1	3	53	lanzhao	3	
674	2014-11-20 15:08:52.23491+00	1	3	58	lband	3	
675	2014-11-20 15:08:52.237499+00	1	3	32	lisa	3	
676	2014-11-20 15:08:52.239988+00	1	3	121	madelinemerck	3	
677	2014-11-20 15:08:52.242676+00	1	3	133	marklewis	3	
678	2014-11-20 15:08:52.245083+00	1	3	6	martinn	3	
679	2014-11-20 15:08:52.248507+00	1	3	155	matthewturk	3	
680	2014-11-20 15:08:52.251217+00	1	3	150	mesco92	3	
681	2014-11-20 15:08:52.253811+00	1	3	137	mjs	3	
682	2014-11-20 15:08:52.255866+00	1	3	92	mjstealey	3	
683	2014-11-20 15:08:52.258552+00	1	3	120	mleonardo	3	
684	2014-11-20 15:08:52.262799+00	1	3	84	moni	3	
685	2014-11-20 15:08:52.26504+00	1	3	97	moon	3	
686	2014-11-20 15:08:52.267116+00	1	3	33	morsy	3	
687	2014-11-20 15:08:52.268926+00	1	3	59	mr_fnord	3	
688	2014-11-20 15:08:52.27093+00	1	3	82	mrl17	3	
689	2014-11-20 15:08:52.272919+00	1	3	79	mtlash	3	
690	2014-11-20 15:08:52.275293+00	1	3	50	myersjd	3	
691	2014-11-20 15:08:52.277929+00	1	3	142	n8urgrl	3	
692	2014-11-20 15:08:52.280804+00	1	3	116	nolankwood	3	
693	2014-11-20 15:08:52.283121+00	1	3	70	peckhams	3	
694	2014-11-20 15:08:52.285201+00	1	3	47	peterfitch	3	
695	2014-11-20 15:08:52.287213+00	1	3	57	pkdash	3	
696	2014-11-20 15:08:52.288943+00	1	3	16	platosken	3	
697	2014-11-20 15:08:52.291248+00	1	3	83	prasad999	3	
698	2014-11-20 15:08:52.293167+00	1	3	7	rayi	3	
699	2014-11-20 15:08:52.294996+00	1	3	44	rayi@computer.org	3	
700	2014-11-20 15:08:52.296832+00	1	3	45	rayi@renci.org	3	
701	2014-11-20 15:08:52.299717+00	1	3	56	reynola3	3	
702	2014-11-20 15:08:52.302958+00	1	3	88	rfun	3	
703	2014-11-20 15:08:52.305003+00	1	3	67	ridaszak	3	
704	2014-11-20 15:08:52.30737+00	1	3	90	rjhudson.illinois	3	
705	2014-11-20 15:08:52.309803+00	1	3	131	rodeogeorge	3	
706	2014-11-20 15:08:52.311642+00	1	3	14	root	3	
707	2014-11-20 15:08:52.313526+00	1	3	105	rrstanto	3	
708	2014-11-20 15:08:52.315354+00	1	3	127	rschweik	3	
709	2014-11-20 15:08:52.317175+00	1	3	98	selimnairb	3	
710	2014-11-20 15:08:52.320609+00	1	3	86	shaowen	3	
711	2014-11-20 15:08:52.324092+00	1	3	30	shaun	3	
712	2014-11-20 15:08:52.326545+00	1	3	11	shaunjl	3	
713	2014-11-20 15:08:52.328761+00	1	3	147	sjmcgrane	3	
714	2014-11-20 15:08:52.331436+00	1	3	143	smclinton	3	
715	2014-11-20 15:08:52.333713+00	1	3	135	solomonvimal	3	
716	2014-11-20 15:08:52.335652+00	1	3	17	srj9	3	
717	2014-11-20 15:08:52.337699+00	1	3	157	stvhoey	3	
718	2014-11-20 15:08:52.339514+00	1	3	128	tanza9	3	
719	2014-11-20 15:08:52.341769+00	1	3	153	tarabongio	3	
720	2014-11-20 15:08:52.343736+00	1	3	81	test	3	
721	2014-11-20 15:08:52.345659+00	1	3	2	th	3	
722	2014-11-20 15:08:52.347626+00	1	3	60	tony-castronova	3	
723	2014-11-20 15:08:52.349368+00	1	3	139	tufford	3	
724	2014-11-20 15:08:52.353386+00	1	3	13	valentinedwv	3	
725	2014-11-20 15:08:52.355687+00	1	3	51	vmmerwade	3	
726	2014-11-20 15:08:52.358397+00	1	3	113	wyaniero	3	
727	2014-11-20 15:08:52.362152+00	1	3	52	yirugi	3	
728	2014-11-20 15:08:52.36438+00	1	3	123	zsdlightning	3	
729	2014-11-20 15:09:26.193241+00	1	3	148	Bruce	3	
730	2014-11-20 15:09:26.197614+00	1	3	5	Castronova	3	
731	2014-11-20 15:09:26.200568+00	1	3	108	Colinbagley	3	
732	2014-11-20 15:09:26.203357+00	1	3	132	Guyfin	3	
733	2014-11-20 15:09:26.205954+00	1	3	48	LenoraS	3	
734	2014-11-20 15:09:26.208412+00	1	3	151	MeganMallard	3	
735	2014-11-20 15:09:26.210754+00	1	3	49	Swoodward	3	
736	2014-11-20 15:09:26.215476+00	1	3	61	Tim_Whiteaker	3	
737	2014-11-20 15:09:26.217391+00	1	3	146	abhijoey234	3	
738	2014-11-20 15:09:26.21925+00	1	3	136	ablemann	3	
739	2014-11-20 15:09:26.220985+00	1	3	115	acgold_4	3	
740	2014-11-20 15:09:26.225081+00	1	3	144	akebedew	3	
741	2014-11-20 15:09:26.227358+00	1	3	80	akilic	3	
742	2014-11-20 15:09:26.229229+00	1	3	129	alan_d_snow	3	
743	2014-11-20 15:09:26.231092+00	1	3	118	amabdallah	3	
744	2014-11-20 15:09:26.233335+00	1	3	87	apadmana	3	
745	2014-11-20 15:09:26.235487+00	1	3	15	ashsemien	3	
746	2014-11-20 15:09:26.238081+00	1	3	140	asouid	3	
747	2014-11-20 15:09:26.24022+00	1	3	71	aufdenkampe	3	
748	2014-11-20 15:09:26.242818+00	1	3	55	bartnijssen	3	
749	2014-11-20 15:09:26.24518+00	1	3	152	bdame	3	
750	2014-11-20 15:09:26.24754+00	1	3	74	beighley	3	
751	2014-11-20 15:09:26.249379+00	1	3	141	bjacobson	3	
752	2014-11-20 15:09:26.251349+00	1	3	109	blmartin	3	
753	2014-11-20 15:09:26.254136+00	1	3	130	brynstclair	3	
754	2014-11-20 15:09:26.258109+00	1	3	75	bwemple	3	
755	2014-11-20 15:09:26.262965+00	1	3	66	caitlinfeehan	3	
756	2014-11-20 15:09:26.265715+00	1	3	138	carolineloop	3	
757	2014-11-20 15:09:26.268372+00	1	3	8	carolxsong	3	
758	2014-11-20 15:09:26.270885+00	1	3	63	cas214	3	
759	2014-11-20 15:09:26.273313+00	1	3	64	cband	3	
760	2014-11-20 15:09:26.276653+00	1	3	154	chhandana	3	
761	2014-11-20 15:09:26.278948+00	1	3	89	chmuibk	3	
762	2014-11-20 15:09:26.281312+00	1	3	69	cjohnsto	3	
763	2014-11-20 15:09:26.284136+00	1	3	103	cjones21	3	
764	2014-11-20 15:09:26.288052+00	1	3	134	crh2pw	3	
765	2014-11-20 15:09:26.290512+00	1	3	4	danames	3	
766	2014-11-20 15:09:26.292981+00	1	3	119	danames2	3	
767	2014-11-20 15:09:26.294883+00	1	3	114	danehurst	3	
768	2014-11-20 15:09:26.296729+00	1	3	145	davidmkey	3	
769	2014-11-20 15:09:26.298472+00	1	3	62	dbtarb	3	
770	2014-11-20 15:09:26.30025+00	1	3	46	demo	3	
771	2014-11-20 15:09:26.30216+00	1	3	107	diet_rich08	3	
772	2014-11-20 15:09:26.304483+00	1	3	111	ditmore	3	
773	2014-11-20 15:09:26.306611+00	1	3	95	donpark	3	
774	2014-11-20 15:09:26.308593+00	1	3	65	drfuka	3	
775	2014-11-20 15:09:26.311169+00	1	3	77	dsmackay	3	
776	2014-11-20 15:09:26.312933+00	1	3	12	dtarb	3	
777	2014-11-20 15:09:26.315379+00	1	3	124	dtarb1	3	
778	2014-11-20 15:09:26.31757+00	1	3	126	dtarb2	3	
779	2014-11-20 15:09:26.319428+00	1	3	102	dtarbrenci	3	
780	2014-11-20 15:09:26.321213+00	1	3	93	dtarbunc	3	
781	2014-11-20 15:09:26.324226+00	1	3	99	dtarbunc1	3	
782	2014-11-20 15:09:26.327239+00	1	3	73	dwilusz1	3	
783	2014-11-20 15:09:26.329389+00	1	3	78	eistan20	3	
784	2014-11-20 15:09:26.331399+00	1	3	85	fanye	3	
785	2014-11-20 15:09:26.333342+00	1	3	104	gaffey	3	
786	2014-11-20 15:09:26.335125+00	1	3	149	garybc	3	
787	2014-11-20 15:09:26.337383+00	1	3	110	henriquepdp	3	
788	2014-11-20 15:09:26.339355+00	1	3	125	hongyi	3	
789	2014-11-20 15:09:26.341142+00	1	3	9	horsburgh	3	
790	2014-11-20 15:09:26.343522+00	1	3	96	hyi	3	
791	2014-11-20 15:09:26.347395+00	1	3	10	jamy	3	
792	2014-11-20 15:09:26.350114+00	1	3	34	jarrigo@cuahsi.org	3	
793	2014-11-20 15:09:26.352727+00	1	3	39	jasonc	3	
794	2014-11-20 15:09:26.354862+00	1	3	91	jching	3	
795	2014-11-20 15:09:26.356903+00	1	3	3	jeff	3	
796	2014-11-20 15:09:26.359123+00	1	3	38	jeffheard	3	
797	2014-11-20 15:09:26.361519+00	1	3	54	jirikadlec2	3	
798	2014-11-20 15:09:26.363726+00	1	3	68	jncole	3	
799	2014-11-20 15:09:26.366048+00	1	3	29	jon_goodall	3	
800	2014-11-20 15:09:26.368289+00	1	3	94	jonglee1	3	
801	2014-11-20 15:09:26.370667+00	1	3	106	jplovette	3	
802	2014-11-20 15:09:26.37398+00	1	3	36	jsadler2	3	
803	2014-11-20 15:09:26.376522+00	1	3	156	jterstriep	3	
804	2014-11-20 15:09:26.378279+00	1	3	76	kkyong77	3	
805	2014-11-20 15:09:26.380056+00	1	3	112	klutton	3	
806	2014-11-20 15:09:26.38198+00	1	3	117	kshparajuli	3	
807	2014-11-20 15:09:26.385115+00	1	3	53	lanzhao	3	
808	2014-11-20 15:09:26.388982+00	1	3	58	lband	3	
809	2014-11-20 15:09:26.391069+00	1	3	32	lisa	3	
810	2014-11-20 15:09:26.393617+00	1	3	121	madelinemerck	3	
811	2014-11-20 15:09:26.395631+00	1	3	133	marklewis	3	
812	2014-11-20 15:09:26.397546+00	1	3	6	martinn	3	
813	2014-11-20 15:09:26.399467+00	1	3	155	matthewturk	3	
814	2014-11-20 15:09:26.401726+00	1	3	150	mesco92	3	
815	2014-11-20 15:09:26.404418+00	1	3	137	mjs	3	
816	2014-11-20 15:09:26.406769+00	1	3	92	mjstealey	3	
817	2014-11-20 15:09:26.409395+00	1	3	120	mleonardo	3	
818	2014-11-20 15:09:26.412481+00	1	3	84	moni	3	
819	2014-11-20 15:09:26.414525+00	1	3	97	moon	3	
820	2014-11-20 15:09:26.416559+00	1	3	33	morsy	3	
821	2014-11-20 15:09:26.418428+00	1	3	59	mr_fnord	3	
822	2014-11-20 15:09:26.420286+00	1	3	82	mrl17	3	
823	2014-11-20 15:09:26.422104+00	1	3	79	mtlash	3	
824	2014-11-20 15:09:26.425273+00	1	3	50	myersjd	3	
825	2014-11-20 15:09:26.427876+00	1	3	142	n8urgrl	3	
826	2014-11-20 15:09:26.429995+00	1	3	116	nolankwood	3	
827	2014-11-20 15:09:26.431788+00	1	3	70	peckhams	3	
828	2014-11-20 15:09:26.433807+00	1	3	47	peterfitch	3	
829	2014-11-20 15:09:26.435674+00	1	3	57	pkdash	3	
830	2014-11-20 15:09:26.437758+00	1	3	16	platosken	3	
831	2014-11-20 15:09:26.439847+00	1	3	83	prasad999	3	
832	2014-11-20 15:09:26.443733+00	1	3	7	rayi	3	
833	2014-11-20 15:09:26.447556+00	1	3	44	rayi@computer.org	3	
834	2014-11-20 15:09:26.449872+00	1	3	45	rayi@renci.org	3	
835	2014-11-20 15:09:26.452241+00	1	3	56	reynola3	3	
836	2014-11-20 15:09:26.454323+00	1	3	88	rfun	3	
837	2014-11-20 15:09:26.456347+00	1	3	67	ridaszak	3	
838	2014-11-20 15:09:26.460427+00	1	3	90	rjhudson.illinois	3	
839	2014-11-20 15:09:26.462131+00	1	3	131	rodeogeorge	3	
840	2014-11-20 15:09:26.463979+00	1	3	14	root	3	
841	2014-11-20 15:09:26.466605+00	1	3	105	rrstanto	3	
842	2014-11-20 15:09:26.468749+00	1	3	127	rschweik	3	
843	2014-11-20 15:09:26.471124+00	1	3	98	selimnairb	3	
844	2014-11-20 15:09:26.473478+00	1	3	86	shaowen	3	
845	2014-11-20 15:09:26.476432+00	1	3	30	shaun	3	
846	2014-11-20 15:09:26.478637+00	1	3	11	shaunjl	3	
847	2014-11-20 15:09:26.480559+00	1	3	147	sjmcgrane	3	
848	2014-11-20 15:09:26.482746+00	1	3	143	smclinton	3	
849	2014-11-20 15:09:26.486455+00	1	3	135	solomonvimal	3	
850	2014-11-20 15:09:26.489274+00	1	3	17	srj9	3	
851	2014-11-20 15:09:26.491401+00	1	3	157	stvhoey	3	
852	2014-11-20 15:09:26.493418+00	1	3	128	tanza9	3	
853	2014-11-20 15:09:26.495816+00	1	3	153	tarabongio	3	
854	2014-11-20 15:09:26.497797+00	1	3	81	test	3	
855	2014-11-20 15:09:26.499686+00	1	3	2	th	3	
856	2014-11-20 15:09:26.501874+00	1	3	60	tony-castronova	3	
857	2014-11-20 15:09:26.504702+00	1	3	139	tufford	3	
858	2014-11-20 15:09:26.507358+00	1	3	13	valentinedwv	3	
859	2014-11-20 15:09:26.510656+00	1	3	51	vmmerwade	3	
860	2014-11-20 15:09:26.513308+00	1	3	113	wyaniero	3	
861	2014-11-20 15:09:26.515615+00	1	3	52	yirugi	3	
862	2014-11-20 15:09:26.517441+00	1	3	123	zsdlightning	3	
\.


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 863, true);


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
\.


--
-- Name: django_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_comments_id_seq', 36, true);


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
94	party	hs_party	party
95	address code list	hs_party	addresscodelist
96	phone code list	hs_party	phonecodelist
97	email code list	hs_party	emailcodelist
98	city	hs_party	city
99	region	hs_party	region
100	country	hs_party	country
101	external identifier code list	hs_party	externalidentifiercodelist
102	name alias code list	hs_party	namealiascodelist
103	person	hs_party	person
104	person email	hs_party	personemail
105	person location	hs_party	personlocation
106	person phone	hs_party	personphone
107	person external identifier	hs_party	personexternalidentifier
108	user code list	hs_party	usercodelist
109	other name	hs_party	othername
110	organization code list	hs_party	organizationcodelist
111	organization	hs_party	organization
112	organization email	hs_party	organizationemail
113	organization location	hs_party	organizationlocation
114	organization phone	hs_party	organizationphone
115	organization name	hs_party	organizationname
116	external org identifier	hs_party	externalorgidentifier
117	group	hs_party	group
118	organization association	hs_party	organizationassociation
119	choice type	hs_party	choicetype
120	docker profile	django_docker_processes	dockerprofile
121	container overrides	django_docker_processes	containeroverrides
122	override env var	django_docker_processes	overrideenvvar
123	override volume	django_docker_processes	overridevolume
124	override link	django_docker_processes	overridelink
125	override port	django_docker_processes	overrideport
126	docker link	django_docker_processes	dockerlink
127	docker env var	django_docker_processes	dockerenvvar
128	docker volume	django_docker_processes	dockervolume
129	docker port	django_docker_processes	dockerport
130	docker process	django_docker_processes	dockerprocess
131	RHESSys Instance Resource	hs_rhessys_inst_resource	instresource
132	post gis geometry columns	gis	postgisgeometrycolumns
133	post gis spatial ref sys	gis	postgisspatialrefsys
134	iRODS Environment	django_irods	rodsenvironment
135	ogr dataset collection	ga_ows	ogrdatasetcollection
136	ogr dataset	ga_ows	ogrdataset
137	ogr layer	ga_ows	ogrlayer
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_content_type_id_seq', 137, true);


--
-- Data for Name: django_docker_processes_containeroverrides; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_containeroverrides (id, docker_profile_id, name, command, working_dir, "user", entrypoint, privileged, lxc_conf, memory_limit, cpu_shares, dns, net) FROM stdin;
\.


--
-- Name: django_docker_processes_containeroverrides_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_containeroverrides_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_dockerenvvar; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_dockerenvvar (id, docker_profile_id, name, value) FROM stdin;
\.


--
-- Name: django_docker_processes_dockerenvvar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_dockerenvvar_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_dockerlink; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_dockerlink (id, docker_profile_id, link_name, docker_profile_from_id, docker_overrides_id) FROM stdin;
\.


--
-- Name: django_docker_processes_dockerlink_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_dockerlink_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_dockerport; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_dockerport (id, docker_profile_id, host, container) FROM stdin;
\.


--
-- Name: django_docker_processes_dockerport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_dockerport_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_dockerprocess; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_dockerprocess (id, profile_id, container_id, token, logs, finished, error, user_id) FROM stdin;
\.


--
-- Name: django_docker_processes_dockerprocess_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_dockerprocess_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_dockerprofile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_dockerprofile (id, name, git_repository, git_use_submodules, git_username, git_password, commit_id, branch) FROM stdin;
\.


--
-- Name: django_docker_processes_dockerprofile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_dockerprofile_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_dockervolume; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_dockervolume (id, docker_profile_id, host, container, readonly) FROM stdin;
\.


--
-- Name: django_docker_processes_dockervolume_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_dockervolume_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_overrideenvvar; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_overrideenvvar (id, container_overrides_id, name, value) FROM stdin;
\.


--
-- Name: django_docker_processes_overrideenvvar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_overrideenvvar_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_overridelink; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_overridelink (id, container_overrides_id, link_name, docker_profile_from_id) FROM stdin;
\.


--
-- Name: django_docker_processes_overridelink_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_overridelink_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_overrideport; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_overrideport (id, container_overrides_id, host, container) FROM stdin;
\.


--
-- Name: django_docker_processes_overrideport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_overrideport_id_seq', 1, false);


--
-- Data for Name: django_docker_processes_overridevolume; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_docker_processes_overridevolume (id, container_overrides_id, host, container) FROM stdin;
\.


--
-- Name: django_docker_processes_overridevolume_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_docker_processes_overridevolume_id_seq', 1, false);


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
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2014-11-19 18:55:34.979716+00
2	auth	0001_initial	2014-11-19 18:55:35.11935+00
3	admin	0001_initial	2014-11-19 18:55:35.262338+00
4	sites	0001_initial	2014-11-19 18:55:35.389205+00
5	redirects	0001_initial	2014-11-19 18:55:35.532924+00
6	sessions	0001_initial	2014-11-19 18:55:35.664696+00
7	tastypie	0001_initial	2014-11-19 18:55:35.810073+00
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_migrations_id_seq', 7, true);


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
pdxuqnzlqj0mc6o95lokio6q2o10ja2u	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-13 15:33:10.402958+00
9rkn3c4iczesj3j3ystqq3jl88me0hvb	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-30 14:16:23.238771+00
o90mqv8pmz7u8ou6mzzb1rvjkdgm52bh	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-09 13:23:29.964167+00
bgyke8ywtf9tlpk1i121xelcgfoxho9u	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-09 16:34:43.177917+00
wc4rrgonauqbni3kcxpx4ruigsg6cp3b	MDE3MGQ0NzgyNGI1Yzg4ZTc1ZWEyNmJmNGFhMDIzZTE3NGQxMWQ4Njp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE3fQ==	2014-04-09 20:54:07.459754+00
u1elt2mtbqye5pvdlbnumrxble01kx2m	ODM0OTVmNjlhNmVjNTM3OWRkMzE2Yjk2MTVkYWYzYWI1NjhkNTE5Njp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ4fQ==	2014-06-30 21:01:09.615539+00
zyrqx8qadvwg3mwc4qcjgcwo7lg01hj3	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-04-10 21:38:42.838615+00
jhh573upkf9gs2ym8wzoit7zowuuai7n	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-06-25 17:06:10.759049+00
nrzsvs6tk1fjcv5ljtvhk8v5glt9xzdh	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-04-14 17:32:10.337189+00
uvb6ll1ydrb4fyu2y5wxey4eqlewiwq1	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-09 17:14:06.05567+00
27o0zb6gv6oki16zejuuxrsjlgc5en6h	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-04-23 14:56:30.122852+00
m98l8vwpg3nawryzyqusg80as3y3et5q	ZGIyMDNjNzUxZWYwNDVmZjZhNmE4YzU3ZjQ5M2Y2NTRmYjEwM2Y1YTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMwfQ==	2014-06-25 17:14:28.808856+00
tke9wphj31tfq0yi73u8e9u8wv4bq9ca	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-06 17:47:41.293076+00
a3ju7d87prcvjx3cnp114l7p8z42uglp	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 13:39:11.416792+00
33ai2992a72zm2safp80dfmm52n10as1	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-05-08 21:16:00.203714+00
06o5642dk8wo4f1s0wrfye0rjbmelndv	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-14 15:09:46.040567+00
nizuoy2ap774s1dgdac4g9wjo525mndt	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-06-20 13:17:35.573941+00
use123pj6rsktfeg7e8ckf4iii6ksu1h	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 15:05:42.794012+00
iks4i9iccctsvfupluelsndy5xrvf5fc	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-07-15 18:40:29.055141+00
2jo19jfo2fygvlaongpa4k5sqw2gc1bs	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-21 01:08:02.729221+00
epghtxgeloarw5xjidc6ylv30b4eub2l	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-13 21:42:58.171993+00
v694gohqokwhb4pq5tx1s68w88046vcr	ZmVkYTI0OTI3MDA2ZjYzOTE5ZmI3NzI5MTI0NDAzZThmNzhlMDFjNTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU1fQ==	2014-07-16 15:24:12.54437+00
p6ak7wqxmmu92dd8qkwoee4u6dlu7lm5	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-07-16 20:26:55.208121+00
dcy0jfxwgau6lcmd3oaaax3nh148aqcs	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-04 17:06:04.840711+00
oiebkhssmsww5ina92c2rfqocalqzqi9	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:49:21.930091+00
ayhoodcqib7a5gpcnie3jg59rfh2drj3	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-07-16 21:34:26.95063+00
ubjfi81gceid3gspk6kppqlq5is8o4og	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:51:03.909031+00
uhz6622g63pzrdxrq00o3aw2fxuoair3	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-23 00:27:12.212915+00
j3wpnwts8c04n1c65q6u7blczvj9d0na	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-07-23 21:58:23.446453+00
qkuh60cf2j3lodjnxbcjx2dtfb3tgnm6	OTFjNDBjYmRiNjgzNzI1ZTRkNjI1ZmJmY2NiMTQ5MmM5OThlYWFjMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjUyfQ==	2014-07-08 15:58:41.285833+00
9lexy064pm6gn8pwznmtuhkhkb006r6p	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-26 21:23:12.907639+00
8tazxgii9rebw2dju9l9j3pf1ah30ibn	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-08 18:57:00.622296+00
ec6gv853tc40jn5uwl9b44oguv4uxbik	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-27 03:45:08.552325+00
a2q7zvxc7729ddlk602vx5lw4bxgomdg	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-27 19:19:46.574898+00
f4ii0hq3e3dwb7jwzge6aq9bpuis7run	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-27 19:30:50.097958+00
nl2ol1hn329h0ijzvoioqysz7dgr51o4	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-28 01:46:29.315069+00
9e9ljhx2brwn0vsvq1h6scqzmn33pg8j	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-03-24 15:02:29.932232+00
qr1xremtfh4zy0jqw2g312hpy5m8gvyf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-09 00:54:28.496144+00
1wn3c6zqf28crfskpyzl66lacryuwbwy	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-28 15:33:28.807751+00
jtwo8e7p26hrq57qx83dr6u45ew8s5mt	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-06-30 15:14:56.217684+00
fjgx0smfm67otctek6kgb3vpe6afuic5	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-06-30 23:49:10.558632+00
jmfqwoja0oo3zi8au56x5h9qat2jpzpt	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-25 17:26:56.617585+00
ot776p91rzidm58k3cp8n2n3ot9f8pvk	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 13:55:20.129106+00
x094y96g2egpwi2na63btrsk8bv1eptl	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-06-26 13:12:50.688963+00
bbhtkjii4lkug90b6ot3oj68xgvc3cwf	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-20 23:59:51.801152+00
2duetxro5bsffi2j4j6y1k2dh7pk61c9	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-24 22:28:59.554253+00
pc2fkm15t2cbgq76qml4fig6utjuaevk	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-04-30 15:21:13.10097+00
a9xbk4ngsvagf50bumcklfy6v27f7xqc	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-21 01:09:12.031427+00
9i2z4t0o99keusrp2mj3gzqjk4ydlcdx	OGI2OTBlMjNmZjcxMTFiN2E0ZDM5NWZjYjBiY2FlMTRlZjc1NzgzYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzfQ==	2014-05-06 19:26:46.609864+00
p6u7rqkyxo77tyjaxf6r4dvy9ncfkn4l	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 16:16:45.121842+00
z1supwob9h3jt2qqv09m3sxr4qt1wng4	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-05-08 21:16:18.035112+00
1cwufl7gkqsfqwg3cxehofjbuurt8mqu	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-05-21 15:18:04.40864+00
9gc5f4si5snwluskmczice2hyxn8474x	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-13 18:16:41.11812+00
ryj9kyaimygli91wb0d9lj1w2kgplj04	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-01 21:33:03.971268+00
nlcgdhresina0ug86aplzsa8tdpgwlju	NzU4MjVjODM2NDJhNDU4MzY2M2MwNTZhZDNlMWUyNjQwYjBjZDY2Yjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU0fQ==	2014-07-16 02:38:13.426781+00
wd7lttwjty5u4i88gle25585g6mnndov	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-14 13:07:52.644815+00
x3pwsiahbkfne1k2c0rxlcprry8l6hbg	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:50:38.77378+00
dskbl9soaxcaxfwwr0y2wdegu02zk0m0	NWEyMDQ2MDk2NmU2Mzg4MjQzNmFhNmRhZGZhYjI3MmZkODkzOGNlMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjUxfQ==	2014-07-16 15:57:16.777956+00
1kcb6kdxl9up0aa3setvjf5iv7vbc6w1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:52:14.162754+00
tujadxl1i7v6yelk47vulafjzu81w62w	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-07 13:05:16.197527+00
6kuu2f1c87dm1b0zydtulm0fvqube1dk	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-07-16 20:41:49.034613+00
3uhkeiuz50k3wy7sclfb1w0kd0hgivxd	NzU2NTY5NDAyNjRlNjcyMjQ3YTMzM2JjMDMxZGIwZDMzZjBkYjc2ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjJ9	2014-06-23 20:23:03.680743+00
1trs5fjrfam9loa1wlpe2k3487td7jrh	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-17 12:36:31.097864+00
4deojakrq9bv7m0zhfp3oct7fupbrqi3	Zjg5Y2U0YjdlMTMxNjMyMGQzNjJkMWJiZjQzNjJkMzk0YTllYmUwYTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU2fQ==	2014-07-22 15:13:52.379115+00
3ken58k4o8nfg9agngc3eu9283cebdsk	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-07-08 03:36:02.923486+00
o4leti7sk77s6vio5otmvn4kmwh5tfzc	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-08 15:33:57.381914+00
1rhzlmbhwgulm4r47gmmpomkpj72hjed	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-23 12:07:03.475963+00
zpxk0ee63c8o32g7n1w79zhtpyhi2h8d	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-08 17:05:47.90783+00
yivi3hczb016c13o09f2h0htufyp08kn	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-25 16:09:11.700333+00
yi7t2dcfihv43tyo9gaqmqcu026ck0ny	Y2YwOGI5YThiZDRiMWVmYjMyN2ZlMDdjMTEyYjZlNjgxZmU3YTQxYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU3fQ==	2014-07-26 22:38:14.726613+00
76dgsrvqlprwsq5v3cj2lhsy71jad0qx	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-07-09 16:26:11.100351+00
cydb8467zrqk4ax7iw93cih8runjmzll	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-27 05:04:31.185932+00
06hcw01wa9iz23ooofrpy1lq3rxhv5vn	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-19 18:05:20.702408+00
cntm0xduasknl0yw3l6c4rfy7ahmxdgp	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-09 12:44:24.965349+00
lsmxqlw05x9f9uloxe62twqootbbn8rw	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-06-02 20:20:58.245613+00
cs0mf98vwoc2pax8f0gjxi6rqrwjlxg0	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 02:44:32.214281+00
8dg9qh25dnfudwgpsprrufuuewvt02ws	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-11 22:21:20.35476+00
oexnkowjky7ztl8w4twy13bpdyjablao	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 14:04:02.406037+00
2f1yj21nsiwo7w1j83ie2wfecesbtd7m	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-20 22:19:04.79546+00
8gik9yj8tppp6v8hcb015akdrjgexsq9	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-25 17:34:35.455896+00
k05tdo6g410rc00bkon25dcidwdl9yho	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-04-24 22:34:21.217653+00
8mag65afpwwxkinqomjqqrzko4nafehp	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-02 02:38:45.558486+00
5ugziyc6p2meh30m7c2p2embfy7a0zzf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-26 14:58:51.483159+00
4j4zxsszx8z1ic31hfno55hgsc8f6wxx	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-07 05:08:15.420443+00
lu3a2gpe7cqije7fzxmasal7k22vrgnr	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-07-14 20:51:10.513755+00
iatpbhsn46uxpkjc5qzfebfalk3wx1up	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-06-27 14:49:46.456873+00
yq977f9gv59h4yz0yfkg9clk00he7pjt	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-06-27 16:21:37.484714+00
0ngds9ari4yirwoa8j1vgo6r3lpw91m4	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-02 01:43:26.253717+00
lerexo4k2nza3j2x1r25d3a67m9b4nue	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-06-27 17:58:03.071956+00
9mjm2wm120hb33e4q6y6xqoa51lfmyj6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:50:41.497681+00
3xqkrydc0y1v4cnr4ptayj4az5mxbhfz	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-07-16 14:40:06.945965+00
y4j0s6m9rfs5o7rh47hnizb9pkl0wrtw	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-05-23 21:07:56.123597+00
p0hopm8wcm9hwccdc2r33zfwip5hc0yg	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:53:24.756195+00
m2k8wj2uwxlulewpoh2fr7p5eke1g6pg	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-07-16 17:42:23.412194+00
zpel3wby5p8crf8v0cuv2yytf0itqhlr	ZjM2NmMzODA5ODEzMjhkODA5OGMzN2IyNDM3MDM5NmUxZjRhZDU4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM5fQ==	2014-06-27 19:56:21.7196+00
vg4vjb2j3g21cymab2fztnl1viqf34vg	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-16 21:11:38.19139+00
inq5t1dus2swg1o2vqt5lcoxeuw69xre	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-06-27 23:20:04.744918+00
k1791ck0rpkjipcz4t533rv6186trpe5	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-22 16:59:13.452065+00
300b22cp5ddi09a8ef3r72f0xk0qgqso	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-06-30 06:28:37.297984+00
lk8htw9tk2uk74e8ruqj6ndqcnp3rixx	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-07-23 17:23:20.132695+00
erbftxz69mxammssuabvqcpxc8cgg86y	MDYzOGUxNTc5OWU3MDBhYjNhZDg4MDY0MjlhMDEzOGQyNDQyYTFmYTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjUwfQ==	2014-07-08 14:54:20.302218+00
domg9eh1k57y8rt4qnatf3epwz0twa4p	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-07-08 15:37:13.961276+00
tfeykt8a3zjqlbmj067cym5vz7phl14i	NTlmMzQxZmNkMzA0ZDhkMTExZjQxMzU5N2FkZmZjYWNiM2ZhODBkNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjUzfQ==	2014-07-08 17:58:54.669689+00
neixfapg6qt3techsnuc3m3ywdq0kpr1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-25 16:08:18.161645+00
b8pa1xmcyhm85wn1q6q2wb1mrmp03izv	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-07-08 19:22:31.075655+00
n5e9gyjc4sson97z0pcrnwws7azj07h6	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-07-26 18:33:23.599753+00
0ryrwda8zd5ul07g5xnw8ws3g7yir1j5	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-27 01:33:21.719451+00
0mysxkmmyc8dgfar1kcoiaxz5e4g92bh	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-07-08 19:42:21.223922+00
dprw2oigbbzcx4i7v6mia68g3kwukwuc	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-27 19:04:46.381434+00
dr3g4284hohjhp9h22stvr4vw0jf1s6n	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-14 03:32:46.330872+00
xynhx0ksj4km1wpwkx7fmc3x7qqiz5q8	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-04 13:04:49.435771+00
b2m4ja8ztwbvrkiqtjplioq1vonimte1	N2RjZTc1ZTdkNzRhZDVlZDc0MzVhNDU3NDU4MTAxNDFiNzYyMmEzNDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI4fQ==	2014-06-25 16:48:49.285633+00
o73jrnucpyje1krqua0qbcvr03vctb6m	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-09 20:11:36.419072+00
g5lxhfruqtkb8rxnjosu8lry34fu7cro	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-03-26 15:36:58.594348+00
509dmh8bfic5t6z4qz7425nv8py5mgxw	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-30 18:50:38.541232+00
em69vk6mvibj0oyb0ise66ta2vwcjevq	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-04-09 21:25:29.165707+00
914gw3cza0x8s3ltdkp3wee6eunxvmbj	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-25 02:24:34.43365+00
1s2coo5ii9ooz97r5kj4qvv6g954iroy	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-13 20:04:32.578327+00
axbs8td5eepp1t1e2yazgy0s0yvzkt33	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-20 17:24:24.355476+00
v8bv3z9iiiwjg2scwosmspy0kvrxv85n	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-03-26 16:28:26.608748+00
wkbvua94fg0d1sukodq72dsjq4qjlwas	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-04-21 17:15:26.919868+00
2eb1mlwwshivx404021k0dmxudbi63c2	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-05-06 17:47:14.483388+00
am3k3y0bcwwrm4gy9o6enmttgsz6qdiu	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 04:16:16.746419+00
6k503vt9ajvxg1lfky2pajdr3loxntdw	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-05-08 21:15:41.055955+00
g7wro61fv7wl6ptnsf1dx8abr61qkv9x	ZmJmMjAzM2U5M2NmNDRkYWQ1NGFkZWZkNmFmNjY1NTZjMGQ2NzQ4ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMyfQ==	2014-06-25 18:05:16.991717+00
9ac05w0h23grhyv39951kdbd1fi0d7qh	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-12 19:00:15.016649+00
p51o31jmp1hnq6dl0t27qzcpsoxv6v1d	N2UzODBmMzg2YzY1OGU3MDk1NDA5MDFmNmQ5NGVlZmU4MmY2YmM1Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjN9	2014-03-26 16:31:04.366811+00
hmp3yccc01qxmfxkud28k5bf819cvuo9	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-01 14:56:29.308851+00
iqa5lrxq1oeibpskedf9iy0ldhbp58qx	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-21 04:11:14.735604+00
7fi4khzisttrqpi06438h3xdyjw13cix	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-26 16:33:05.487359+00
gwpkv4ro27qx2mbekjjky5ydhcp7sj3z	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-05-13 21:15:51.603611+00
ap1vq6215xi7md0ydxnu2jjszyzjuiyn	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-03-27 01:26:20.200585+00
ztqjqj79ebmmiveni7r1xc2qoyepwf2x	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-03-31 17:18:55.775987+00
0yns8mxt5jg6q1y5nqy1faoq4ubaim0n	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-02 04:09:35.726824+00
f5ypbfhda7va1ndryg0omtadafuh4ren	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-06-23 19:07:30.433163+00
u3v0crcvmiehn322dd9dwph7n0g5jkv6	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-04-02 16:13:22.274201+00
h5qc5terfvmr627pl0d0ynt7169qcb3n	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:47:13.733766+00
6b13sdrfr84867u7q99qd51ez8rjswkr	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-05-21 18:19:00.352417+00
epcsrkf9y0rrhdkjet371gmdyd07t7ai	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-03 11:50:12.743579+00
4swl0ekjisxpj8lok7z7rrhfh519iwy1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:50:53.71061+00
w7haixpumvmc8qd9cayi667iqniuep2t	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-03 11:56:21.159705+00
n7ku873s40dw005pmt073yszu17iaasb	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-06 14:30:46.369229+00
4ydacy0khrzg5lh6uqqj8ancrk06doeo	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-23 19:53:27.734894+00
nvs3f3bc5qkg1wdlu4qkatoe7ubqt7wz	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-04-07 22:17:31.327026+00
fhd6o7x2i5o48q1monldogkoreey3ztc	ZjM2NmMzODA5ODEzMjhkODA5OGMzN2IyNDM3MDM5NmUxZjRhZDU4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM5fQ==	2014-06-27 19:56:41.817047+00
vddplf5ss9irp2epzr1m8dmsfj3je90a	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-06-27 22:34:29.086988+00
sfljqkj7qyl2t6r7tz119jtmd25erw75	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-06-28 20:02:58.340198+00
n53vkid7q359qr6nklgrk0x1o5pqoeyg	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-01 11:39:47.374268+00
n6srw5ehog7facstd9dqa1l3akcrqdss	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-07-28 15:58:30.467789+00
da6illd5j3kpfxm0zqiet3nrbo6ojz3v	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-08-13 18:06:45.682423+00
uakc97isaovd1uliw5s8sblx6uxxv0n7	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-08-13 19:35:36.529465+00
jjqrsw20utv1j063o9kkxa4cua0ct7th	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-07-28 16:20:09.593915+00
a4cf7tieu4iwgjks3facm3458e8gkelp	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-28 18:18:59.262882+00
cfe1bvjg1y6docrmvlj02489ayeyjy6x	MmVlYzgyMTA4Yzk2NzI2YmU3NTlhNTA4YmEyNzBkNzkyZDY2MGIwZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU5fQ==	2014-07-28 18:34:09.917316+00
3bwmvg14o14z7bvjzuzohglcqmfjdfh8	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-29 13:31:00.098118+00
ewoasnwd4ldiaxs4fkr5t6feecm0pz9c	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-01 11:47:20.53883+00
saq6guus8tnoyd5vwlv2x66yx58krhdo	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-07-29 17:29:50.994445+00
fdetdcgx89d2a748u7ihm9snhmfh0a6b	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-29 17:31:09.247578+00
sxdawf3k34p8xtww86170s4a2m6o56m2	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-07-29 17:47:11.123567+00
brvb2g9cr01d5zzui42naazl4qybldxu	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-03 01:14:01.836106+00
k0g671uxd7u14adrck24lw5pr0t4hoqr	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-29 18:19:29.134247+00
48gmbe4or8t4t0l5fxq90xf1i19f7h8x	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-03 06:47:04.571821+00
liaaawdpgtzyvsrttf6wst1xz4lxd4oh	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-04 12:59:12.458343+00
pzc6efbp8kz5lv0fa83eoxnd6ntvu67p	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-04 12:59:58.968797+00
vdq03wdix5scg2cv3wv1e6rqr2z3ympx	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-04 17:43:18.669105+00
668v10lhuqzkidjc0xezobd3pptfxe3l	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-29 18:46:59.38163+00
u9tt72xfbvfqgxw9jrmuqla3f1vn883e	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-30 13:49:38.074084+00
6puzc0paemi30u1vreqk1iwvbawmlu49	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-08-04 19:07:49.648853+00
c7c3lyisammx5fv8og4m2hzq0molk83e	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-30 16:30:18.20293+00
tvqz220v8237kzl7lwl4orjrsfau05pi	OGRiNzdmZWQ2M2RlMmY1YTQ4ZGIwODE3MmRlYjBlYzQ3YWQ4YWJjYTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYwfQ==	2014-07-31 15:39:23.959722+00
hk446ythqtuft4tczvx6njiab49dwo0t	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-07-31 19:27:38.667517+00
25af7w1mf00gzhiqrgw1t6b21sghl1mb	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-07-31 22:32:03.01745+00
icvxoba08rj0e669pvz2xr4l58f8yypd	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-07-31 22:37:20.915301+00
2nl0aqpj8z2t15srhehpbkrkevq0oynj	Y2YwOGI5YThiZDRiMWVmYjMyN2ZlMDdjMTEyYjZlNjgxZmU3YTQxYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU3fQ==	2014-08-04 20:42:17.202324+00
5n1yf63y5t2u9po645lruprnmg5ofdi9	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-04 21:12:40.111254+00
xmc1lruj4wb263pv9e5rvxin79l49qmf	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-05 04:38:19.092039+00
5txtp1x01zdicnfu38478gtpildjen7f	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-05 12:25:00.642395+00
f5afwk52z0abozjse286fonkedxpjqnj	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-05 13:51:06.684156+00
hxk1pyrx7ysgt1vlt51i7f7nde6eytz2	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-05 16:22:49.060708+00
ecgo1vyhmay0ego2w89ahjuot43j3f5i	Y2YwOGI5YThiZDRiMWVmYjMyN2ZlMDdjMTEyYjZlNjgxZmU3YTQxYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU3fQ==	2014-08-05 18:20:58.500323+00
fj2uuajfiqel7ot9boegroxrv18jzeji	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-05 19:46:34.254734+00
t46zrjpwx4mvmfa0i04zvm8xypln2s63	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-09-08 17:51:27.201586+00
wl6k5bpre3wx74ya9mck813fqgrnfspu	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-08-13 18:05:24.310555+00
04uybif2763t3e55un3wda442ju10cop	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-09-09 15:08:39.585618+00
fjdgdoo6drhq7p8fh6fq86woia98c8o2	OGZhNDBmZjY5MTk0NWViNWY1YTBjZDVmOGZhMmUxNWFhNDkzZTJiZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM4fQ==	2014-08-06 14:39:25.418044+00
h550nl43eiarcj2mpgselh9x4xo0e2d8	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-13 18:13:44.482364+00
3lwrzn2l6iez4hti9lzjwfuukce7qt3b	ZjQ4MzdhNmIwYTZlYTE0OWE0ZWViNWVlMjkwMWY2M2JhMzI4NDJhMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYxfQ==	2014-08-06 19:18:03.807605+00
xbp5ivpfs9hi9e6r1yb0l8wt65p0p4kp	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-09-10 18:34:39.512655+00
eteqar4us3ws7yzuy63ngw3eiw5qbx0n	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-06 19:34:55.608007+00
6jqy9yt8ibzorbsysk4ycdge7vbw5ab2	Y2M3YzdhYWQ5ZGFjMTNkNDYxNDk5NWQzMTI5ZTkxNTNmOGU2ZjQyYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwOX0=	2014-10-13 22:10:45.168163+00
ts4hhxu7pe5xbjfeckvnkkt6jgrkyodj	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-08-06 23:28:40.465684+00
ecmvcpn4yaob3uw8adp4lolk82ste0pb	NTdlMWJkNTg5NTQ4NDA4MjhkODE0M2YwZDBkNWUzMGQ5MGFiNGQ0ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk1fQ==	2014-09-11 23:47:17.030999+00
b6xrhtb5l1jz34oky06axdmbgrh52etf	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-09 03:39:03.216025+00
l48f21axdanoun5nmnqv5rtgck2oecp1	YjlkYmNiZDdhMTUzMTE2N2U5NWZhNmM2YTIyYjUzNzM2OTU3MTgxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMX0=	2014-10-14 01:27:38.609868+00
jltwedk48chx5v4xl1cu6g8pgmxoc49p	NWE3ODg1NTkxMDBhOTI2ZmQ4MTY2NWI5ZjI1NDQwNDdjMGZkNThjMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjc2fQ==	2014-08-13 19:55:28.621201+00
cq41dc7znm6y31eu7vu4lomck08nvxgk	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-08-13 20:04:22.970256+00
ogperjgz38zrcc9w0yanmpcec6ii2ppk	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-13 20:34:41.033286+00
fj1xjda60u08ol83a48buvfgqmnt4y3a	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-11 17:24:05.11747+00
evxq6jdvcdenl2f10dc2cvp8a9q7tti4	YjViOTk4NDEwMmQ1ZDEyYjAzZjY4MDUwMjAzYTE2OGQ5ZGY4NmYxZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY3fQ==	2014-08-12 00:07:06.236045+00
ki9t7fsugtqzuot4nbzek5krj7mtfptv	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-15 06:09:59.647076+00
ehtpz7swwqvnhtn5aqsvx9ulornzc0zh	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-12 04:31:36.85429+00
mg4t5uxa69g29l23otfsm1yjfqg3hydn	ZDQwNTYwYjE5MDNlMjlkYzNhNWIzNjIzZGFhZjM2YjZhZjVkMjlhNDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY4fQ==	2014-08-12 15:08:43.493443+00
nn0eww2qyxd519074orbdcccjnusltos	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-08-15 20:46:15.785135+00
rdca9l6qe8enq8s6ejxvrte36rkp6048	MWE4ZDJmYzQ2NDY1Y2EzOTY4YjMyM2QwMThhMzFmYjc5OWM3ZThiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjl9	2014-08-12 19:55:16.550153+00
5erjhilpmueze80qcb10cko2l0xgohee	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-18 09:25:52.063202+00
5xyofs72os39pn1uv5mwk31ov4y7pt7e	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-13 10:59:08.093563+00
7apjq342jqs8sekgxpbdof6qwmfrlzkw	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-08-13 14:45:56.493052+00
215p32mpvqspaoaj79qcy3f4mjuf5bmi	MjYwYTBlMzQyNjAyOGY0NWJmNDgzZTU2MWJkM2E3NmExZjBiYWJiZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjgyfQ==	2014-08-22 13:00:56.811291+00
njvutgqhl21cb7i98mt3qf3dl2yh3j25	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-26 21:36:25.780522+00
6vsnia6dhn3umt6bryn3bbe1fzhay5gh	MWNjYTM5MzVhMDE1ODZjYTBlOGUwZTE4Njk3NWFiZWIxMGI1MzYyYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjg2fQ==	2014-08-27 17:21:53.366597+00
yfpeyi91xw0w6b2v2lknqb66nxg5nni6	ZGYzNDFlMGU3NjdkMDZjMzdkOGExZjViY2ZjNzA4NmJjYTZhNWE4NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjg4fQ==	2014-08-28 02:52:19.657308+00
vglfrtllt4a4holsyccj4m0ydh2iv2sb	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-30 13:58:57.395235+00
v2w8t1lmgfzrmbxx33zm7zeqobxf67i1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-01 18:52:35.699563+00
gdya80chj3wrn9qaxu2eg8sfvs8mm7yr	MThmNjExMzFiNjU3NWNiMzMxNmU2YzFmMmIyNjAyNWJhYmIxOTFlODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkxfQ==	2014-09-07 20:25:15.74423+00
3ihrd68o8bk3icsndd5ae1w240ia2dzu	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-09-08 15:26:51.044385+00
jlnhkv3044j06opnfrltbfbce4qqe0nh	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-05 19:00:34.050482+00
ldz52iz3t0gtr88r9tst61vs319uh12c	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-09-08 18:38:58.823111+00
rt6xg4w7ll7kjmpezi6yzist1saqoqbk	MzhjMzAxZjk5ZTE0NTM2NWZmZGE4YTY0ZWNhN2ZlN2U3ZTJkODdhMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMH0=	2014-10-14 00:37:14.36443+00
b0y0rktoar582zk762l9to3q028wninj	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-06 05:09:59.503241+00
t5m9m2szz3scq6qpxi2wfxmtdonthd43	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-09-10 02:28:25.249571+00
hbqh8w1k3zo5faae34nuycl5tq0vdrq7	Y2YwOGI5YThiZDRiMWVmYjMyN2ZlMDdjMTEyYjZlNjgxZmU3YTQxYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU3fQ==	2014-08-06 15:20:53.115879+00
06jczy8iomkft671ekw5cvg9uslt7487	NWYxMzc0YzBhYTA0NWI5NDhiZjk4MTFkNWEzNmIyNTZkNzMxMDdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYzfQ==	2014-08-06 19:29:52.158322+00
rdsxtguemiy6g40iooqwpa9f73z9nmcu	YmViYzlhNWMwODMwZTU0NTA0NGFkMTAxNzkwNTI2MDgxNzA1YTdlOTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjc0fQ==	2014-08-13 19:46:38.337921+00
of35b1f6g0g1wiz7w7n9ex0s5nmroi4a	YjQ3Y2U5ODJhZDQ5NjZjZTgwZmNkMTJhYTcyMmMxNDA0NDJmMTE5NTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY0fQ==	2014-08-06 19:37:26.423598+00
ohu0mhdhn7pcvo4yb5sbc7rgx4jeewsr	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-08-13 19:54:52.846155+00
sfeqmo9xhs2yf7ytonaohoy41qcf90bt	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-09 19:06:31.205207+00
3pn182potaggsj5k8foqmy24ja9uzzb5	MmY3ZDk4YjJjNzliNDFkMGE0MDNiZjJlOGIwODA0ODljNGExMDExZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjc3fQ==	2014-08-13 19:56:32.786537+00
x4677j4gpqk5s9lvt9g0a20vdd1oi07k	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-09 20:38:44.069729+00
sf4jphner1ab5w5z5lcatx6zilnbiog3	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-11 15:44:54.006134+00
d0piruawdffweiuj182xwgqn4zq93nok	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-09-12 18:29:57.360695+00
i5wadkhiduadntuttslfvwwe8vmhz39r	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-13 20:39:50.021399+00
c2nfavzdgu38byju94gl2semu3vj6oey	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-08-11 13:31:14.097764+00
eh71ysr7btqupv8t3svqlcea8x6dd9g9	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-14 01:27:19.068036+00
mhl7kyt7dbv5w8qy8f1mtyfh453j4olx	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-17 21:37:43.892506+00
mgjr7no39a6ow099ct9m1nca9o2hzuij	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-14 18:58:50.776406+00
sphgx9a2x750ss0foxhod5vpyv4h2n5c	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-12 03:14:24.380267+00
kxer3eiw6mlhm0l8n8mzb23kmyf4mf6n	NDFmMzM2Mzk0YmFhM2IyOTIzYTZkNzAxMjg3Zjk1MTRiM2JmZGVmNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExfQ==	2014-09-19 18:05:45.815977+00
iz41o9swnvbmo2v6mz1cqlfemtsxj5d5	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-12 13:05:20.960465+00
539ifc0b745k08ddc6vdusphc6yz51cy	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-15 15:12:17.006329+00
7aw7mmckifvv7sr30rv6z1bc0e65beay	ZmI3NjNjOWYxNDE5NGQ0MTdlYzE5ODJmNmM0MGE3NTliYjQzZDI5MDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjc5fQ==	2014-08-19 16:38:19.522698+00
lxz8kj0ipdanq1t84z8aq3idsl6kh75i	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-12 20:41:02.636086+00
5heszqnmzdlomucg78p71c06ep8nq3k3	YjViOTk4NDEwMmQ1ZDEyYjAzZjY4MDUwMjAzYTE2OGQ5ZGY4NmYxZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY3fQ==	2014-09-22 15:42:08.23199+00
iuweznlv4h12dmmyrwsp9rnd0a6qo7qe	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-12 20:58:54.127959+00
fvsx71t5yadz5t3fbogl76mc1n781e7q	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-21 14:25:49.968137+00
63keuh1w5ioe9y2xjp9s3rtix064tq8v	YjViOTk4NDEwMmQ1ZDEyYjAzZjY4MDUwMjAzYTE2OGQ5ZGY4NmYxZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY3fQ==	2014-08-13 12:29:53.569213+00
md8777teezh0oc8pqm894jgp5h4shsh9	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-13 14:46:19.368342+00
ua3vys39j47qwisvwfn6kbu0760rmub1	ZWZhZmZkZWE0ZmMxN2FiNjYyMTM1Yjc2Mzg3ZjViODY0Nzc3ZDg5Yjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjg0fQ==	2014-08-25 14:14:57.273608+00
tpbvty24u8g0xgqky698vy83tv6r9a4r	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-27 17:18:25.464256+00
dasvwgplu8224sceoirgyddj0i5dxad1	ZGYzMWExYjA1YzVmYTU5ZTE1MDU2M2EzMWQ5ODU2N2RlZjE5YTM0MTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjg3fQ==	2014-08-27 17:27:35.143998+00
sjuvehb2sctttuu6ct9jehcv2wj3uzq4	ODQ0M2VlZmU3NTQ4Nzg5YjAwNzc0NzQxYzI5MWViNjFlNWFlMzRjNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjg5fQ==	2014-09-02 15:04:44.596811+00
qq96ldec970fy7ivd60qkgg0t5uqy7ez	NjUzZGRmMTViNWNkN2Y2ZTU5MjJhM2U5MmQ3NTc1NDhiMzc0NWQwYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkyfQ==	2014-09-08 17:49:59.075745+00
32etopkfbe78848pppn15zb8jv4t86g4	ZjQ4MzdhNmIwYTZlYTE0OWE0ZWViNWVlMjkwMWY2M2JhMzI4NDJhMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYxfQ==	2014-08-05 20:11:01.74028+00
41lcxsbyu7ii54h55nkflhfwmqfzxp7k	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-13 18:06:11.35314+00
16s0xh2n107r3623jhzidn6tyeyf1d38	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-09-08 20:15:23.677051+00
53en123abq0dborps65tbcuk38pbpeuz	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-13 19:30:23.105858+00
1mdb8epnhw3tsxmsmx7lui5m5fj5n8u8	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-06 16:06:02.378017+00
cnka0rvv0t4zdosj0afirufhq4b4qzl8	YTA1YTAxMDk3Y2UyMTExN2YwNTcxNjgxYzU5NGE1Nzc5N2ViOGJjNTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjczfQ==	2014-08-13 19:47:26.850544+00
kwi7mg9oeegtdpr8vhs4wck91u7u32of	NWYxMzc0YzBhYTA0NWI5NDhiZjk4MTFkNWEzNmIyNTZkNzMxMDdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYzfQ==	2014-08-06 19:32:41.602135+00
enfidaqtfi9flot665evnif6grgpnhez	NTdlMWJkNTg5NTQ4NDA4MjhkODE0M2YwZDBkNWUzMGQ5MGFiNGQ0ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk1fQ==	2014-09-10 03:54:41.038998+00
jw27wqz64yhfgatputt2uoivs3c9kxyw	OTdjMTFmYTRkNGMwZmVkNzAyYmM5MjZhNTk3ZGM3ZWQzZDA1YTdmMjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY1fQ==	2014-08-06 20:02:36.974959+00
mkfq6iuo7idfp1b7s10a8air82czyttf	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-08-13 19:55:03.175686+00
hcuqnqfxzmgph0c6v1lco51ywssj9ka4	NGJiZjlmZDUyNzUwYWE4MTVmNzkyNzc2ODA2ZTFmYjM4ZDczNGE3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjc4fQ==	2014-08-13 19:58:39.16333+00
vdlrcfqqbxxe1nefcf16wy6ut51oo8tb	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-11 15:39:03.929361+00
wwo0o4ilj4b4zizachpaljpvy1v6d56a	MDJhZDk5MGVlZjZiMTNlYzlmNjMxZmY2MGM5MjRmNTY3MzI2YTgwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjcxfQ==	2014-08-13 20:29:13.209198+00
akbd5eiwmtl4ytqqdbduzuam783ywf40	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-09-11 18:16:18.551071+00
cueukqbu8rb9iavmoxxb3lq83cyf6du0	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-06 00:17:44.47079+00
zviqqcv4irgd3itcjo041tswjmvqk7gm	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-09-16 14:59:25.598589+00
dyk2pjcd10xg9ic8wys2ibw4ssoohkcj	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-06 03:39:32.869609+00
4xeaqtk4whoxmvuz6wtp1pzthz1g5tra	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-11 02:20:25.492461+00
5mzhivw8sa5hwrsyzvjpa1519xtgg3bk	ZTlhMWE3ODg1ZTQyN2NkNTM2ODA2OWVkZDU2ZTkyMjdlZWMyMDFjZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY2fQ==	2014-08-11 16:31:30.406928+00
7s6xgxbfqz0b6zzqb0p6otr7noetpjhk	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-14 18:58:51.094929+00
f3dbfk7zames78knzph675j5v3nsvibo	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-18 00:55:31.941026+00
kgf98sjz63uf0pqzlnn0y6akz0par2gf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-15 15:12:17.134189+00
99973ui211yo2gy47k5acp3o94jjl6ge	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-12 04:26:03.712924+00
jl0zvr48z120jep3tqn6pkv38tiih345	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-12 13:13:05.423034+00
uqqekisxnapwfnw2fknl3oeyal1r4jbm	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-17 20:15:58.947891+00
pe9ofqpofhc9qp3tobzyxt7r5yoyxvch	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-12 15:27:31.774539+00
et0tvnthtttqclizq9qf4ogs5de94u4b	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-09-22 15:22:37.135372+00
jb3h6n0i4gm9t5b0r0a4zyluqku0jbug	ZjZmOTllZTE1OTMyNjMxNWZmNDExNTM2MzFmNjlhYzdhYzYwNGEwMjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjgwfQ==	2014-08-20 03:11:12.454741+00
97ns9y7tvievg3qni6nwtswxvlxn4v7j	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-08-13 03:12:09.25684+00
edmo8rwwjtlrx097dok9moosekjrwnhn	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-21 17:03:54.607279+00
zh1m7cuu1wy6viuor3gfrlutd4dy81v8	YjViOTk4NDEwMmQ1ZDEyYjAzZjY4MDUwMjAzYTE2OGQ5ZGY4NmYxZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY3fQ==	2014-08-13 14:45:53.233377+00
p2dysr5i2sia29ayemugnyionbpdlzmz	YjQ2MTg5M2VjOWRhMTllN2YzY2IwMDQ4M2I0NWE2ODVmNDU5NGVkMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjg1fQ==	2014-08-27 17:18:59.42292+00
eb2fnhxgmr16kxyb91be31p0r09jbb8m	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-08-27 19:41:25.344418+00
oey1k1epo6t1ccpmj991l4lcskne6ejb	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-29 10:05:33.889631+00
hwy0ofmjvk0pnc0xkhpu78preo1rkbwo	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-08-30 13:27:31.250262+00
b9q0mukfydn71bauf0wi8mm0k44z47nl	MDc1MzgwNGZhYzkxZmY0ZjgwZTBiM2UxNzcxZmYxNjVlYWFiMjlkODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjI5fQ==	2014-09-01 16:32:48.494613+00
mtkypxywl01b87f3stq8bgeysgfo9vyc	M2ZmNGU2NTY4M2JhMmU4Njg2MjA5MTU1YzZlN2I2YjViZDZlNTBhOTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkwfQ==	2014-09-03 21:51:21.613763+00
om685qq9s40wxrgyy51hqkcj79hvt2u6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-22 16:20:01.869221+00
n8da76axvimzjusl8gsb0n0sghj2kuxo	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-22 16:20:40.622626+00
na7meko272qr67gpdfo6u0axcpq5q3ms	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-09-24 20:56:56.548898+00
c41s4gakqox39if2qknsqs9t3xand1dk	NWEzNmIzOTk2MzhmMzc2OTI5YzAxMjZkMWI5MGJmM2JjNDg2YjZiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk3fQ==	2014-09-25 01:11:10.632658+00
4y7v4safodivvtufi1d9r43f3bnqn4d3	NTdlMWJkNTg5NTQ4NDA4MjhkODE0M2YwZDBkNWUzMGQ5MGFiNGQ0ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk1fQ==	2014-09-29 06:14:42.524226+00
amcxxa91zkf0uscbsgf9a2krkmzwmyot	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-09-29 15:32:18.497731+00
0ed403og92tqfx01sfzitqqa458m02c6	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-09-29 20:27:55.58405+00
2cc2x8cmkvd4xj9qfbcsk0lo8uebkpi3	YzIxNjMwZDQ3NjJkZTliYTViYWU0NDc0Yjg5OWMzMzEzM2RiM2UwMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk4fQ==	2014-09-30 21:05:34.88265+00
e91dhqd22s12n38h4cz1olzfpqpgy7d8	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-02 15:39:33.218704+00
xi1zpej0khee17f3oi9idkztoxyvcu4x	YjViOTk4NDEwMmQ1ZDEyYjAzZjY4MDUwMjAzYTE2OGQ5ZGY4NmYxZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjY3fQ==	2014-10-02 16:16:45.526353+00
3vf3msrl89tehpb9lnnvfo7m4fiwdx0v	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-10-02 18:30:21.871353+00
8cwo8tg5el60lu8h34divg84x06ubgxg	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-03 14:25:07.261741+00
0ald4yh4v0f23517y7wzrg0gzkwy75hk	NjdiOGFiN2U3NWJkMmUzZDc3NjNhNDBkYTBmOTFiMjU3MjM3ZjNkNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU4fQ==	2014-10-03 14:25:17.665413+00
pcf7irwu4zxzw972eyj028rcvg7e36ki	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-03 23:21:11.90551+00
8ilxh64dd0102nnj525ydc5hgvw06q00	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-05 01:28:56.343283+00
7a1nkqr9uu3rjqxgzepsh6h09tj52cfv	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-06 13:25:55.205882+00
m3qy6dl3farruq2pe9kumyys058cxhie	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-06 14:06:35.489261+00
wxzqy62vfes47d2esp782qbc0o4zlii9	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-10-06 14:24:37.953829+00
3k59dy8ocj5678nvk6h0p9zjzjsfupst	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-10-06 15:11:02.509655+00
213n304r1yycwrcihcq5v7vy4lntrjv5	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-06 20:21:30.36269+00
h8j87reozajmom71xk0q7rk58vkyamkb	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-08 20:27:44.727917+00
gdd1afl3g36xv4q0lpygbwli2m8zxd4m	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-08 20:40:29.007105+00
1kqys5p52ka0r13m48hvhyoo63gbldp2	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-08 20:43:11.374102+00
q8yahd9wd927o2mg2a2h5vfklngk8if4	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-08 21:40:25.622771+00
vjao66jcbhjqtgl2ed6mymymwg1p48fb	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-08 23:44:27.600312+00
3e5cb1k95bosgq4u6frr5g89hu1a6mdi	YjBjN2NhMDViNDg1YTdkMTk4ODUyYmQyY2IwZWI1OWJkZjkxN2E0Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwM30=	2014-10-09 12:17:04.235588+00
yz9liuways9nz6dt9z9a6ug071z6x1i6	NWYxOTQ2MDg2Y2Q1ZDRkOWYwZGEzZjAwNzI2OWNiNjVlMjM5ODY4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNH0=	2014-10-09 13:10:52.063498+00
9mxpv5yu36uohx0e1ve19gnwx82p0cjy	Y2EzOTNiMjAxNWUwZmVkZGM1ZWFlMjRkYTAwZTA1NDlkODUxZDE4Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNX0=	2014-10-09 14:24:14.273962+00
02d78ucnmr4ghbij592unlzmm8zv180w	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-09 17:32:16.940818+00
bziuc99p42ya9anl9rckiuarbibch1pj	ZDk3YjhmZGQwNmYxMzFlNGYyZTc1ODc4MzVmOWZkNWU3OWRjMGI0Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNn0=	2014-10-09 17:33:39.87785+00
0htr3n3t9pleoh3gdsh917ct3zkzf3xi	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-09 18:15:05.091509+00
qn1blt393s1sizxc4cwpti4mv0q4qad3	NjUzZGRmMTViNWNkN2Y2ZTU5MjJhM2U5MmQ3NTc1NDhiMzc0NWQwYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkyfQ==	2014-10-10 16:23:53.853102+00
boqiuix262txtmlhyarfncfad3d5tkk1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-13 00:32:27.852789+00
ye1rm2xaphk7b44802kqn2tc827fu48a	NTdlMWJkNTg5NTQ4NDA4MjhkODE0M2YwZDBkNWUzMGQ5MGFiNGQ0ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk1fQ==	2014-10-13 03:47:15.654182+00
ijw6ibyofa88up4cjsm8x4psyuk53xnq	MzhjMzAxZjk5ZTE0NTM2NWZmZGE4YTY0ZWNhN2ZlN2U3ZTJkODdhMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMH0=	2014-10-14 00:44:55.456348+00
43xcrjmzmsgtpzkmc3agjevyadm74gxm	NjM4NzZjM2E0NmU3N2FmY2E2NzMwOTkwY2I1YmMyZDdkY2VhOWU5ODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwOH0=	2014-10-13 14:37:51.038379+00
3fozn76iyr2cg0ecsxy3cjxmot5xjpr6	NDI4YWQ2MGMzMDRmMjk4OGFlOGViYWFkYjdmOWJiYzY0NDE5YjVkMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMn0=	2014-10-14 02:51:58.121985+00
at2n32l9l5ccrodaz4p2p1i1b03y5kks	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-14 16:44:55.311593+00
nvg8964o959pjk7owgyn6y6hjohluhra	YjBjN2NhMDViNDg1YTdkMTk4ODUyYmQyY2IwZWI1OWJkZjkxN2E0Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwM30=	2014-10-14 17:09:32.217543+00
2g118oxzuk6i0qbopbfbwfx49cptk7ti	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-10-14 17:49:17.899303+00
vrifhj75gum37h5awwu2l6daq0kpnc04	YjlkYmNiZDdhMTUzMTE2N2U5NWZhNmM2YTIyYjUzNzM2OTU3MTgxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMX0=	2014-10-15 01:51:17.747828+00
pwajor8aqws287g7bv425n5umqxifgfg	YjcxMzQ4ZWJkYjdjNWYwOTQ3ZWFlY2QxMDdkOTRlM2IwNmE5ZGZlNDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNX0=	2014-10-15 02:03:23.301672+00
xvzgqfa37zhwpuf67uw32djbxugfhw55	YjYzYzI4YjUyOWU2NzY2NTdhNjdhZTIwYjU1OWUzNGUyYzc2Y2JjZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNn0=	2014-10-15 02:17:59.64114+00
cxii8tcqzhszznhpyksfva3ksdk1eicz	OGUwMDA0MjUyMDZmNDUwZWU4NzBmMjk5ZDBhYmQ2OTJjYzU5ZjQxMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExN30=	2014-10-15 04:17:17.219774+00
k2ewv8fmgabtv0qvpxkfh66im76oc74i	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-15 11:00:32.528285+00
alvtgh4fbdd5xl57yy6p4v9b7oekaezd	Y2EzOTNiMjAxNWUwZmVkZGM1ZWFlMjRkYTAwZTA1NDlkODUxZDE4Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNX0=	2014-10-15 13:13:45.003151+00
t7nq10nnmvobxnzl5foehi0wj7361hvf	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-15 14:59:07.905905+00
sc270nip8oifgm7e0nsdyv8krnvsm0bs	NGU4NWVmOWI0Y2NiNTcxNzk0ODk0NWZlMDQ2MTg1M2I3YWU0ZWIzZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExOH0=	2014-10-15 20:30:11.09126+00
yhht56m9vu6kkyvoedsb0ddy7lqswvy6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-16 01:50:54.715818+00
crw08z1470qwu6r0svvbsm2ipd6d2peh	NGMwYTNjMWZmYjM5MjYwZmMzMjBiN2RhYTBlZWMyNDViMDFlZjU5ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ3fQ==	2014-10-16 05:58:34.367083+00
o07nrnn9i5tfklyom12hraeuquysjlog	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-16 17:11:24.466234+00
skx40y10sihbj0remsz5trb9bz1murnp	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-16 19:45:45.760133+00
1nevs16sck76v3ntg80og4akcsxah9lr	OGUwMDA0MjUyMDZmNDUwZWU4NzBmMjk5ZDBhYmQ2OTJjYzU5ZjQxMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExN30=	2014-10-16 22:53:52.076915+00
0q0kcikysnjosakljz4z43f5d6cffwhk	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-10-17 00:46:23.808199+00
59shhkkigmk61hzlr7s02auqhxisla5f	YjlkYmNiZDdhMTUzMTE2N2U5NWZhNmM2YTIyYjUzNzM2OTU3MTgxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMX0=	2014-10-17 14:14:35.123756+00
1h19lajjz105wgancfc6ksh87mpuh3sq	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-17 19:00:41.918848+00
lzdv78u80pdcjv4zy4hkr60n777tmhbw	MzhjMzAxZjk5ZTE0NTM2NWZmZGE4YTY0ZWNhN2ZlN2U3ZTJkODdhMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMH0=	2014-10-20 03:54:29.887083+00
ic5frbwk2pb28y74hp4sibnei6iqtabq	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-10-20 14:32:21.111527+00
fhl99l0se0i88wl8vhmk13ffrppn97uj	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-20 15:46:54.367185+00
rxx4e7wq65sft850jx98bjo28rnviuot	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-20 18:17:57.805931+00
rte6sll33s9kagjjjaxur4erkle99evm	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-21 10:33:37.554964+00
p7vd7djvj6ynch3hsd792uj0xpu2pood	NTgyODA5YjVmYTgyZGE1Mjg1MjkyZWZiZTUxNTE4NjI0OWRlNmRlNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyMH0=	2014-10-22 06:59:32.523788+00
a1j8avlpi8j7v41bm9r9d0ma0el99hx5	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-22 17:18:57.071066+00
2tu1e8vzpzwf9qx23xrqkoti5vz0p6zs	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-24 02:37:54.062532+00
udv0nw34www27d74eeq6f9wuaac8sdc7	NjM4NzZjM2E0NmU3N2FmY2E2NzMwOTkwY2I1YmMyZDdkY2VhOWU5ODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwOH0=	2014-10-24 04:05:06.440372+00
0opciwsx0z1q6g52mj540x5xsrjkexvr	YzY5YWM2MmNjZmZiMWM2OWFhNmIyZWI3ZTIyMjJkMjE1ZTc5Y2M3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyMX0=	2014-10-24 05:34:19.35516+00
2vzs110edcuxv1at7altoc91okoc0ro2	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-24 08:58:05.359402+00
yqmp4g8ajzkqp5dop8c7vyjpgfxg08e8	OGRiNzdmZWQ2M2RlMmY1YTQ4ZGIwODE3MmRlYjBlYzQ3YWQ4YWJjYTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYwfQ==	2014-10-24 17:37:12.983991+00
o2bqszawm73eydn0829htt3b128t0ts1	OGRiNzdmZWQ2M2RlMmY1YTQ4ZGIwODE3MmRlYjBlYzQ3YWQ4YWJjYTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjYwfQ==	2014-10-24 17:41:11.801522+00
swkagrv9920l8sgznowawulpuo1t9e2w	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-24 18:51:53.116371+00
6ukx3kva0lnjth4l3w367v9mrf1zg6j6	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-27 14:51:01.716351+00
0ag23hgtxkk22rk8i0gldpglmiyptczy	NTlmMzQxZmNkMzA0ZDhkMTExZjQxMzU5N2FkZmZjYWNiM2ZhODBkNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjUzfQ==	2014-10-27 15:30:20.642996+00
v96d65dk3y6cibnjmha784q188rdpdru	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-11-03 14:12:48.808806+00
1bwyjug7jhej60zrv9nu4pfu65er68tc	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-27 16:19:41.84936+00
0p5pbgdfigj1dhgoymvs1qwml6y40euf	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-11-03 14:12:57.167767+00
2lo573hcj9zb06nz7750jhcgddgl30qe	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-27 18:34:12.845679+00
71ud71on9deq2i591a9btkdqfpqbcwul	ZDk3YjhmZGQwNmYxMzFlNGYyZTc1ODc4MzVmOWZkNWU3OWRjMGI0Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNn0=	2014-10-27 19:46:12.005246+00
jvrjh879kt736zvhfy5f6kex1wsud2p5	Y2MwOGY5NmYxYzRlNjYxNjRmMTkxYmVmMWM3ODk4MDJlMDA4Y2VlODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjF9	2014-11-03 14:16:18.530498+00
wl06uh7tojux64d65u7fabnsecannroe	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-11-03 21:09:19.38556+00
tpg0b9z830cuf75ip0huov9a4z90bln3	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-10-28 13:38:56.997388+00
8int0md0eifkutrdmfrwzw1p45m6418j	NzNhNmNhNDRiNTVmNGNlZTU2YzhiNmZjNGYwYjc0ZTFjYTg3NDMxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjM2fQ==	2014-11-03 22:26:27.645466+00
loci3ojylbfvouuvsprbqqtahv8l2wig	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-28 14:20:59.286674+00
39v06rhe2uplcx227gfvqful7lrh0ejl	NDI4YWQ2MGMzMDRmMjk4OGFlOGViYWFkYjdmOWJiYzY0NDE5YjVkMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMn0=	2014-11-04 16:06:06.181625+00
loajaic3in1gzlpoucjjw09uo8jw59hz	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-28 15:08:28.844057+00
7w4oybpjpqmqnactzjcyf8otgdi4kp9u	NTlmMzQxZmNkMzA0ZDhkMTExZjQxMzU5N2FkZmZjYWNiM2ZhODBkNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjUzfQ==	2014-11-05 14:53:11.611928+00
rfewzulsh060cwi6oexm1b25uznm9y2d	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-11-05 15:42:12.821134+00
e0z7htv1zu8wihi8d1zzbj45peh6wwfr	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-28 15:27:20.323589+00
h770vhxuovddm09kr543sry62lrijbvf	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-10-28 17:56:20.916472+00
y4kw408le9kgrxvgp57wcxqyprslesnn	OTg5YjE0MTI3MDliMDMzMGM2MDI5MDZlYmE3ODUwOTA2YzhiOTYzZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjMzfQ==	2014-11-05 16:27:45.904148+00
7d11wjdwbbkpodjlsimjugwy4sj6jt93	OWRiY2FlN2JlNzJiMGVhZjQ5MGQ3Yjg3NGJiM2JkODNmNDkyNzM2YTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyM30=	2014-10-29 02:10:55.806306+00
edsghvc24pogvaa2sddvcj06nypqj7ah	MmU2OTBjOGE2NzM5NWZkMzRmNzdjNTk3NTQ3NDFlNzUyZTUzNDA2MDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyOH0=	2014-11-06 14:49:51.965585+00
om0w5y1fn2pwndcz2rs5qcakqftuthne	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-29 13:38:00.039885+00
xq0ib09a8v72gy909t383g2m9836q1bj	NzU4MjVjODM2NDJhNDU4MzY2M2MwNTZhZDNlMWUyNjQwYjBjZDY2Yjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjU0fQ==	2014-11-06 19:35:56.860966+00
6h9y1z8a28sbthyneofgrhtxkpwmfzv2	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-29 15:18:09.01602+00
sg0ypbzy3aqper8t643np7id00b98p6e	YjA3OTdhODgwNDFlZjEzMjBjM2EwYjY1ODNjZGUzZGViZTQ1Nzc3Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyNn0=	2014-10-29 17:52:49.757253+00
2c9pk3qof7icuzevbhl7457cd5u512gf	OWRiY2FlN2JlNzJiMGVhZjQ5MGQ3Yjg3NGJiM2JkODNmNDkyNzM2YTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyM30=	2014-10-29 18:46:43.746191+00
e2n3ubti2ddn9b59911vj270khxj8pq1	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-29 19:16:49.246269+00
jx9d73okfctjm5xgx10ufc7cxcizhsgo	NTMxMmQ5NjQ5YzRhNDk5MjMxNTBhNmU3OTMwYTAxMzRkNjM1Zjg5Njp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyN30=	2014-10-29 22:11:13.765187+00
szv96u42bbopr9gqcur6qxxdl256ey0q	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-10-30 17:50:29.404142+00
4yzkacmsavtko6wht48hjue9yw41ygr9	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-10-31 16:56:44.767078+00
atw59b5bundia3shbjrfagtibjmj9qeq	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-10-31 21:42:47.36892+00
swtc2ykpt9wvr6py9yumlhchzfqb610t	OWRiY2FlN2JlNzJiMGVhZjQ5MGQ3Yjg3NGJiM2JkODNmNDkyNzM2YTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyM30=	2014-11-02 18:42:38.7037+00
j993dmht03k602cfk627hpkt4hddsht0	NTdlMWJkNTg5NTQ4NDA4MjhkODE0M2YwZDBkNWUzMGQ5MGFiNGQ0ZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk1fQ==	2014-11-03 03:55:05.571245+00
jtabr872eq0t817bn558qoibjtu3itcu	MmU2OTBjOGE2NzM5NWZkMzRmNzdjNTk3NTQ3NDFlNzUyZTUzNDA2MDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyOH0=	2014-11-06 14:52:07.17516+00
jg92au7iz7pwpmvej27t3qwz3mlw06xg	NWYxOTQ2MDg2Y2Q1ZDRkOWYwZGEzZjAwNzI2OWNiNjVlMjM5ODY4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNH0=	2014-11-12 13:06:35.499645+00
gy87d1o1hxk766p751su6m87keij4s5y	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-11-13 17:31:19.793265+00
6wp94gciaxzgfmicdupmc20qycowbmzy	YjYzYzI4YjUyOWU2NzY2NTdhNjdhZTIwYjU1OWUzNGUyYzc2Y2JjZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNn0=	2014-11-13 18:45:46.089767+00
3l7wmoqc21c8pefef006qk05xvstup7f	MzBmNjNkNGJmMWVlZWU0ZDQxNjRhYzI2MmZlZDliMTFmY2Q3MDdkYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0N30=	2014-11-13 20:13:34.845124+00
h4uc490ku0hz4sv78t8yki9zzemyy3bb	NjZjOGVlZTYzMmQ5MGViMTBjODJkOTBmYWEyNWZkOGQ4ZDU3NjQ5Njp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0OX0=	2014-11-14 20:35:17.774709+00
gmnvs20iu6b9wr1jznxpk5pwmurpgwr5	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-11-17 15:36:09.784627+00
ayv76xvssomdlebdh8mlv8e0a1h11u0d	YjYzYzI4YjUyOWU2NzY2NTdhNjdhZTIwYjU1OWUzNGUyYzc2Y2JjZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNn0=	2014-11-17 16:45:08.406306+00
0gtdfrlksxdygy3f3me32fj0g4n0xnxa	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-11-06 15:40:10.306599+00
m87tlar4vf1n2a3fl9a3sslx57v8hr6o	ZDk3YjhmZGQwNmYxMzFlNGYyZTc1ODc4MzVmOWZkNWU3OWRjMGI0Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNn0=	2014-11-12 14:26:04.551599+00
oxetfl8iaebxeinvajumbdmpni73jhoy	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-12 18:00:57.434503+00
57uuhcpu5qljcwcllk1j2h4141e8v32n	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-11-13 15:34:52.982193+00
syr4x82orpjlwyozo1oou8jmgwh1y14y	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-11-13 17:40:10.619741+00
qhfgr3imi6e6a2a5lw5ki3vmdkeb4gda	MzhjMzAxZjk5ZTE0NTM2NWZmZGE4YTY0ZWNhN2ZlN2U3ZTJkODdhMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMH0=	2014-11-13 21:53:54.264559+00
dfng63zjc5i33xeblbdv8wpanp8ceumx	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-14 15:06:37.181227+00
f23bhnla4q11vzr293k5gelpokyrjxzo	ZGU1MjE1Y2ExYzYwYzI0YjI0ZGJiNzU5ZjRlZWIyYmUxZWU1ZDg3MTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzN30=	2014-11-14 16:32:36.735392+00
83wj92o934ii25mvomfiwos76v5e4dnv	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-11-15 14:53:05.329076+00
ip9vsjz3ocg7v762gsdbf3sj3zmslvda	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-17 14:48:45.181312+00
jmo7kzy1x10w2pfwvfp3lt7d8lt7czjg	YjYzYzI4YjUyOWU2NzY2NTdhNjdhZTIwYjU1OWUzNGUyYzc2Y2JjZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNn0=	2014-11-17 16:32:24.332572+00
ih9xrnd22yunv848i8796nfbs440cjoa	NjM4NzZjM2E0NmU3N2FmY2E2NzMwOTkwY2I1YmMyZDdkY2VhOWU5ODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwOH0=	2014-11-17 16:45:22.604938+00
nmmic9sme41ctkdcun9w3549jxafbb3d	YWIwYTJiMjcwZmVkMGRlN2ZjMDQ5YmQ0NDUxYWJjN2U5NDM4OGI1OTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjR9	2014-11-06 19:36:39.549095+00
g6758pi23je5z2lwqgogfh7bn41xz68p	MDJhZDk5MGVlZjZiMTNlYzlmNjMxZmY2MGM5MjRmNTY3MzI2YTgwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjcxfQ==	2014-11-12 16:23:39.849984+00
gbezn5hps3vrr4uuxqsmczi6w6h0ceft	MmQ4ZGZmMTE4OWQ1ZmIwMjBiN2MzOGM1NmEzOTZiZGM1MGVlYzIwYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzMH0=	2014-11-06 19:37:47.144039+00
fikbp558raer3yxjj1lnxznlhdutz5pc	NWIyNGFkZTNiYTQ2MGIzYWNmOGM5NzZlYjZjOTliOTQ5NzVhYjAxMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzMn0=	2014-11-06 19:37:52.494797+00
bg8mngnb0byoqzl3wqt2zck90w56ke6f	Y2E0Nzk3ZDk3Zjc1Y2I1MGI0N2RmN2I3YjA3YmVkM2YyYWFmZGEzNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyOX0=	2014-11-06 19:38:04.928848+00
bozkvkleput4gzrigk4trqnkkc4a4kgl	MWU0NWRmMGRhZTU5MWUyMDE4MjM3Nzk0ZjU5Zjk5ZTNiNDM0NDZlZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzMX0=	2014-11-06 19:38:07.089122+00
te1ufwsd2gmp689h3rj9c2nh4752v545	ZGU0ODU0OWNhM2M2MGFlYWRkNDU0MzNhYWQ2OTYxOTc1ZmEzMDI5Yjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzNH0=	2014-11-06 19:45:27.580439+00
n420rdk88qftxu5tt6ye22j94x3t1m5h	YjliZTFiMTUyYTc0NDJmN2Q4NWRlMjBlMjQxZjg2ZDExZTRmOTFkNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzNX0=	2014-11-06 23:46:36.445071+00
r89j7qkdgm4a3zqhx09wgmstty7kgpdi	NjFjY2RmYzA5MzA4ZjUyOTcyNDY1MWFmNjMwNDFiYzljNTI4ODM1Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzNn0=	2014-11-07 12:55:39.89709+00
1h0b6irgptztqdon1rai4rbdnwigsoxq	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-11-07 17:52:15.285917+00
nnm5zl7z6i2re6ni8nt1bj2hbvl4mir5	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-07 18:55:27.853568+00
3j0jyjsvqbmw3s5858p90xolpd5pa17d	ZGU1MjE1Y2ExYzYwYzI0YjI0ZGJiNzU5ZjRlZWIyYmUxZWU1ZDg3MTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzN30=	2014-11-07 19:15:27.564433+00
zydm3ea6c1hqcff0zmujxq18ep5yrjb1	NjUzZGRmMTViNWNkN2Y2ZTU5MjJhM2U5MmQ3NTc1NDhiMzc0NWQwYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkyfQ==	2014-11-07 19:15:59.824607+00
331plf177elk5ype1wit422y6o0xgxq7	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-11-07 23:59:17.828996+00
e9xaqr7t228bop535ywubn6m6287mz3e	YjBjN2NhMDViNDg1YTdkMTk4ODUyYmQyY2IwZWI1OWJkZjkxN2E0Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwM30=	2014-11-09 18:31:04.611229+00
e7bddswsuo8bcby9crzj6ss71sik93ld	OWRiY2FlN2JlNzJiMGVhZjQ5MGQ3Yjg3NGJiM2JkODNmNDkyNzM2YTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyM30=	2014-11-09 19:39:02.459621+00
rbywtjyj30l2g3atl8fo6q0xmntudsd4	NGZiNzM0Y2FiOGEzZDA3NTRmODI5YTA3ZDRlYzM1NmE3MjdlNjkzZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzOH0=	2014-11-10 12:28:31.817023+00
umq5mdzitpjwss1aj4usla1teiborg2u	YjY5NTQ1MWE0YzFjM2VmNTlhNWJhNWMwMDRkNDVlZTE2YTM2MzJiMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzOX0=	2014-11-10 12:40:01.560327+00
9uet01ljjjaj2676csp27qy4fkrcg4wc	NjA2Nzc2Y2FmZTNhODZlZmYzODg4MDFhZmNmNTgzNWI5YzAyMWE4NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0MH0=	2014-11-10 12:47:12.757225+00
hq95dy3bfrnf06y0x94v0rm6fx3fjaxf	ZTdjZjUyNjk0Yjk2ZmZhOGRiZDZlZGJhNjJlOGVkNzQwMjFhZDJiNDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0MX0=	2014-11-10 13:13:05.821611+00
q75unf8e7w117112sgpwfs6jkfovwsyf	NzBhODIxNjVmYjI1Mjk5ZGRhOWVkNzUxYTc4YzQ3ZWY0ZTQ5OGMyOTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0Mn0=	2014-11-10 13:15:31.610884+00
wxcey2j0m4lh15gjbcgby9pp2iuvcnh4	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-11-10 14:40:43.879008+00
gefro1rz25xjx7kfetbsgw52p1kox1wt	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-11-10 14:40:45.569782+00
rztcvxdrwu2bgbke73ecqp2h8z84h5sa	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-10 14:53:41.861061+00
aftjiobbf6frw0feb0dcrg16sbzgilqz	NWYxOTQ2MDg2Y2Q1ZDRkOWYwZGEzZjAwNzI2OWNiNjVlMjM5ODY4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNH0=	2014-11-10 15:53:34.884082+00
47qca1edd4pvvujtpeqsftwkvjjrhydm	Y2M3YzdhYWQ5ZGFjMTNkNDYxNDk5NWQzMTI5ZTkxNTNmOGU2ZjQyYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwOX0=	2014-11-10 21:04:53.552268+00
7ohubwfvkyr2bj1qtcluwz1p6jakyblm	YjYzYzI4YjUyOWU2NzY2NTdhNjdhZTIwYjU1OWUzNGUyYzc2Y2JjZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNn0=	2014-11-11 00:49:12.765812+00
ttwhty9armowynw20cs6s4q3qzvaigsu	Y2EzOTNiMjAxNWUwZmVkZGM1ZWFlMjRkYTAwZTA1NDlkODUxZDE4Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNX0=	2014-11-11 13:24:27.678969+00
4gdhimj4rdirzb55w6y6jtb86ye99uw4	ZGU1MjE1Y2ExYzYwYzI0YjI0ZGJiNzU5ZjRlZWIyYmUxZWU1ZDg3MTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEzN30=	2014-11-11 13:41:22.490527+00
2l8fajeo0b83v62v8autyjvo3xfco8nt	Y2EzOTNiMjAxNWUwZmVkZGM1ZWFlMjRkYTAwZTA1NDlkODUxZDE4Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNX0=	2014-11-11 15:16:25.152804+00
bgrvmc84phum3d2040gygsj7vpacdpvl	Y2MwOGY5NmYxYzRlNjYxNjRmMTkxYmVmMWM3ODk4MDJlMDA4Y2VlODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjF9	2014-11-11 15:20:03.671677+00
x17fl6ic1ncw9p1djlq6congv8afkwy9	ODQxNWJlYjUxN2UyZjI2YzBmYjhhMThmOTE2NGZkY2M3ZmYzMDg2MDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExM30=	2014-11-11 15:28:09.400793+00
j2j66e7uj5vzhzfp5pj2dodpumg53jtw	NDI4YWQ2MGMzMDRmMjk4OGFlOGViYWFkYjdmOWJiYzY0NDE5YjVkMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMn0=	2014-11-11 16:27:36.241856+00
a423f7bsf02wz8tosov2ub8dtj97ml2x	NWYxOTQ2MDg2Y2Q1ZDRkOWYwZGEzZjAwNzI2OWNiNjVlMjM5ODY4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNH0=	2014-11-11 17:41:56.720504+00
adscaowyi3d0dimvj7qjcvil0vad1w1v	NjEzY2Q5YjE2YzUyY2RiOWRiM2RkZmJhM2Y1NjMwYzFiNDIwOTA0MTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0NX0=	2014-11-12 18:19:28.614155+00
lhoeuo8ejslymkraczjszb6iisnc1af9	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-11 17:59:57.266695+00
r156m238fnbxl8nsdib8sw8c77c6i1eh	NWYxOTQ2MDg2Y2Q1ZDRkOWYwZGEzZjAwNzI2OWNiNjVlMjM5ODY4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNH0=	2014-11-13 15:55:33.752915+00
qm0p3o4ab23b3269pvpo4snrezqs0e7y	NjEzY2Q5YjE2YzUyY2RiOWRiM2RkZmJhM2Y1NjMwYzFiNDIwOTA0MTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0NX0=	2014-11-11 18:02:31.760021+00
abmhsaay66exznucom1osflnykowoimj	YzY5YWM2MmNjZmZiMWM2OWFhNmIyZWI3ZTIyMjJkMjE1ZTc5Y2M3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyMX0=	2014-11-13 18:31:25.35116+00
rj1pzx28fwgp3tnpoyv5df495wzuaxsc	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-11 18:21:20.43915+00
wv1pmw7kgszanasyqeighgfut8kx0pby	MDJhZDk5MGVlZjZiMTNlYzlmNjMxZmY2MGM5MjRmNTY3MzI2YTgwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjcxfQ==	2014-11-11 18:30:28.208884+00
ps7pf5wwkfselwty8ww0uisvwxgjtkd9	ZWUxNmM4ZDI3MDliZDU2YWMwY2U2OWQxZjNlYmE3MTUyOTgyMzUzMjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0Nn0=	2014-11-13 19:51:11.294497+00
m2ipnn1864kjjo78vuw8fsfm76qhd6gy	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-11-14 15:08:45.635147+00
1i3m4l4b8beuz8zf3e7526ob99cd80nf	YjJjZGM2MjU2ZTZmODQ4NzkwZGQzMTE0NTkyMjU2NTUzZTg3MzlmYzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE0fQ==	2014-11-11 20:01:59.412276+00
bd2hlf2gwh8npwao6onydi580cbgjf5i	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-14 19:13:45.255333+00
axkzj3pqby0opj29tq3mjkarcystg08n	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-11-17 00:37:20.396423+00
ldqkarkmw5oglk5io2qbyd7wndfvy5wf	NDI4YWQ2MGMzMDRmMjk4OGFlOGViYWFkYjdmOWJiYzY0NDE5YjVkMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMn0=	2014-11-17 15:33:23.376434+00
e4lhejr0lzkjgj577d321ul3kegzle9m	YzY5YWM2MmNjZmZiMWM2OWFhNmIyZWI3ZTIyMjJkMjE1ZTc5Y2M3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyMX0=	2014-11-17 16:39:39.069172+00
l2v0g0s5zudi5z70zmu30s98vfrf6871	Y2MwOGY5NmYxYzRlNjYxNjRmMTkxYmVmMWM3ODk4MDJlMDA4Y2VlODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjF9	2014-11-17 21:32:26.398479+00
t6ih01xg4wulbhl8g7bxxcb76z6o04ui	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-11 20:46:21.866983+00
wdgmouix81uuh1q222gkp2r3m0vfjyfk	NTg3MWQ5OGIwMjdlNDE2ZjliNmUyZWI1YWQxMmRjNjA4NDZkODcwNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwfQ==	2014-11-11 21:19:48.602366+00
iyukbkdsuqyju25prszo5m5uidmfy9tw	NTgyODA5YjVmYTgyZGE1Mjg1MjkyZWZiZTUxNTE4NjI0OWRlNmRlNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyMH0=	2014-11-11 21:25:34.335819+00
9h9g1widch8lmwgwznexbu9cdjadc7a0	YjcxMzQ4ZWJkYjdjNWYwOTQ3ZWFlY2QxMDdkOTRlM2IwNmE5ZGZlNDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNX0=	2014-11-11 21:25:50.648859+00
w0kdejizw5by5eblitevtut2x51f45j1	MzhjMzAxZjk5ZTE0NTM2NWZmZGE4YTY0ZWNhN2ZlN2U3ZTJkODdhMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMH0=	2014-11-11 23:05:13.51333+00
nrkrzxmdzzkzj37kc27cyvnijxpyvpqz	ZDU0YTc1M2Y4MzgzZTlkNmNmNTE3YjZkMzRhOGYzZDQ0ODQ3YWRmYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwN30=	2014-11-12 00:11:09.802573+00
w9tbue4mgsfxz30j4pmvn60hvsjaexqg	OGUwMDA0MjUyMDZmNDUwZWU4NzBmMjk5ZDBhYmQ2OTJjYzU5ZjQxMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExN30=	2014-11-12 00:28:17.913432+00
6uybxk99y684j5igapzkf4rfdxvl5etp	NjM4NzZjM2E0NmU3N2FmY2E2NzMwOTkwY2I1YmMyZDdkY2VhOWU5ODp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwOH0=	2014-11-12 01:47:17.608356+00
vlxx5rf26f1ha5t4hnvdfind7aak7md3	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-12 01:56:50.362307+00
n3t8w9qflmaxgusgml32vb0bteg7bu0b	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-11-12 02:46:04.592796+00
51tn0o78xdg85q68u8u1ymaij3x4ez75	NTgyODA5YjVmYTgyZGE1Mjg1MjkyZWZiZTUxNTE4NjI0OWRlNmRlNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyMH0=	2014-11-12 04:11:42.930321+00
g8mzfc4xujoh0cb04jejvd76juf9wqvj	YjlkYmNiZDdhMTUzMTE2N2U5NWZhNmM2YTIyYjUzNzM2OTU3MTgxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMX0=	2014-11-12 04:16:49.248357+00
671vvsnq2hg23a7pb5cuz97cpqnwaaow	YmYzNWQ1MjQwYzhkMmJlMGU1YWM0YTI3YWJiNjcyZGYxNjRmMjRiZjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkzfQ==	2014-11-18 23:22:09.370542+00
3ztviz9hm64ewh7bu80wx4wev2tb2zng	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-11-19 05:40:31.860961+00
xo58rmsj4d1suecknfx7h3ivb6zh5271	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-11-19 13:49:37.575523+00
rg0pjy8jfgi9tbxr84ozpqgd1ekrylo6	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-19 14:25:15.608953+00
ftdflwmxbuj7x35rh7tnnr9bm2rdr96o	ZDBmOGIxZTIwZWM1YjA0N2VhMjE2Y2MzNDlmOTkzZmE2YzdkY2JjMDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExNH0=	2014-11-19 14:57:01.000457+00
0lixjyou1pdlagydsiptm9mfw498jbjx	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-19 16:23:29.697127+00
k5qzufs3s2pe52tprsjsqk93ageutjqm	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-19 16:28:16.214582+00
9992u5r15vda88g5ihytz1h3fz7b8uik	OGUwMDA0MjUyMDZmNDUwZWU4NzBmMjk5ZDBhYmQ2OTJjYzU5ZjQxMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExN30=	2014-11-19 18:24:25.577607+00
ezzukf5h31iw87zdfiusyq8vfeh1nfq5	NDI4YWQ2MGMzMDRmMjk4OGFlOGViYWFkYjdmOWJiYzY0NDE5YjVkMzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMn0=	2014-11-19 18:44:33.69978+00
va6ed6skvigmkf3zb5ud79nb0g3jdvv4	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-19 19:18:57.02158+00
e28gqvam246hsfh538na5cmlbxybi8tr	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-19 19:34:06.320846+00
4c5o8u4zsr749gytl4jd1ccmoi3hxxe6	M2E3YjdjNmY3Nzg3N2Q5NWZiMzlmMWNhODU1NTUzNGQxZmJhMDg5NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1MH0=	2014-11-19 20:29:47.622535+00
v8fdpfasd1d0cltarept9p4tdu70dlpi	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-19 20:52:00.315173+00
mi9mqc7rxfm1qpo61rfwe1tadbhrtte0	Y2EzOTNiMjAxNWUwZmVkZGM1ZWFlMjRkYTAwZTA1NDlkODUxZDE4Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNX0=	2014-11-20 01:30:45.034677+00
whmk3m2sj5jsqb34pw7h5sq0sa4ep8hr	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-20 02:40:32.850868+00
h6e9he34rso7lggcjtngvsbz8w7f1cl8	ZDU0YTc1M2Y4MzgzZTlkNmNmNTE3YjZkMzRhOGYzZDQ0ODQ3YWRmYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwN30=	2014-11-20 17:37:46.241348+00
iylibhwc3k3b5lz5je3lcnu0lqqb8bix	NWYxOTQ2MDg2Y2Q1ZDRkOWYwZGEzZjAwNzI2OWNiNjVlMjM5ODY4Yzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEwNH0=	2014-11-20 19:17:11.339776+00
23a2dz3jtvwd2lkifau0qyupq4oe3tal	YjlkYmNiZDdhMTUzMTE2N2U5NWZhNmM2YTIyYjUzNzM2OTU3MTgxZDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjExMX0=	2014-11-21 01:43:11.681851+00
1rspvd1n7snmo7kehtt19kedn541ged3	MjhlZjBlNzFmNGQ1MGEyODk3ZGVhMDcyOTFhNTRmYjQwMzFkNjdiNjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjV9	2014-11-21 16:24:50.196864+00
ikmcnsonhsndskzh71j5h1a0tceouola	YTAxMzIyMzM3ZjllNDZjMzgwOTFlNGIwZDZiYjUwN2ZmYTk3NzY3Mzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjk2fQ==	2014-11-21 19:46:17.056732+00
jgge199oz3g8jf7ubd29zciw40z74drg	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-21 21:27:49.07217+00
qmb17y9sb1y3r7cyvs2k5iyr8a4u4xww	NzlkNWE2MDY0YWFmOTE5OGI1NzU3YzQ2ODkzNGM5Mzg5NzQ5ZDEwMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1MX0=	2014-11-21 23:40:37.972217+00
tqovvqvfim9jtzs4uujx54su2ag223l4	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-24 12:25:17.84863+00
edxfu80436rxtnekgaurrfp0huzk96c7	NjUzZGRmMTViNWNkN2Y2ZTU5MjJhM2U5MmQ3NTc1NDhiMzc0NWQwYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkyfQ==	2014-11-24 14:19:58.543375+00
8fcowmml8c7u6upz5slbtnyza2ggz7u3	YjYyNWU0YzNmOWU0ODUxZmU5ODU1OWEyZDkwZDk1NGQwOGQ1ZjA1Zjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjQ2fQ==	2014-11-24 15:05:24.265437+00
54njxhz4nhcyup5l3cdi7wqcb7f8ulhx	OWY1ZGJiMmRjMzk2NmVmNWY1MWE4ZGE1ZTFkNDNkYzg3ZmE1MmQ0ZTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjd9	2014-11-24 15:44:40.931299+00
1f054iasilrs5a94xi88btti6q82cf51	ZGI2NDAwMmU5MDFhOTY2YzM0ODhmMzU1OTc2MGVjNzUxOTExNGU3NDp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjEyfQ==	2014-11-25 00:36:02.288706+00
u0y9w4hkymupwyi13qvtnvq6uds4gnma	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-26 14:06:46.270817+00
vxta1i518a2ty74yiurzyupsbndw94k5	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-26 15:19:43.171415+00
hk9t9dw1pvmoqvkxlehmvydt8qk1bn6c	NjUzZGRmMTViNWNkN2Y2ZTU5MjJhM2U5MmQ3NTc1NDhiMzc0NWQwYjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjkyfQ==	2014-11-26 17:43:07.802273+00
1c6nt29o89u6qt5v5ozbe7ugjc05lomn	MzBiNDg4NmRhNzM2ZTExYjdmYWIyNzgyOGM1NjMzZjgxMzc3MzRiNzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1Mn0=	2014-11-26 19:46:47.768575+00
viobox8j5m8mna3j274fhu54kfb8gs3x	OTFmM2VlN2FlZDdjMDhlYjE0ODQ0YzYzYzcyMGVlMTY4ZWM4NGVmMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1M30=	2014-11-27 17:03:23.688762+00
lbaloyogh242562tw26fiqboj3ol439w	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-11-27 22:44:44.08042+00
p987vbjgmzzsctaufrpi95xr3amwavzh	N2RiMzRiMzg3MzNlOGYwOTdiZmNhODliZmZhOTYxMTEzNTZmMmQ4Nzp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1NX0=	2014-11-28 17:08:13.861554+00
9xo048t38rga74f33bntpyz0wviw5u57	MTAzMDg1YWVmZDQwMzVjYmRiYzA3ZjRmNzU2MDk3Nzc2MGRlNGQwMjp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1Nn0=	2014-12-01 06:21:44.824553+00
6cbmo1md0czw67lhlpnphz03xo3095h2	NTdmZDBlYmZjZGI4ZTdiZWMwODU0ZThlODE5YmYxNjIwYTM2MjNhMTp7Il9hdXRoX3VzZXJfYmFja2VuZCI6Im1lenphbmluZS5jb3JlLmF1dGhfYmFja2VuZHMuTWV6emFuaW5lQmFja2VuZCIsIl9hdXRoX3VzZXJfaWQiOjE1N30=	2014-12-02 12:43:09.443406+00
y9hnmida0rpefpzzjnkogyloq6wn2jak	NmM0MTZkOGYzNTBkNDEwMTBiZTc3NTFmODg5ZDU4N2VkNmVkZDJlZTp7fQ==	2014-12-04 15:50:48.766134+00
\.


--
-- Data for Name: django_site; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_site (id, domain, name) FROM stdin;
1	localhost:8000	Default
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
4	9	32	AB		This is a simple generic resource that is not entirely public.  DaveT, JeffH, and Jefferson should be able to view it.	2014-03-12 14:16:21.953376+00	2014-03-12 14:16:21.953398+00
\.


--
-- Name: dublincore_qualifieddublincoreelement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('dublincore_qualifieddublincoreelement_id_seq', 1374, true);


--
-- Data for Name: dublincore_qualifieddublincoreelementhistory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY dublincore_qualifieddublincoreelementhistory (id, object_id, content_type_id, term, qualifier, content, updated_at, created_at, qdce_id, qdce_id_stored) FROM stdin;
4	103	32	REF	\N	Tarboton, D. G., R. Idaszak, J. S. Horsburgh, J. Heard, D. Ames, J. L. Goodall, L. Band, V. Merwade, A. Couch, J. Arrigo, R. Hooper, D. Valentine and D. Maidment, (2014), "HydroShare: Advancing Collaboration through Hydrologic Data and Model Sharing," in D. P. Ames, N. W. T. Quinn and A. E. Rizzoli (eds), Proceedings of the 7th International Congress on Environmental Modelling and Software, San Diego, California, USA, International Environmental Modelling and Software Society (iEMSs), ISBN: 978-88-9035-744-2, http://www.iemss.org/sites/iemss2014/papers/iemss2014_submission_243.pdf	2014-07-22 18:50:27.634123+00	2014-07-22 18:50:27.634146+00	\N	612
2	78	32	FMT	\N	txt	2014-07-14 16:21:41.56091+00	2014-07-14 16:21:41.560931+00	\N	402
\.


--
-- Name: dublincore_qualifieddublincoreelementhistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('dublincore_qualifieddublincoreelementhistory_id_seq', 4, true);


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
-- Data for Name: ga_ows_ogrdataset; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_ows_ogrdataset (id, collection_id, location, checksum, name, human_name, extent) FROM stdin;
\.


--
-- Name: ga_ows_ogrdataset_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ga_ows_ogrdataset_id_seq', 1, false);


--
-- Data for Name: ga_ows_ogrdatasetcollection; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_ows_ogrdatasetcollection (id, name) FROM stdin;
\.


--
-- Name: ga_ows_ogrdatasetcollection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ga_ows_ogrdatasetcollection_id_seq', 1, false);


--
-- Data for Name: ga_ows_ogrlayer; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_ows_ogrlayer (id, dataset_id, name, human_name, extent) FROM stdin;
\.


--
-- Name: ga_ows_ogrlayer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('ga_ows_ogrlayer_id_seq', 1, false);


--
-- Data for Name: ga_resources_catalogpage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY ga_resources_catalogpage (page_ptr_id, public, owner_id) FROM stdin;
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
\.


--
-- Name: generic_assignedkeyword_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('generic_assignedkeyword_id_seq', 171, true);


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
water-usage	17	water usage	1
time-series	18	time series	1
lake-level	19	Lake Level	1
openstreetmap	20	openstreetmap	1
pbf	21	pbf	1
basemaps	22	basemaps	1
hydroshare	23	hydroshare	1
ppt	24	ppt	1
talks	25	talks	1
data-sharing	26	Data Sharing	1
model-sharing	27	Model Sharing	1
information-model	28	Information Model	1
web-services	29	Web Services	1
hjkl	30	hjkl	1
utah-energy-balance-model	31	Utah Energy Balance Model	1
snow-water-equivalent	32	snow water equivalent	1
hec-ras	33	HEC-RAS	1
east-fork-white-river	34	East Fork white River	1
hydraulic-modeling	35	Hydraulic Modeling	1
temperature	36	Temperature	1
water	37	Water	1
little-bear-river	38	Little Bear River	1
utah	39	Utah	1
water-quality	40	Water Quality	1
temperature-humidity	41	Temperature; Humidity	1
nothing	42	Nothing	1
test	43	Test	1
blah	44	blah	1
stuff	45	stuff	1
hydroshare-design	46	HydroShare Design	1
resource-data-model	47	Resource Data Model	1
hydroshare-presentation	48	HydroShare Presentation	1
hydroshare-paper	49	HydroShare Paper	1
hydroshare-annual-report	50	HydroShare Annual Report	1
arcgis	51	ArcGIS	1
geoprocessing	52	geoprocessing	1
hexagon	53	hexagon	1
sampling	54	sampling	1
dissolved-oxygen	55	Dissolved Oxygen	1
ph	56	pH	1
turbidity	57	Turbidity	1
specific-conductance	58	Specific Conductance	1
stage	59	Stage	1
development-presentation	60	Development; Presentation	1
arduino	61	Arduino	1
low-cost-sensors	62	Low-Cost Sensors	1
dem	63	DEM	1
ascii	64	ASCII	1
terrain	65	Terrain	1
python	66	python	1
shapefile	67	shapefile	1
conversion	68	conversion	1
file-format	69	file format	1
lakes	70	lakes	1
test-1	71	test	1
volume	72	Volume	1
riverml	73	RiverML	1
url-website-link	74	URL website link	1
vulnerability	75	vulnerability	1
giswr2014	76	GISWR2014	1
cross-section-cutlines	77	cross-section cutlines	1
flood-hazard-lines	78	flood hazard lines	1
river-centerline	79	river centerline	1
swat	80	swat	1
test-trial-first	81	test; trial; first	1
swatshare	82	swatshare	1
rhessys	83	RHESSys	1
testing	84	testing	1
fungi	85	fungi	1
toxic	86	toxic	1
soil	87	soil	1
image-test	88	image test	1
lake-volume	89	Lake Volume	1
discharge	90	Discharge	1
floods	91	Floods	1
nfie	92	NFIE	1
\.


--
-- Name: generic_keyword_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('generic_keyword_id_seq', 92, true);


--
-- Data for Name: generic_rating; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY generic_rating (content_type_id, id, value, object_pk, rating_date, user_id) FROM stdin;
\.


--
-- Name: generic_rating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('generic_rating_id_seq', 27, true);


--
-- Data for Name: generic_threadedcomment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY generic_threadedcomment (by_author, comment_ptr_id, replied_to_id, rating_count, rating_average, rating_sum) FROM stdin;
\.


--
-- Data for Name: hs_core_bags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_bags (id, object_id, content_type_id, "timestamp", bag) FROM stdin;
\.


--
-- Name: hs_core_bags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_bags_id_seq', 331, true);


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
2
3
4
5
6
7
\.


--
-- Name: hs_core_coremetadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_coremetadata_id_seq', 7, true);


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
1	1	93	\N	David G Tarboton	\N	david.tarboton@gmail.com	\N	\N	\N	\N	\N	1
2	2	93	\N	David G Tarboton	\N	david.tarboton@gmail.com	\N	\N	\N	\N	\N	1
3	5	93	\N	David Tarboton	\N	dtarb@usu.edu	\N	\N	\N	\N	\N	1
4	6	93	\N	Hong Yi	\N	hongyi@renci.org	\N	\N	\N	\N	\N	1
5	7	93	\N	David G Tarboton	\N	david.tarboton@gmail.com	\N	\N	\N	\N	\N	1
\.


--
-- Name: hs_core_creator_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_creator_id_seq', 5, true);


--
-- Data for Name: hs_core_date; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_date (id, object_id, content_type_id, type, start_date, end_date) FROM stdin;
1	1	93	created	2014-11-05 05:28:41.837234+00	\N
2	1	93	modified	2014-11-05 05:28:41.845165+00	\N
3	2	93	created	2014-11-05 05:41:29.806858+00	\N
4	2	93	modified	2014-11-05 05:41:29.813682+00	\N
5	5	93	created	2014-11-05 05:56:50.210171+00	\N
6	5	93	modified	2014-11-05 05:56:50.218001+00	\N
7	6	93	created	2014-11-07 19:59:07.163698+00	\N
8	6	93	modified	2014-11-07 19:59:07.172154+00	\N
9	7	93	created	2014-11-10 12:28:35.107128+00	\N
10	7	93	modified	2014-11-10 12:28:35.114559+00	\N
\.


--
-- Name: hs_core_date_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_date_id_seq', 10, true);


--
-- Data for Name: hs_core_description; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_description (id, object_id, content_type_id, abstract) FROM stdin;
1	1	93	These comma separated variable files give the level and volume of the Great Salt Lake from the start of the record in 1847 to 2014-05-03.  Level in feet is as recorded by the USGS.  Level in m was converted from ft and volume and area were computed from the bathymetry\r\n
2	2	93	A sample RAPID run to use in evaluating data sharing as part of the National Flood Interoperability Experiment.\r\n\r\nThe files are as follows\r\nNHDFlowline_NHDPlus_WGRFC_Subset_Shapefile.zip  Shapefile of the domain\r\nresult_2014100520141101.nc  NetCDF file with results\r\nPlotNCinR.R   R Script to plot the time series for an arbitrary COMID\r\nAnalysis.pptx  Powerpoint file illustrating the time series for a selected stream reach.
3	5	93	HydroShare is an online, collaborative system being developed for open sharing of hydrologic data and models.  This presentation will introduce the HydroShare functionality developed to date and describe ongoing development of functionality to support collaboration and integration of data and models.  
4	6	93	12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n12345678901234567890\r\n
5	7	93	 HydroShare is an online, collaborative system being developed for open sharing of hydrologic data and models.  The goal of HydroShare is to enable scientists to easily discover and access hydrologic data and models, retrieve them to their desktop or perform analyses in a distributed computing environment that may include grid, cloud or high performance computing model instances as necessary.  Scientists may also publish outcomes (data, results or models) into HydroShare, using the system as a collaboration platform for sharing data, models and analyses.  HydroShare is expanding the data sharing capability of the CUAHSI Hydrologic Information System by broadening the classes of data accommodated to include geospatial data used in hydrology.  HydroShare will also include new capability to share models and model components, and will take advantage of emerging social media functionality to enhance information about and collaboration around hydrologic data and models.  \r\n\r\nThis presentation will introduce the HydroShare functionality developed to date and describe ongoing development of functionality to support collaboration and integration of data and models.  
\.


--
-- Name: hs_core_description_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_description_id_seq', 5, true);


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
\.


--
-- Data for Name: hs_core_genericresource_edit_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_edit_groups (id, genericresource_id, group_id) FROM stdin;
\.


--
-- Name: hs_core_genericresource_edit_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_edit_groups_id_seq', 5, true);


--
-- Data for Name: hs_core_genericresource_edit_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_edit_users (id, genericresource_id, user_id) FROM stdin;
\.


--
-- Name: hs_core_genericresource_edit_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_edit_users_id_seq', 181, true);


--
-- Data for Name: hs_core_genericresource_owners; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_owners (id, genericresource_id, user_id) FROM stdin;
\.


--
-- Name: hs_core_genericresource_owners_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_owners_id_seq', 201, true);


--
-- Data for Name: hs_core_genericresource_view_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_view_groups (id, genericresource_id, group_id) FROM stdin;
\.


--
-- Name: hs_core_genericresource_view_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_view_groups_id_seq', 6, true);


--
-- Data for Name: hs_core_genericresource_view_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_genericresource_view_users (id, genericresource_id, user_id) FROM stdin;
\.


--
-- Name: hs_core_genericresource_view_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_genericresource_view_users_id_seq', 158, true);


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
1	1	93	hydroShareIdentifier	http://hydroshare.org/resource/1a6586ac7cfa4e7bab019dd9fa1155c0
2	2	93	hydroShareIdentifier	http://hydroshare.org/resource/7997c5c14204404186ec30634f58e01c
3	5	93	hydroShareIdentifier	http://hydroshare.org/resource/ce9c114a36f541c88aecd9c6ff0a06a4
4	6	93	hydroShareIdentifier	http://hydroshare.org/resource/3a48ef2f22574f209ff9767ae50947f8
5	7	93	hydroShareIdentifier	http://hydroshare.org/resource/6cc40e13b92843f9b8e963337b43758e
\.


--
-- Name: hs_core_identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_identifier_id_seq', 5, true);


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
\.


--
-- Name: hs_core_resourcefile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_resourcefile_id_seq', 229, true);


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
1	1	93	Lake Level
2	1	93	Lake Volume
3	2	93	Discharge
4	2	93	Floods
5	2	93	NFIE
6	6	93	test
\.


--
-- Name: hs_core_subject_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_subject_id_seq', 6, true);


--
-- Data for Name: hs_core_title; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_core_title (id, object_id, content_type_id, value) FROM stdin;
1	1	93	 Great Salt Lake Level and Volume
2	2	93	Sample RAPID Run for Water Resources Region 12 in Texas
3	3	93	AWRA conference presentations "HydroShare: Advancing Collaboration through Hydrologic Data and Model Sharing"
4	4	93	AWRA conference presentations "HydroShare: Advancing Collaboration through Hydrologic Data and Model Sharing"
5	5	93	AWRA conference presentations "HydroShare: Advancing Collaboration through Hydrologic Data and Model Sharing"
6	6	93	test abstract length
7	7	93	AWRA Presentation: "HydroShare: Advancing Collaboration through Hydrologic Data and Model Sharing"
\.


--
-- Name: hs_core_title_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_core_title_id_seq', 7, true);


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
-- Data for Name: hs_rhessys_inst_resource_instresource; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_rhessys_inst_resource_instresource (page_ptr_id, comments_count, content, user_id, creator_id, public, frozen, do_not_distribute, discoverable, published_and_frozen, last_changed_by_id, short_id, doi, name, git_repo, git_username, git_password, commit_id, model_desc, git_branch, study_area_bbox, model_command_line_parameters, project_name, object_id, content_type_id) FROM stdin;
\.


--
-- Data for Name: hs_rhessys_inst_resource_instresource_edit_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_rhessys_inst_resource_instresource_edit_groups (id, instresource_id, group_id) FROM stdin;
\.


--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_rhessys_inst_resource_instresource_edit_groups_id_seq', 1, false);


--
-- Data for Name: hs_rhessys_inst_resource_instresource_edit_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_rhessys_inst_resource_instresource_edit_users (id, instresource_id, user_id) FROM stdin;
\.


--
-- Name: hs_rhessys_inst_resource_instresource_edit_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_rhessys_inst_resource_instresource_edit_users_id_seq', 1, false);


--
-- Data for Name: hs_rhessys_inst_resource_instresource_owners; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_rhessys_inst_resource_instresource_owners (id, instresource_id, user_id) FROM stdin;
\.


--
-- Name: hs_rhessys_inst_resource_instresource_owners_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_rhessys_inst_resource_instresource_owners_id_seq', 1, false);


--
-- Data for Name: hs_rhessys_inst_resource_instresource_view_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_rhessys_inst_resource_instresource_view_groups (id, instresource_id, group_id) FROM stdin;
\.


--
-- Name: hs_rhessys_inst_resource_instresource_view_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_rhessys_inst_resource_instresource_view_groups_id_seq', 1, false);


--
-- Data for Name: hs_rhessys_inst_resource_instresource_view_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY hs_rhessys_inst_resource_instresource_view_users (id, instresource_id, user_id) FROM stdin;
\.


--
-- Name: hs_rhessys_inst_resource_instresource_view_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('hs_rhessys_inst_resource_instresource_view_users_id_seq', 1, false);


--
-- Data for Name: pages_link; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY pages_link (page_ptr_id) FROM stdin;
\.


--
-- Data for Name: pages_page; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY pages_page (status, _order, parent_id, description, title, short_url, login_required, id, expiry_date, publish_date, titles, content_model, slug, keywords_string, site_id, gen_description, in_menus, _meta_title, in_sitemap, created, updated) FROM stdin;
2	10	\N	HydroShare Statement of Privacy \nLast modified July 7, 2013	Statement of Privacy	\N	f	27	\N	2014-05-07 17:28:04+00	Statement of Privacy	richtextpage	privacy		1	t			t	2014-05-07 17:28:04.061384+00	2014-06-09 19:16:27.220663+00
2	9	\N	HydroShare Terms of Use\nLast modified July 7, 2013	Terms of Use	\N	f	26	\N	2014-05-07 17:27:32+00	Terms of Use	richtextpage	terms-of-use		1	t			t	2014-05-07 17:27:32.928522+00	2014-06-09 19:16:48.480425+00
2	7	\N	Please give us your email address and we will resend the confirmation	Resend Verification Email	\N	f	24	\N	2014-05-05 19:51:29.969921+00	Resend Verification Email	form	resend-verification-email		1	t			t	2014-05-05 19:51:29.971722+00	2014-05-05 19:51:29.971722+00
2	12	\N	share resource	Share resource	\N	f	29	\N	2014-06-02 18:08:59.906453+00	Share resource	richtextpage	share-resource		1	t			t	2014-06-02 18:08:59.931029+00	2014-06-02 18:08:59.931029+00
2	11	\N	hjkl	Resource landing	\N	f	28	\N	2014-06-02 18:07:38+00	Resource landing	richtextpage	resourcelanding		1	t			t	2014-06-02 18:07:38.184936+00	2014-06-02 18:09:05.842892+00
2	3	\N	This page is slated for release 2	Explore	\N	f	20	\N	2014-04-29 19:02:27+00	Explore	richtextpage	explore		1	t			t	2014-04-29 19:02:27.56175+00	2014-06-11 12:34:11.658582+00
2	4	\N	hjkl	Collaborate	\N	f	21	\N	2014-04-29 19:02:40+00	Collaborate	richtextpage	collaborate		1	t			t	2014-04-29 19:02:40.289254+00	2014-06-11 12:34:19.706092+00
2	0	\N	Hydroshare is an online collaboration environment for sharing data, models, and code.  Join the community to start sharing.	Home	\N	f	6	\N	2014-03-05 16:16:07+00	Home	homepage	/		1	t			t	2014-03-05 16:16:07.848+00	2014-08-03 20:16:24.927+00
2	2	\N	hjkl	Resources	\N	f	19	\N	2014-04-29 19:01:32+00	Resources	richtextpage	my-resources		1	t	1,2,3		t	2014-04-29 19:01:32.78+00	2014-07-18 18:04:31.804+00
2	5	\N	This page is under construction	Support	\N	f	22	\N	2014-04-29 19:02:56+00	Support	richtextpage	help		1	t	1,2,3		t	2014-04-29 19:02:56.717+00	2014-06-02 18:03:55.848+00
2	6	\N	Thank you for signing up for HydroShare! We have sent you an email from hydroshare.org to verify your account.  Please click on the link within the email and verify your account with us and you can get started sharing data and models with HydroShare.	Verify account	\N	f	23	\N	2014-05-05 19:40:28+00	Verify account	richtextpage	verify-account		1	t			t	2014-05-05 19:40:28.558+00	2014-05-05 19:47:25.082+00
2	8	\N	jkl;	Create Resource	\N	t	25	\N	2014-05-07 15:16:21.597+00	Create Resource	richtextpage	create-resource		1	t			t	2014-05-07 15:16:21.598+00	2014-05-07 15:16:21.598+00
\.


--
-- Name: pages_page_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('pages_page_id_seq', 195, true);


--
-- Data for Name: pages_richtextpage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY pages_richtextpage (content, page_ptr_id) FROM stdin;
<p>share resource</p>	29
<p>hjkl</p>	28
<h1><b>HydroShare Statement of Privacy </b></h1>\n<p><em>Last modified July 7, 2013</em></p>\n<p>HydroShare is operated by a team of researchers associated with the Consortium of Universities for the Advancement of Hydrologic Science, Inc. and funded by the National Science Foundation.  The services are hosted at participating institutions including the Renaissance Computing Institute at University of North Carolina, Utah State University, Brigham Young University, Tufts, University of Virginia, University of California at San Diego, University of Texas, Purdue and CUAHSI.  In the following these are referred to as participating institutions.</p>\n<p>We respect your privacy. We will only use your personal identification information to support and manage your use of hydroshare.org, including the use of tracking cookies to facilitate hydroshare.org security procedures. The HydroShare participating institutions and the National Science Foundation (which funds hydroshare.org development) regularly request hydroshare.org usages statistics and other information. Usage of hydroshare.org is monitored and usage statistics are collected and reported on a regular basis. Hydroshare.org also reserves the right to contact you to request additional information or to keep you updated on changes to Hydroshare.org. You may opt out of receiving newsletters and other non-essential communications. No information that would identify you personally will be provided to sponsors or third parties without your permission.</p>\n<p>While HydroShare uses policies and procedures to manage the access to content according to the access control settings set by users all information posted or stored on hydroshare.org is potentially available to other users of hydroshare.org and the public. The HydroShare participating institutions and hydroshare.org disclaim any responsibility for the preservation of confidentiality of such information. <i>Do not post or store information on hydroshare.org if you expect to or are obligated to protect the confidentiality of that information.</i></p>	27
<h1>HydroShare Terms of Use</h1>\n<p><em>Last modified July 7, 2013</em></p>\n<p>Thank you for using the HydroShare hydrologic data sharing system hosted at hydroshare.org.  HydroShare services are provided by a team of researchers associated with the Consortium of Universities for the Advancement of Hydrologic Science, Inc. and funded by the National Science Foundation.  The services are hosted at participating institutions including the Renaissance Computing Institute at University of North Carolina, Utah State University, Brigham Young University, Tufts, University of Virginia, University of California at San Diego, University of Texas, Purdue and CUAHSI. Your access to hydroshare.org is subject to your agreement to these Terms of Use. By using our services at hydroshare.org, you are agreeing to these terms.  Please read them carefully.</p>\n<h2><b>Modification of the Agreement</b></h2>\n<p>We maintain the right to modify these Terms of Use and may do so by posting modifications on this page. Any modification is effective immediately upon posting the modification unless otherwise stated. Your continued use of hydroshare.org following the posting of any modification signifies your acceptance of that modification. You should regularly visit this page to review the current Terms of Use.</p>\n<h2><b>Conduct Using our Services</b></h2>\n<p>The hydroshare.org site is intended to support data and model sharing in hydrology.  This is broadly interpreted to include any discipline or endeavor that has something to do with water.  You are responsible at all times for using hydroshare.org in a manner that is legal, ethical, and not to the detriment of others and for purposes related to hydrology. You agree that you will not in your use of hydroshare.org:</p>\n<ul>\n<li>Violate any applicable law, commit a criminal offense or perform actions that might encourage others to commit a criminal offense or give rise to a civil liability;</li>\n<li>Post or transmit any unlawful, threatening, libelous, harassing, defamatory, vulgar, obscene, pornographic, profane, or otherwise objectionable content;</li>\n<li>Use hydroshare.org to impersonate other parties or entities;</li>\n<li>Use hydroshare.org to upload any content that contains a software virus, "Trojan Horse" or any other computer code, files, or programs that may alter, damage, or interrupt the functionality of hydroshare.org or the hardware or software of any other person who accesses hydroshare.org;</li>\n<li>Upload, post, email, or otherwise transmit any materials that you do not have a right to transmit under any law or under a contractual relationship;</li>\n<li>Alter, damage, or delete any content posted on hydroshare.org, except where such alterations or deletions are consistent with the access control settings of that content in hydroshare.org;</li>\n<li>Disrupt the normal flow of communication in any way;</li>\n<li>Claim a relationship with or speak for any business, association, or other organization for which you are not authorized to claim such a relationship;</li>\n<li>Post or transmit any unsolicited advertising, promotional materials, or other forms of solicitation;</li>\n<li>Post any material that infringes or violates the intellectual property rights of another.</li>\n</ul>\n<p>Certain portions of hydroshare.org are limited to registered users and/or allow a user to participate in online services by entering personal information. You agree that any information provided to hydroshare.org in these areas will be complete and accurate, and that you will neither register under the name of nor attempt to enter hydroshare.org under the name of another person or entity.</p>\n<p>You are responsible for maintaining the confidentiality of your user ID and password, if any, and for restricting access to your computer, and you agree to accept responsibility for all activities that occur under your account or password. Hydroshare.org does not authorize use of your User ID by third-parties.</p>\n<p>We may, in our sole discretion, terminate or suspend your access to and use of hydroshare.org without notice and for any reason, including for violation of these Terms of Use or for other conduct that we, in our sole discretion, believe to be unlawful or harmful to others. In the event of termination, you are no longer authorized to access hydroshare.org.</p>\n<h2><b>Disclaimers</b></h2>\n<p>HYDROSHARE AND ANY INFORMATION, PRODUCTS OR SERVICES ON IT ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. Hydroshare.org and its participating institutions do not warrant, and hereby disclaim any warranties, either express or implied, with respect to the accuracy, adequacy or completeness of any good, service, or information obtained from hydroshare.org. Hydroshare.org and its participating institutions do not warrant that Hydroshare.org will operate in an uninterrupted or error-free manner or that hydroshare.org is free of viruses or other harmful components. Use of hydroshare.org is at your own risk.</p>\n<p>You agree that hydroshare.org and its participating institutions shall have no liability for any consequential, indirect, punitive, special or incidental damages, whether foreseeable or unforeseeable (including, but not limited to, claims for defamation, errors, loss of data, or interruption in availability of data), arising out of or relating to your use of water-hub.org or any resource that you access through hydroshare.org.</p>\n<p>The hydroshare.org site hosts content from a number of authors. The statements and views of these authors are theirs alone, and do not reflect the stances or policies of the HydroShare research team or their sponsors, nor does their posting imply the endorsement of HydroShare or their sponsors.</p>\n<h2><b>Choice of Law/Forum Selection/Attorney Fees</b></h2>\n<p>You agree that any dispute arising out of or relating to hydroshare.org, whether based in contract, tort, statutory or other law, will be governed by federal law and by the laws of North Carolina, excluding its conflicts of law provisions. You further consent to the personal jurisdiction of and exclusive venue in the federal and state courts located in and serving the United States of America, North Carolina as the exclusive legal forums for any such dispute.</p>	26
<p>This page is slated for release 2</p>	20
<p>hjkl</p>	21
<p>jkl;</p>	25
<p>hjkl</p>	19
<p>This page is under construction</p>	22
<p>Thank you for signing up for HydroShare! We have sent you an email from hydroshare.org to verify your account.  Please click on the link within the email and verify your account with us and you can get started sharing data and models with HydroShare.</p>\n<p><a href="/hsapi/_internal/resend_verification_email/">Please click here if you do not receive a verification email within 1 hour.</a></p>	23
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
103	hs_core	0011_auto__add_publisher__add_unique_publisher_content_type_object_id__add_	2014-11-04 22:05:46.743499+00
104	hs_core	0012_auto__chg_field_contributor_description__chg_field_contributor_researc	2014-11-04 22:05:47.104002+00
105	hs_party	0001_initial	2014-11-04 22:05:48.528071+00
106	django_docker_processes	0001_initial	2014-11-04 22:05:49.381337+00
107	django_docker_processes	0002_auto__add_field_dockerprocess_finished__add_field_dockerprocess_error_	2014-11-04 22:05:49.57438+00
108	django_docker_processes	0003_auto__add_field_dockerlink_docker_overrides	2014-11-04 22:05:49.600733+00
109	django_docker_processes	0004_auto__add_field_dockerprocess_user	2014-11-04 22:05:49.63892+00
110	hs_rhessys_inst_resource	0001_initial	2014-11-04 22:05:50.469011+00
111	hs_rhessys_inst_resource	0002_auto__add_field_instresource_object_id__add_field_instresource_content	2014-11-04 22:05:50.506624+00
112	hs_rhessys_inst_resource	0003_auto__chg_field_instresource_model_command_line_parameters	2014-11-04 22:05:50.550957+00
\.


--
-- Name: south_migrationhistory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('south_migrationhistory_id_seq', 112, true);


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
\.


--
-- Name: tastypie_apikey_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('tastypie_apikey_id_seq', 113, true);


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
1	1	Contact us	<p><a href="mailto:support@hydroshare.org">Email us at hydroshare.org</a></p>	Follow		Open Source	<p>HydroShare is Open Source. <a target="_blank" href="https://github.com/hydroshare/">Find us on Github</a>.</p>\n<p><a href="https://github.com/hydroshare/hydroshare/issues?state=open">Report a bug here. </a>     This is HydroShare Version 1.2.1</p>	http://twitter.com/cuahsi 	https://www.facebook.com/pages/CUAHSI-Consortium-of-Universities-for-the-Advancement-of-Hydrologic-Science-Inc/179921902590		http://www.youtube.com/user/CUAHSI	http://github.com/hydroshare	https://www.linkedin.com/company/2632114			t	&copy {% now "Y" %} CUAHSI. This material is based upon work supported by the National Science Foundation (NSF) under awards 1148453 and 1148090.  Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.
\.


--
-- Name: theme_siteconfiguration_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('theme_siteconfiguration_id_seq', 1, true);


--
-- Data for Name: theme_userprofile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY theme_userprofile (id, user_id, title, profession, subject_areas, organization, organization_type, phone_1, phone_1_type, phone_2, phone_2_type, public, picture, cv, details) FROM stdin;
117	1	\N	Student	\N	\N	\N	\N	\N	\N	\N	t			\N
\.


--
-- Name: theme_userprofile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('theme_userprofile_id_seq', 147, true);


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
-- Name: django_docker_processes_containeroverrides_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_containeroverrides
    ADD CONSTRAINT django_docker_processes_containeroverrides_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_dockerenvvar_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerenvvar
    ADD CONSTRAINT django_docker_processes_dockerenvvar_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_dockerlink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerlink
    ADD CONSTRAINT django_docker_processes_dockerlink_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_dockerport_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerport
    ADD CONSTRAINT django_docker_processes_dockerport_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_dockerprocess_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerprocess
    ADD CONSTRAINT django_docker_processes_dockerprocess_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_dockerprocess_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerprocess
    ADD CONSTRAINT django_docker_processes_dockerprocess_token_key UNIQUE (token);


--
-- Name: django_docker_processes_dockerprofile_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerprofile
    ADD CONSTRAINT django_docker_processes_dockerprofile_name_key UNIQUE (name);


--
-- Name: django_docker_processes_dockerprofile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockerprofile
    ADD CONSTRAINT django_docker_processes_dockerprofile_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_dockervolume_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_dockervolume
    ADD CONSTRAINT django_docker_processes_dockervolume_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_overrideenvvar_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_overrideenvvar
    ADD CONSTRAINT django_docker_processes_overrideenvvar_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_overridelink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_overridelink
    ADD CONSTRAINT django_docker_processes_overridelink_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_overrideport_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_overrideport
    ADD CONSTRAINT django_docker_processes_overrideport_pkey PRIMARY KEY (id);


--
-- Name: django_docker_processes_overridevolume_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_docker_processes_overridevolume
    ADD CONSTRAINT django_docker_processes_overridevolume_pkey PRIMARY KEY (id);


--
-- Name: django_irods_rodsenvironment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_irods_rodsenvironment
    ADD CONSTRAINT django_irods_rodsenvironment_pkey PRIMARY KEY (id);


--
-- Name: django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


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
-- Name: ga_ows_ogrdataset_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_ows_ogrdataset
    ADD CONSTRAINT ga_ows_ogrdataset_pkey PRIMARY KEY (id);


--
-- Name: ga_ows_ogrdatasetcollection_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_ows_ogrdatasetcollection
    ADD CONSTRAINT ga_ows_ogrdatasetcollection_pkey PRIMARY KEY (id);


--
-- Name: ga_ows_ogrlayer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ga_ows_ogrlayer
    ADD CONSTRAINT ga_ows_ogrlayer_pkey PRIMARY KEY (id);


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
-- Name: hs_rhessys_inst_resource__instresource_id_23958bb64d02c7e0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_owners
    ADD CONSTRAINT hs_rhessys_inst_resource__instresource_id_23958bb64d02c7e0_uniq UNIQUE (instresource_id, user_id);


--
-- Name: hs_rhessys_inst_resource__instresource_id_45fd306dda50ac33_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_groups
    ADD CONSTRAINT hs_rhessys_inst_resource__instresource_id_45fd306dda50ac33_uniq UNIQUE (instresource_id, group_id);


--
-- Name: hs_rhessys_inst_resource__instresource_id_55a671d29d314ba2_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_users
    ADD CONSTRAINT hs_rhessys_inst_resource__instresource_id_55a671d29d314ba2_uniq UNIQUE (instresource_id, user_id);


--
-- Name: hs_rhessys_inst_resource__instresource_id_628be0f6ac14948d_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_users
    ADD CONSTRAINT hs_rhessys_inst_resource__instresource_id_628be0f6ac14948d_uniq UNIQUE (instresource_id, user_id);


--
-- Name: hs_rhessys_inst_resource_i_instresource_id_7a81bdda38a7864_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_groups
    ADD CONSTRAINT hs_rhessys_inst_resource_i_instresource_id_7a81bdda38a7864_uniq UNIQUE (instresource_id, group_id);


--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_groups
    ADD CONSTRAINT hs_rhessys_inst_resource_instresource_edit_groups_pkey PRIMARY KEY (id);


--
-- Name: hs_rhessys_inst_resource_instresource_edit_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_users
    ADD CONSTRAINT hs_rhessys_inst_resource_instresource_edit_users_pkey PRIMARY KEY (id);


--
-- Name: hs_rhessys_inst_resource_instresource_owners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_owners
    ADD CONSTRAINT hs_rhessys_inst_resource_instresource_owners_pkey PRIMARY KEY (id);


--
-- Name: hs_rhessys_inst_resource_instresource_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource
    ADD CONSTRAINT hs_rhessys_inst_resource_instresource_pkey PRIMARY KEY (page_ptr_id);


--
-- Name: hs_rhessys_inst_resource_instresource_view_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_groups
    ADD CONSTRAINT hs_rhessys_inst_resource_instresource_view_groups_pkey PRIMARY KEY (id);


--
-- Name: hs_rhessys_inst_resource_instresource_view_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_users
    ADD CONSTRAINT hs_rhessys_inst_resource_instresource_view_users_pkey PRIMARY KEY (id);


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
-- Name: django_docker_processes_containeroverrides_docker_profile_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_containeroverrides_docker_profile_id ON django_docker_processes_containeroverrides USING btree (docker_profile_id);


--
-- Name: django_docker_processes_dockerenvvar_docker_profile_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerenvvar_docker_profile_id ON django_docker_processes_dockerenvvar USING btree (docker_profile_id);


--
-- Name: django_docker_processes_dockerlink_docker_overrides_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerlink_docker_overrides_id ON django_docker_processes_dockerlink USING btree (docker_overrides_id);


--
-- Name: django_docker_processes_dockerlink_docker_profile_from_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerlink_docker_profile_from_id ON django_docker_processes_dockerlink USING btree (docker_profile_from_id);


--
-- Name: django_docker_processes_dockerlink_docker_profile_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerlink_docker_profile_id ON django_docker_processes_dockerlink USING btree (docker_profile_id);


--
-- Name: django_docker_processes_dockerport_docker_profile_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerport_docker_profile_id ON django_docker_processes_dockerport USING btree (docker_profile_id);


--
-- Name: django_docker_processes_dockerprocess_profile_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerprocess_profile_id ON django_docker_processes_dockerprocess USING btree (profile_id);


--
-- Name: django_docker_processes_dockerprocess_token_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerprocess_token_like ON django_docker_processes_dockerprocess USING btree (token varchar_pattern_ops);


--
-- Name: django_docker_processes_dockerprocess_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerprocess_user_id ON django_docker_processes_dockerprocess USING btree (user_id);


--
-- Name: django_docker_processes_dockerprofile_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockerprofile_name_like ON django_docker_processes_dockerprofile USING btree (name varchar_pattern_ops);


--
-- Name: django_docker_processes_dockervolume_docker_profile_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_dockervolume_docker_profile_id ON django_docker_processes_dockervolume USING btree (docker_profile_id);


--
-- Name: django_docker_processes_overrideenvvar_container_overrides_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_overrideenvvar_container_overrides_id ON django_docker_processes_overrideenvvar USING btree (container_overrides_id);


--
-- Name: django_docker_processes_overridelink_container_overrides_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_overridelink_container_overrides_id ON django_docker_processes_overridelink USING btree (container_overrides_id);


--
-- Name: django_docker_processes_overridelink_docker_profile_from_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_overridelink_docker_profile_from_id ON django_docker_processes_overridelink USING btree (docker_profile_from_id);


--
-- Name: django_docker_processes_overrideport_container_overrides_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_overrideport_container_overrides_id ON django_docker_processes_overrideport USING btree (container_overrides_id);


--
-- Name: django_docker_processes_overridevolume_container_overrides_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_docker_processes_overridevolume_container_overrides_id ON django_docker_processes_overridevolume USING btree (container_overrides_id);


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
-- Name: ga_ows_ogrdataset_collection_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrdataset_collection_id ON ga_ows_ogrdataset USING btree (collection_id);


--
-- Name: ga_ows_ogrdataset_extent_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrdataset_extent_id ON ga_ows_ogrdataset USING gist (extent);


--
-- Name: ga_ows_ogrdataset_human_name; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrdataset_human_name ON ga_ows_ogrdataset USING btree (human_name);


--
-- Name: ga_ows_ogrdataset_human_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrdataset_human_name_like ON ga_ows_ogrdataset USING btree (human_name text_pattern_ops);


--
-- Name: ga_ows_ogrdataset_name; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrdataset_name ON ga_ows_ogrdataset USING btree (name);


--
-- Name: ga_ows_ogrdataset_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrdataset_name_like ON ga_ows_ogrdataset USING btree (name varchar_pattern_ops);


--
-- Name: ga_ows_ogrlayer_dataset_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrlayer_dataset_id ON ga_ows_ogrlayer USING btree (dataset_id);


--
-- Name: ga_ows_ogrlayer_extent_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrlayer_extent_id ON ga_ows_ogrlayer USING gist (extent);


--
-- Name: ga_ows_ogrlayer_human_name; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrlayer_human_name ON ga_ows_ogrlayer USING btree (human_name);


--
-- Name: ga_ows_ogrlayer_human_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrlayer_human_name_like ON ga_ows_ogrlayer USING btree (human_name text_pattern_ops);


--
-- Name: ga_ows_ogrlayer_name; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrlayer_name ON ga_ows_ogrlayer USING btree (name);


--
-- Name: ga_ows_ogrlayer_name_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX ga_ows_ogrlayer_name_like ON ga_ows_ogrlayer USING btree (name varchar_pattern_ops);


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
-- Name: hs_rhessys_inst_resource_instresource_content_type_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_content_type_id ON hs_rhessys_inst_resource_instresource USING btree (content_type_id);


--
-- Name: hs_rhessys_inst_resource_instresource_creator_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_creator_id ON hs_rhessys_inst_resource_instresource USING btree (creator_id);


--
-- Name: hs_rhessys_inst_resource_instresource_doi; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_doi ON hs_rhessys_inst_resource_instresource USING btree (doi);


--
-- Name: hs_rhessys_inst_resource_instresource_doi_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_doi_like ON hs_rhessys_inst_resource_instresource USING btree (doi varchar_pattern_ops);


--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_edit_groups_group_id ON hs_rhessys_inst_resource_instresource_edit_groups USING btree (group_id);


--
-- Name: hs_rhessys_inst_resource_instresource_edit_groups_instresou1d45; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_edit_groups_instresou1d45 ON hs_rhessys_inst_resource_instresource_edit_groups USING btree (instresource_id);


--
-- Name: hs_rhessys_inst_resource_instresource_edit_users_instresour6ff4; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_edit_users_instresour6ff4 ON hs_rhessys_inst_resource_instresource_edit_users USING btree (instresource_id);


--
-- Name: hs_rhessys_inst_resource_instresource_edit_users_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_edit_users_user_id ON hs_rhessys_inst_resource_instresource_edit_users USING btree (user_id);


--
-- Name: hs_rhessys_inst_resource_instresource_last_changed_by_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_last_changed_by_id ON hs_rhessys_inst_resource_instresource USING btree (last_changed_by_id);


--
-- Name: hs_rhessys_inst_resource_instresource_owners_instresource_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_owners_instresource_id ON hs_rhessys_inst_resource_instresource_owners USING btree (instresource_id);


--
-- Name: hs_rhessys_inst_resource_instresource_owners_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_owners_user_id ON hs_rhessys_inst_resource_instresource_owners USING btree (user_id);


--
-- Name: hs_rhessys_inst_resource_instresource_short_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_short_id ON hs_rhessys_inst_resource_instresource USING btree (short_id);


--
-- Name: hs_rhessys_inst_resource_instresource_short_id_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_short_id_like ON hs_rhessys_inst_resource_instresource USING btree (short_id varchar_pattern_ops);


--
-- Name: hs_rhessys_inst_resource_instresource_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_user_id ON hs_rhessys_inst_resource_instresource USING btree (user_id);


--
-- Name: hs_rhessys_inst_resource_instresource_view_groups_group_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_view_groups_group_id ON hs_rhessys_inst_resource_instresource_view_groups USING btree (group_id);


--
-- Name: hs_rhessys_inst_resource_instresource_view_groups_instresou980b; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_view_groups_instresou980b ON hs_rhessys_inst_resource_instresource_view_groups USING btree (instresource_id);


--
-- Name: hs_rhessys_inst_resource_instresource_view_users_instresour6b12; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_view_users_instresour6b12 ON hs_rhessys_inst_resource_instresource_view_users USING btree (instresource_id);


--
-- Name: hs_rhessys_inst_resource_instresource_view_users_user_id; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX hs_rhessys_inst_resource_instresource_view_users_user_id ON hs_rhessys_inst_resource_instresource_view_users USING btree (user_id);


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
-- Name: comment_ptr_id_refs_id_d4c241e5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_threadedcomment
    ADD CONSTRAINT comment_ptr_id_refs_id_d4c241e5 FOREIGN KEY (comment_ptr_id) REFERENCES django_comments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: container_overrides_id_refs_id_510a839c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overrideenvvar
    ADD CONSTRAINT container_overrides_id_refs_id_510a839c FOREIGN KEY (container_overrides_id) REFERENCES django_docker_processes_containeroverrides(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: container_overrides_id_refs_id_78c1f902; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overridevolume
    ADD CONSTRAINT container_overrides_id_refs_id_78c1f902 FOREIGN KEY (container_overrides_id) REFERENCES django_docker_processes_containeroverrides(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: container_overrides_id_refs_id_92d17cd7; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overridelink
    ADD CONSTRAINT container_overrides_id_refs_id_92d17cd7 FOREIGN KEY (container_overrides_id) REFERENCES django_docker_processes_containeroverrides(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: container_overrides_id_refs_id_ef853568; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overrideport
    ADD CONSTRAINT container_overrides_id_refs_id_ef853568 FOREIGN KEY (container_overrides_id) REFERENCES django_docker_processes_containeroverrides(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: content_type_id_refs_id_27cd1620; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource
    ADD CONSTRAINT content_type_id_refs_id_27cd1620 FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: creator_id_refs_id_01f3936e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource
    ADD CONSTRAINT creator_id_refs_id_01f3936e FOREIGN KEY (creator_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: creator_id_refs_id_7e75022f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource
    ADD CONSTRAINT creator_id_refs_id_7e75022f FOREIGN KEY (creator_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: django_admin_log_content_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_fkey FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: django_comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_comments
    ADD CONSTRAINT django_comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_irods_rodsenvironment_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_irods_rodsenvironment
    ADD CONSTRAINT django_irods_rodsenvironment_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_overrides_id_refs_id_f4fdaf84; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerlink
    ADD CONSTRAINT docker_overrides_id_refs_id_f4fdaf84 FOREIGN KEY (docker_overrides_id) REFERENCES django_docker_processes_containeroverrides(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_from_id_refs_id_0a9ee02d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerlink
    ADD CONSTRAINT docker_profile_from_id_refs_id_0a9ee02d FOREIGN KEY (docker_profile_from_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_from_id_refs_id_e64bf6f2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_overridelink
    ADD CONSTRAINT docker_profile_from_id_refs_id_e64bf6f2 FOREIGN KEY (docker_profile_from_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_id_refs_id_0a9ee02d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerlink
    ADD CONSTRAINT docker_profile_id_refs_id_0a9ee02d FOREIGN KEY (docker_profile_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_id_refs_id_7f4076c3; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerport
    ADD CONSTRAINT docker_profile_id_refs_id_7f4076c3 FOREIGN KEY (docker_profile_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_id_refs_id_a60496a5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_containeroverrides
    ADD CONSTRAINT docker_profile_id_refs_id_a60496a5 FOREIGN KEY (docker_profile_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_id_refs_id_bcaa597c; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerenvvar
    ADD CONSTRAINT docker_profile_id_refs_id_bcaa597c FOREIGN KEY (docker_profile_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: docker_profile_id_refs_id_c613f9db; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockervolume
    ADD CONSTRAINT docker_profile_id_refs_id_c613f9db FOREIGN KEY (docker_profile_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: entry_id_refs_id_e329b086; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY forms_fieldentry
    ADD CONSTRAINT entry_id_refs_id_e329b086 FOREIGN KEY (entry_id) REFERENCES forms_formentry(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: ga_ows_ogrdataset_collection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_ows_ogrdataset
    ADD CONSTRAINT ga_ows_ogrdataset_collection_id_fkey FOREIGN KEY (collection_id) REFERENCES ga_ows_ogrdatasetcollection(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ga_ows_ogrlayer_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ga_ows_ogrlayer
    ADD CONSTRAINT ga_ows_ogrlayer_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES ga_ows_ogrdataset(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: group_id_refs_id_c1faeb19; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_groups
    ADD CONSTRAINT group_id_refs_id_c1faeb19 FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: group_id_refs_id_eafd3ff4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_groups
    ADD CONSTRAINT group_id_refs_id_eafd3ff4 FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: group_id_refs_id_f4b32aac; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT group_id_refs_id_f4b32aac FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: homepage_id_refs_page_ptr_id_f766bdfd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_iconbox
    ADD CONSTRAINT homepage_id_refs_page_ptr_id_f766bdfd FOREIGN KEY (homepage_id) REFERENCES theme_homepage(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: instresource_id_refs_page_ptr_id_9e592426; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_groups
    ADD CONSTRAINT instresource_id_refs_page_ptr_id_9e592426 FOREIGN KEY (instresource_id) REFERENCES hs_rhessys_inst_resource_instresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: instresource_id_refs_page_ptr_id_a88be7c5; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_users
    ADD CONSTRAINT instresource_id_refs_page_ptr_id_a88be7c5 FOREIGN KEY (instresource_id) REFERENCES hs_rhessys_inst_resource_instresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: instresource_id_refs_page_ptr_id_b67c9746; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_owners
    ADD CONSTRAINT instresource_id_refs_page_ptr_id_b67c9746 FOREIGN KEY (instresource_id) REFERENCES hs_rhessys_inst_resource_instresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: instresource_id_refs_page_ptr_id_d4cb5d6d; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_groups
    ADD CONSTRAINT instresource_id_refs_page_ptr_id_d4cb5d6d FOREIGN KEY (instresource_id) REFERENCES hs_rhessys_inst_resource_instresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: instresource_id_refs_page_ptr_id_f104c81a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_users
    ADD CONSTRAINT instresource_id_refs_page_ptr_id_f104c81a FOREIGN KEY (instresource_id) REFERENCES hs_rhessys_inst_resource_instresource(page_ptr_id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: last_changed_by_id_refs_id_01f3936e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource
    ADD CONSTRAINT last_changed_by_id_refs_id_01f3936e FOREIGN KEY (last_changed_by_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: last_changed_by_id_refs_id_7e75022f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource
    ADD CONSTRAINT last_changed_by_id_refs_id_7e75022f FOREIGN KEY (last_changed_by_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: page_ptr_id_refs_id_8aa2112f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource
    ADD CONSTRAINT page_ptr_id_refs_id_8aa2112f FOREIGN KEY (page_ptr_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: parent_id_refs_id_68963b8e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_page
    ADD CONSTRAINT parent_id_refs_id_68963b8e FOREIGN KEY (parent_id) REFERENCES pages_page(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: profile_id_refs_id_dfb05146; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerprocess
    ADD CONSTRAINT profile_id_refs_id_dfb05146 FOREIGN KEY (profile_id) REFERENCES django_docker_processes_dockerprofile(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: qdce_id_refs_id_7eb27ec4; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY dublincore_qualifieddublincoreelementhistory
    ADD CONSTRAINT qdce_id_refs_id_7eb27ec4 FOREIGN KEY (qdce_id) REFERENCES dublincore_qualifieddublincoreelement(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: site_id_refs_id_70c9ac77; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pages_page
    ADD CONSTRAINT site_id_refs_id_70c9ac77 FOREIGN KEY (site_id) REFERENCES django_site(id) DEFERRABLE INITIALLY DEFERRED;


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
-- Name: user_id_refs_id_01f3936e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource
    ADD CONSTRAINT user_id_refs_id_01f3936e FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_0326e167; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_edit_users
    ADD CONSTRAINT user_id_refs_id_0326e167 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_13f09379; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_view_users
    ADD CONSTRAINT user_id_refs_id_13f09379 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_40c41112; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT user_id_refs_id_40c41112 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_4876f3f8; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_users
    ADD CONSTRAINT user_id_refs_id_4876f3f8 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_4dc23c39; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT user_id_refs_id_4dc23c39 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_77917a71; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_docker_processes_dockerprocess
    ADD CONSTRAINT user_id_refs_id_77917a71 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_7e75022f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource
    ADD CONSTRAINT user_id_refs_id_7e75022f FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_8d852095; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_owners
    ADD CONSTRAINT user_id_refs_id_8d852095 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_9436ba96; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY generic_rating
    ADD CONSTRAINT user_id_refs_id_9436ba96 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_990aee10; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tastypie_apikey
    ADD CONSTRAINT user_id_refs_id_990aee10 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_ae3696a7; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_owners
    ADD CONSTRAINT user_id_refs_id_ae3696a7 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_b13e9651; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY theme_userprofile
    ADD CONSTRAINT user_id_refs_id_b13e9651 FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_b319fa2a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY core_sitepermission
    ADD CONSTRAINT user_id_refs_id_b319fa2a FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_ba84458b; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_core_genericresource_edit_groups
    ADD CONSTRAINT user_id_refs_id_ba84458b FOREIGN KEY (group_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_id_refs_id_e7c0ddff; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY hs_rhessys_inst_resource_instresource_view_users
    ADD CONSTRAINT user_id_refs_id_e7c0ddff FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


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

